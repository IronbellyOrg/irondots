#!/usr/bin/env python3
"""Private local Brain ledger. NEVER invokes provider tools, sockets or subprocesses.

CLI: init --db FILE --input run.json
     create|reserve-call|record-call|ingest|record-assessment|cancel|handoff --db FILE
       --operation ID --owner OWNER --revision N --input payload.json
     hydrate|export --db FILE (--operation ID | --scope-key KEY)

init input: {run_id, coordinator, authority_ref, aggregate_cap,
 cases: {A:{cap:6,verification_reserve:2}, B:{cap:7,verification_reserve:4},
 C:{cap:6,verification_reserve:2}}, reused_evidence: [...]}
create input: {case: A|B|C, semantic_key, request: exact v1 envelope,
 packet: exact outbound text, authority_ref, audience_ref, workspace_id,
 previous_operation?: ID, refresh_authority_ref?: REF, evidence_class}
reserve-call input: {call_id, category: send|reply_read|verify|preflight,
 tool, arguments: object}; send arguments MUST contain exact packet as content
 and workspace_id/channel_id. reply_read requires workspace_id/message_id
 (channel is derived from the retained send receipt, NOT a fabricated read arg).
record-call input: {call_id, status: success|error|timeout,
 raw_path, started_at, finished_at, evidence_class, context_ref}
Raw path is captured connector JSON, not invented wire bytes. Read receipts retain
exact reservation arguments. For captured imports context_ref names retained
parent invocation evidence; assurance is labelled captured, never live proof.
ingest input: {call_id, reply_id, projection: {criteria:{C1:{status,claim,
 evidence:[{quote,source_id,location}]},...}, parse_gap?, generated_at?}}
Missing criteria become not-returned. Quotes must occur in actual reply text;
semantic adequacy/independent verification remains a separate review gate.
record-assessment input: {assessment_id, return_id, reviewer, provenance,
 authority_ref, criteria: {C1:{verdict:verified|partial|unresolved|contradicted,
 evidence:[{path,sha256,location}], reason}}, next_permitted_step}.
Evidence files are read locally and SHA256-checked. References attest coordinator
provenance; they are not identity authentication. This never changes Brain state.
Execution create uses exact dot-brain-execution/0.1 envelope; see validate_execution.
Execution ingest projection: {effects:{E1:{reported_status,reported_ids:{},
 evidence:[{quote,location}],remaining_gap}}}. AI cannot assert verification.
Execution record-assessment uses effects:{E1:{verdict,reason,evidence:[{path,
 sha256,location}],checks:{<every frozen verification criterion>:true}}}.
import-captured-execution uses captured-execution-import/0.1 normalized manifest
(original bytes/hash, artifacts, source-backed stages/costs/correlation). Business
conversion remains outside this package. Imported operations cannot dispatch.
Execution verify intents require effect_id/effect_hash/return_id/verification_kind
(task_identity,task_content,attachment_download,notification_message).
reserve-transfer commits a one-use HTTP ticket attempt before local transfer;
record-transfer retains status and file hash. Sanitized ticket receipts omit URLs.
reserve-continuation requires call_id,continuation_id,effect_ids,authority_ref,
authority_quote,assessment_id; it derives exact same-root packet, never generic retry.
init optional carry_in:{charged,ledger_ref,ledger_sha256} binds actual prior JSON
charged_calls; aggregate capacity includes prior charges plus all new case caps.
cancel/handoff input: {authority_ref, new_owner?}. No unlock/retry/refund command.
All identities/authority references are coordinator attestations, not authentication.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
from urllib.parse import quote
from batch_stage import canonical, digest, require, Invalid, Conflict, now
import task_progress

FORMAT = 'dot-brain-state/0.1'
APP = 0x42524149
ALLOWED = {'read_summary', 'read_compare', 'propose_spec', 'propose_change'}

EXECUTION='dot-brain-execution/0.1'
EFFECT_TYPES={'task_create','report_create','attachment_add','notify_people'}

def validate_execution(r):
    required={'contract_version','operation_id','parent_run_id','scope_revision','attempt_id','predecessor','request_provenance',
              'coordinator','executor_audience','canonical_work','outcome','criteria','exclusions','effects','input_files',
              'source_versions','budget','control','report_requirements'}
    require(set(r)==required and r['contract_version'] in {EXECUTION, task_progress.EXECUTION}, 'exact execution envelope fields/version required')
    require(all(r.get(k) for k in ('operation_id','parent_run_id','attempt_id','request_provenance','coordinator','canonical_work','outcome','report_requirements')), 'execution material scope missing')
    require(type(r['scope_revision']) is int and r['scope_revision']>0 and r['control'].get('cancelled') is False, 'invalid/cancelled execution scope')
    require(isinstance(r['criteria'],list) and r['criteria'] and len({x.split()[0] for x in r['criteria']})==len(r['criteria']), 'stable unique execution criteria required')
    require(isinstance(r['exclusions'],list) and r['exclusions'], 'explicit execution exclusions required')
    require(isinstance(r['input_files'],list) and isinstance(r['source_versions'],list), 'execution files/source versions must be explicit lists')
    require(type(r['budget'].get('reply_read_allowance')) is int and r['budget']['reply_read_allowance']>=0, 'explicit execution reply allowance required')
    a=r['executor_audience'];require(set(a)=={'workspace_id','channel_id','type','visibility','evidence_ref'} and all(a.values()) and a['type']=='ASK_AI' and a['visibility']=='PRIVATE', 'exact private executor audience required')
    require(isinstance(r['effects'],list) and r['effects'], 'effect list required')
    require(sum(e.get('type')=='task_update' for e in r['effects'])<=1, 'at most one progress update per milestone envelope')
    keys={'effect_id','type','target_or_creation_rule','payload','baseline','authority_ref','depends_on','side_effects','verification','capability_state'}
    effectmap={e.get('effect_id'):e for e in r['effects']}
    require(None not in effectmap and '' not in effectmap and len(effectmap)==len(r['effects']), 'unique effect IDs required')
    for e in r['effects']:
        require(set(e)==keys and e['type'] in (EFFECT_TYPES | ({'task_update'} if r['contract_version']==task_progress.EXECUTION else set())), 'unsupported effect fields/type')
        require(e['authority_ref'] and e['capability_state']=='bounded_supported' and isinstance(e['side_effects'],list), 'effect authority/capability/side effects required')
        require(isinstance(e['depends_on'],list) and all(x in effectmap and x!=e['effect_id'] for x in e['depends_on']), 'unknown/self dependency')
        require(all(x in {'provider_attributed_actor','existing_task_watchers_may_receive_platform_notifications'} for x in e['side_effects']), 'unknown consequential side effect')
        t=e['target_or_creation_rule'];p=e['payload'];require(isinstance(t,dict) and isinstance(p,dict) and isinstance(e['verification'],list), 'exact target/payload/checks required')
        if e['type']=='task_update':
            task_progress.validate(e,r)
            checks=task_progress.CHECKS
        elif e['type']=='task_create':
            require(set(t)=={'workspace_id','list_id','dedup_key','existing_behavior'} and all(t.values()) and t['existing_behavior']=='reuse_preserve_human_content', 'task exact create/dedup target required')
            require(str(t['workspace_id'])==str(a['workspace_id']), 'task workspace differs from approved execution workspace')
            require(set(p)=={'title','status','body_requirements'} and all(p.values()), 'task payload permits only title/status/body requirements')
            checks={'container','title_status','no_unapproved_fields','dedup'}
        elif e['type']=='report_create':
            require(t.get('kind') in {'brain_reply','task_description'}, 'unsupported report destination')
            if t['kind']=='brain_reply':require(set(t)=={'kind','channel_id'} and t['channel_id']==a['channel_id'], 'report reply must remain private approved Brain thread')
            else:require(set(t)=={'kind','task_effect_id'} and t['task_effect_id'] in e['depends_on'] and effectmap[t['task_effect_id']]['type']=='task_create', 'report task dependency required')
            require(set(p)=={'requirements','content_only','preserve_human_content'} and isinstance(p['requirements'],list) and p['requirements'] and p['preserve_human_content'] is True, 'exact report requirements/preservation required')
            require(p['content_only'] is (t['kind']=='brain_reply'), 'report content-only mode mismatch')
            checks={'ai_authorship','complete_content','approved_destination','excluded_private_data'}
        elif e['type']=='attachment_add':
            require(set(t)=={'task_effect_id'} and t['task_effect_id'] in e['depends_on'] and effectmap[t['task_effect_id']]['type']=='task_create', 'attachment task dependency required')
            require(set(p)=={'file_id','name','size','sha256','input_receipt_ref','semantics'} and p['semantics']=='binary_attachment' and p['input_receipt_ref'], 'exact existing binary attachment required')
            files=[f for f in r['input_files'] if f.get('file_id')==p['file_id']]
            require(len(files)==1 and all(files[0].get(k)==p[k] for k in ('name','size','sha256')), 'attachment approved file identity mismatch')
            require(re.fullmatch('[0-9a-f]{64}',p['sha256']) and type(p['size']) is int and p['size']>0, 'attachment hash/size invalid')
            require(files[0].get('transport_ref') and not str(files[0]['transport_ref']).startswith(('/', 'file:')) and files[0].get('audience_ref'), 'AI-accessible approved file transport required')
            checks={'attachment_metadata','downloaded_hash','source_hash','binary_not_link'}
        else:
            require(set(t)=={'workspace_id','channel_id','user_ids','recipient_evidence_ref','audience_ref'} and all(t.values()) and isinstance(t['user_ids'],list) and len(t['user_ids'])==len(set(t['user_ids'])), 'exact verified recipients/channel required')
            require(str(t['workspace_id'])==str(a['workspace_id']) and all(isinstance(x,str) and x for x in t['user_ids']), 'notification workspace/user IDs invalid')
            require(set(p)=={'content','substitutions','mechanism'} and p['content'] and p['mechanism']=='one_channel_message' and p['substitutions']==['actual_task_link'], 'exact notification payload/mechanism required')
            require({'task_create','report_create','attachment_add'} <= {effectmap[x]['type'] for x in e['depends_on']}, 'notification requires task/report/file dependencies')
            checks={'channel','mentions','exact_content','one_message','dependency_success'}
        require(set(e['verification'])==checks and len(e['verification'])==len(checks), 'exact per-type verification criteria required')
    done=set();active=set()
    def visit(eid):
        require(eid not in active,'cyclic effect dependencies')
        if eid in done:return
        active.add(eid)
        for dep in effectmap[eid]['depends_on']:visit(dep)
        active.remove(eid);done.add(eid)
    for eid in effectmap:visit(eid)


def rawhash(raw):
    return hashlib.sha256(raw).hexdigest()

def payload(raw):
    obj = json.loads(raw)
    require(not obj.get('isError'), 'connector error is not accepted evidence')
    if isinstance(obj.get('structuredContent'), dict):
        return obj['structuredContent']
    texts = [x['text'] for x in obj.get('content', []) if x.get('type') == 'text']
    require(len(texts) == 1, 'unparseable connector wrapper')
    return json.loads(texts[0])

def validate_echoes(reply, request):
    """Only explicit identity labels/backticks are echoes, not generic prose.

    Historical: Operation `ID`, attempt 1, scope revision 1.
    Current: Operation: `ID` · attempt `1` · scope revision `1`.
    A bare phrase such as "operation identifiers" is not a protocol field.
    """
    for key in ('operation_id','attempt_id','scope_revision'):
        if key in reply:
            require(str(reply[key]) == str(request[key]), 'mismatched '+key+' echo')
    patterns = {
        'operation_id': r'\b(?:operation|operation_id)(?:\s*:\s*`?|\s+`)([A-Za-z0-9_-]+)',
        'attempt_id': r'\battempt(?:_id)?\s*:?\s*`?(\d+)',
        'scope_revision': r'\bscope(?: revision|_revision)\s*:?\s*`?(\d+)'
    }
    for key, pattern in patterns.items():
        for value in re.findall(pattern, reply.get('content',''), re.I):
            require(str(value) == str(request[key]), 'mismatched '+key+' text echo')


def initialize(path, config):
    require(all(config.get(k) for k in ('run_id','coordinator','authority_ref')), 'run authority required')
    require(isinstance(config.get('reused_evidence'), list), 'explicit reused evidence ledger required')
    require(type(config.get('aggregate_cap')) is int and config['aggregate_cap'] > 0, 'explicit positive aggregate cap required')
    require(isinstance(config.get('cases'), dict) and config['cases'], 'explicit case budgets required')
    for budget in config['cases'].values():
        require(type(budget.get('cap')) is int and type(budget.get('verification_reserve')) is int and 0 <= budget['verification_reserve'] < budget['cap'], 'invalid case budget')
    carry=config.get('carry_in',{'charged':0})
    require(type(carry.get('charged')) is int and carry['charged']>=0, 'invalid carry-in charge')
    if carry['charged']:
        require(carry.get('ledger_ref') and carry.get('ledger_sha256') and rawhash(Path(carry['ledger_ref']).read_bytes())==carry['ledger_sha256'], 'carry-in actual ledger hash required')
        observed=json.loads(Path(carry['ledger_ref']).read_bytes())
        require(observed.get('charged_calls')==carry['charged'], 'carry-in charged count differs from actual linked ledger')
    require(carry['charged'] + sum(x['cap'] for x in config['cases'].values()) <= config['aggregate_cap'], 'aggregate must protect all case allocations')
    path = Path(path)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        with sqlite3.connect(path) as db:
            db.executescript('''
            PRAGMA application_id=1112686921;
            PRAGMA user_version=1;
            CREATE TABLE config(body TEXT NOT NULL, hash TEXT NOT NULL);
            CREATE TABLE operations(id TEXT PRIMARY KEY, semantic_key TEXT NOT NULL,
              revision INTEGER NOT NULL, owner TEXT NOT NULL, body TEXT NOT NULL, hash TEXT NOT NULL);
            CREATE TABLE events(seq INTEGER PRIMARY KEY, operation_id TEXT NOT NULL,
              revision INTEGER NOT NULL, kind TEXT NOT NULL, at TEXT NOT NULL,
              body TEXT NOT NULL, hash TEXT NOT NULL, UNIQUE(operation_id,revision));
            CREATE TABLE observations(id TEXT PRIMARY KEY, operation_id TEXT NOT NULL,
              namespace TEXT NOT NULL, provider_id TEXT NOT NULL, raw BLOB NOT NULL,
              hash TEXT NOT NULL, metadata TEXT NOT NULL, metadata_hash TEXT NOT NULL, UNIQUE(namespace,provider_id));
            ''')
            c = dict(config, schema=FORMAT, initialized_at=now())
            db.execute('INSERT INTO config VALUES (?,?)', (canonical(c), digest(c)))
        return {'initialized':str(path), 'schema':FORMAT, 'run_id':config['run_id']}
    except BaseException:
        path.unlink(missing_ok=True)
        raise

class Store:
    def __init__(self, path, readonly=False):
        self.readonly = readonly
        # URI mode guarantees a missing path never creates a file.
        self.db = sqlite3.connect('file:' + quote(str(Path(path).absolute())) +
                                  '?mode=' + ('ro' if readonly else 'rw'), uri=True,
                                  timeout=3, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA query_only=' + ('ON' if readonly else 'OFF'))
        if not readonly:
            self.db.execute('PRAGMA synchronous=FULL')
        require(self.db.execute('PRAGMA application_id').fetchone()[0] == APP, 'wrong database application')
        require(self.db.execute('PRAGMA user_version').fetchone()[0] == 1, 'unsupported database version')
        require(self.db.execute('PRAGMA quick_check').fetchone()[0] == 'ok', 'database integrity failed')
        names = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        require({'config','operations','events','observations'} <= names, 'missing schema tables')
        row = self.db.execute('SELECT * FROM config').fetchall()
        require(len(row) == 1, 'invalid config')
        self.config = json.loads(row[0]['body'])
        require(digest(self.config) == row[0]['hash'] and self.config['schema'] == FORMAT, 'config hash/schema mismatch')

    def close(self):
        self.db.close()

    def _load(self, operation):
        row = self.db.execute('SELECT * FROM operations WHERE id=?', (operation,)).fetchone()
        require(row is not None, 'unknown operation; local recovery blocked')
        b = json.loads(row['body'])
        require(digest(b) == row['hash'], 'operation hash mismatch')
        require(b['revision'] == row['revision'] and b['owner'] == row['owner'], 'snapshot columns mismatch')
        require(digest(b['request']) == b['request_hash'] and rawhash(b['packet'].encode()) == b['packet_hash'], 'immutable request hash mismatch')
        events = self.db.execute('SELECT * FROM events WHERE operation_id=? ORDER BY revision', (operation,)).fetchall()
        require(len(events) == b['revision'], 'event chain missing')
        for n, e in enumerate(events, 1):
            require(e['revision'] == n and digest(json.loads(e['body'])) == e['hash'], 'event corruption')
        require(events[-1]['hash'] == row['hash'], 'latest event differs from snapshot')
        for oid in b['observation_ids']:
            o = self.db.execute('SELECT * FROM observations WHERE id=?', (oid,)).fetchone()
            require(o is not None and rawhash(o['raw']) == o['hash'] and digest(json.loads(o['metadata'])) == o['metadata_hash'], 'raw observation/metadata missing/corrupt')
        return b

    def _all(self):
        return [self._load(r[0]) for r in self.db.execute('SELECT id FROM operations').fetchall()]

    def _save(self, b, oldrev, kind):
        b['revision'] = oldrev + 1
        b['updated_at'] = now()
        body, h = canonical(b), digest(b)
        if oldrev == 0:
            self.db.execute('INSERT INTO operations VALUES (?,?,?,?,?,?)',
                            (b['id'], b['semantic_key'], 1, b['owner'], body, h))
        else:
            r = self.db.execute('UPDATE operations SET revision=?,owner=?,body=?,hash=? WHERE id=? AND revision=?',
                                (b['revision'], b['owner'], body, h, b['id'], oldrev))
            if r.rowcount != 1:
                raise Conflict('stale revision')
        self.db.execute('INSERT INTO events(operation_id,revision,kind,at,body,hash) VALUES (?,?,?,?,?,?)',
                        (b['id'], b['revision'], kind, b['updated_at'], body, h))

    def _observe(self, b, oid, namespace, provider_id, raw, metadata):
        old = self.db.execute('SELECT * FROM observations WHERE namespace=? AND provider_id=?',
                              (namespace, provider_id)).fetchone()
        if old:
            if old['hash'] != rawhash(raw) or old['operation_id'] != b['id']:
                raise Conflict('conflicting observation identity/content; existing evidence preserved')
            return False
        self.db.execute('INSERT INTO observations VALUES (?,?,?,?,?,?,?,?)',
                        (oid,b['id'],namespace,provider_id,raw,rawhash(raw),canonical(metadata),digest(metadata)))
        b['observation_ids'].append(oid)
        return True

    def apply(self, command, operation, owner, revision, data):
        require(not self.readonly, 'read-only store')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            if command == 'import-captured-execution':
                b,changed=self._import_execution(operation,owner,data)
                if not changed:
                    require(revision==b['revision'], 'import replay stale revision')
                else:
                    require(revision==0,'import creation requires revision zero')
            elif command == 'create':
                require(revision == 0, 'create requires revision zero')
                b = self._create(operation, owner, data)
                changed = True
            else:
                b = self._load(operation)
                if b['owner'] != owner or b['revision'] != revision:
                    raise Conflict('owner/revision mismatch; rehydrate')
                changed = getattr(self, '_' + command.replace('-', '_'))(b, data)
            if changed:
                self._save(b, revision, command)
            self.db.execute('COMMIT')
            return {'operation_id':operation, 'revision':b['revision'], 'hash':digest(b), 'state':b['state'], 'changed':changed}
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def _effect(self,b,eid):
        matches=[e for e in b['request'].get('effects',[]) if e['effect_id']==eid]
        require(b.get('execution') and len(matches)==1,'unknown execution effect')
        return matches[0]

    def _binding(self,b,eid,kind):
        matches=[x for x in b.get('verification_bindings',[]) if x['effect_id']==eid and x['kind']==kind and x['return_id']==b['latest_return_id']]
        require(matches and matches[-1]['valid'],'missing/contradicted current typed '+kind+' binding')
        return matches[-1]

    def _current_effect_support(self,b,eid,review):
        """Recheck current typed evidence, never reuse superseded semantic review."""
        effect=self._effect(b,eid);kind=effect['type']
        if b.get('imported_nondispatchable') or (kind=='report_create' and effect['target_or_creation_rule'].get('kind')=='brain_reply'):
            return
        required_kind='task_identity' if kind=='task_create' else 'notification_message' if kind=='notify_people' else 'task_content'
        binding=self._binding(b,eid,required_kind)
        require(binding['call_id'] in review.get('binding_call_ids',[]),'assessment supporting '+eid+' readback superseded; independent re-review required')
        for dep in effect['depends_on']:
            self._verified_dependency(b,dep)
        if kind=='attachment_add':
            transfers=[t for t in b.get('transfers',[]) if t['effect_id']==eid and t['return_id']==b['latest_return_id']]
            require(transfers and transfers[-1].get('valid') and transfers[-1]['transfer_id'] in review.get('transfer_ids',[]),'latest attachment transfer invalid/pending or supersedes assessment')
            download=self._binding(b,eid,'attachment_download')
            require(download['call_id']==transfers[-1]['call_id'],'attachment download ticket superseded approved transfer')

    def _verified_dependency(self,b,eid):
        assessments=[a for a in b.get('assessments',[]) if a.get('return_id')==b['latest_return_id'] and 'effects' in a]
        require(assessments and eid in assessments[-1]['effects'],'dependency lacks current independent assessment')
        assessment=assessments[-1];review=assessment['effects'][eid]
        require(review['verdict']=='verified','dependency lacks current independent verification')
        require(not any(c.get('category')=='verify' and c.get('effect_id')==eid and c['receipt'] is None and c['reserved_at']>assessment['recorded_at'] for c in b['calls']), 'new unresolved readback invalidates dependency readiness')
        self._current_effect_support(b,eid,review)

    def _assessment_invalidation(self,b,assessment):
        if not assessment:return ['no independent assessment recorded']
        if assessment['return_id']!=b['latest_return_id']:return ['assessment belongs to an earlier Brain return']
        gaps=[]
        if b.get('execution'):
            for eid,item in assessment.get('effects',{}).items():
                if item['verdict']=='verified':
                    try:self._verified_dependency(b,eid)
                    except Invalid as exc:gaps.append(eid+': '+str(exc))
        return gaps

    def _validate_execution_read(self,b,d):
        require(d.get('return_id')==b['latest_return_id'] and b['latest_return_id'],'readback must bind latest return')
        e=self._effect(b,d.get('effect_id'));require(d.get('effect_hash')==digest(e),'readback frozen effect hash mismatch')
        kind=d.get('verification_kind');args=d['arguments'];tool=d['tool'].split('__')[-1]
        require(str(args.get('workspace_id'))==b['workspace_id'],'readback wrong workspace')
        reported=b['returns'][-1]['effects'][e['effect_id']]
        if kind=='task_identity':
            require(e['type']=='task_create' and tool=='clickup_get_task','identity read requires approved task create')
            require(set(args)=={'workspace_id','task_id','include'} and args['include']==[],'identity read must be compact exact arguments')
            require(reported.get('reported_ids',{}).get('task_id') and args['task_id']==reported['reported_ids']['task_id'],'task ID not nominated by correlated create effect')
        elif kind=='task_content' and e['type']=='task_update':
            require(tool=='clickup_get_task' and set(args)=={'workspace_id','task_id','include'} and args['task_id']==e['target_or_creation_rule']['task_id'] and args['include']==['description'], 'progress exact existing target read required')
        elif kind=='task_content':
            require(e['type'] in {'report_create','attachment_add'} and tool=='clickup_get_task','content read unsupported effect')
            task_eid=e['target_or_creation_rule'].get('task_effect_id');binding=self._binding(b,task_eid,'task_identity')
            required='description' if e['type']=='report_create' else 'attachments'
            require(set(args)=={'workspace_id','task_id','include'} and args['task_id']==binding['task_id'] and isinstance(args['include'],list) and required in args['include'] and set(args['include'])<={'description','attachments'},'content read scope/sections mismatch')
        elif kind=='attachment_download':
            require(e['type']=='attachment_add' and tool=='clickup_download_task_attachment','download requires attachment effect')
            binding=self._binding(b,e['effect_id'],'task_content')
            require(set(args)=={'workspace_id','task_id','attachment_id'} and args['task_id']==binding['task_id'] and args['attachment_id']==binding['attachment_id'],'download must use exact accepted metadata binding')
            require(not any(t.get('call_id')==d['call_id'] for t in b.get('transfers',[])),'download identity already consumed')
        elif kind=='notification_message':
            require(e['type']=='notify_people' and tool=='clickup_get_chat_channel_messages','notification read wrong effect/tool')
            for dep in e['depends_on']:self._verified_dependency(b,dep)
            require(set(args)<={'workspace_id','channel_id','limit','cursor','include_reactions'} and args.get('channel_id')==e['target_or_creation_rule']['channel_id'],'notification read wrong frozen channel')
            require(type(args.get('limit')) is int and 1<=args['limit']<=25 and args.get('include_reactions',False) is False,'bounded read without reaction fanout required')
            require(d.get('expected_message_id') and d['expected_message_id']==reported.get('reported_ids',{}).get('message_id'),'expected message ID must be locally bound, not fabricated tool arg')
            if args.get('cursor'):
                prev=[x for x in b.get('verification_bindings',[]) if x['kind']=='notification_message' and x['effect_id']==e['effect_id'] and x['return_id']==b['latest_return_id']]
                require(prev and prev[-1].get('next_cursor')==args['cursor'],'pagination cursor must come from preceding exact channel receipt')
        else:raise Invalid('unsupported execution verification kind')

    def _record_execution_read(self,b,c,raw):
        e=self._effect(b,c['effect_id']);kind=c['verification_kind'];p=payload(raw);args=c['arguments']
        binding={'effect_id':e['effect_id'],'effect_hash':digest(e),'kind':kind,'return_id':c['return_id'],
                 'call_id':c['call_id'],'raw_sha256':rawhash(raw),'recorded_at':now(),'valid':False,'gaps':[]}
        gaps=binding['gaps']
        if kind=='task_identity':
            target=e['target_or_creation_rule'];expected=e['payload']
            binding.update(task_id=args['task_id'],list_id=target['list_id'])
            if p.get('id')!=args['task_id']:gaps.append('task identity mismatch')
            if p.get('list',{}).get('id')!=target['list_id']:gaps.append('wrong/missing approved list')
            if p.get('name')!=expected['title'] or p.get('status')!=expected['status']:gaps.append('wrong/missing title or status')
            for key,empty in [('assignees',[]),('due_date',None),('start_date',None),('priority',None)]:
                if key not in p:gaps.append('not-returned: '+key)
                elif p[key]!=empty:gaps.append('unapproved field: '+key)
            binding['observed_fields']={key:{'presence':'present' if key in p else 'not-returned','value':p.get(key)} for key in ('id','list','name','status','assignees','due_date','start_date','priority')}
        elif kind=='task_content' and e['type']=='task_update':
            binding.update(task_progress.observe(e,p))
            gaps=binding['gaps']
            prior=[x for x in b.get('verification_bindings',[]) if x['effect_id']==e['effect_id'] and x['kind']=='task_content' and x.get('description_sha256') and x.get('valid')]
            if prior and any(x['description_sha256']!=binding['description_sha256'] for x in prior):
                gaps.append('same marker content changed; conflict')
        elif kind=='task_content':
            task_eid=e['target_or_creation_rule']['task_effect_id'];identity=self._binding(b,task_eid,'task_identity');te=self._effect(b,task_eid)
            binding.update(task_id=identity['task_id'],list_id=identity['list_id'])
            if p.get('id')!=identity['task_id'] or p.get('list',{}).get('id')!=identity['list_id'] or p.get('name')!=te['payload']['title'] or p.get('status')!=te['payload']['status']:gaps.append('task identity changed during content read')
            if e['type']=='report_create':
                if not isinstance(p.get('markdown_description'),str):gaps.append('full markdown_description not returned')
                else:binding['report_text_sha256']=rawhash(p['markdown_description'].encode());binding['report_text']=p['markdown_description']
            else:
                metadata=[x for x in p.get('attachments',[]) if x.get('title')==e['payload']['name'] and x.get('size')==e['payload']['size']]
                if len(metadata)!=1 or not metadata[0].get('id'):gaps.append('exact unique file metadata not returned')
                else:binding['attachment_id']=metadata[0]['id'];binding['metadata']=metadata[0]
        elif kind=='attachment_download':
            wrapper=json.loads(raw);require(wrapper.get('sanitized') is True and 'url' in wrapper.get('omitted_fields',[]),'download ticket must be explicitly sanitized, never persist URL')
            require(set(p)<={'success','task_id','attachment_id','title','size','mimetype','extension','custom_id'},'transient/unknown download ticket fields forbidden')
            if p.get('success') is not True or p.get('task_id')!=args['task_id'] or p.get('attachment_id')!=args['attachment_id'] or p.get('title')!=e['payload']['name'] or p.get('size')!=e['payload']['size']:gaps.append('download metadata mismatch or unknown')
            binding.update(task_id=args['task_id'],attachment_id=args['attachment_id'],serialization_basis='sanitized connector receipt; URL deliberately not persisted')
        elif kind=='notification_message':
            binding['next_cursor']=p.get('next_cursor');binding['expected_message_id']=c['expected_message_id']
            messages=[x for x in p.get('messages',[]) if x.get('id')==c['expected_message_id']]
            if len(messages)!=1:gaps.append('target message unresolved in examined page; not evidence of non-dispatch')
            else:
                msg=messages[0];task_eid=next(x for x in e['depends_on'] if self._effect(b,x)['type']=='task_create');task=self._binding(b,task_eid,'task_identity')
                content=e['payload']['content'].replace('{actual_task_link}','https://app.clickup.com/t/'+task['task_id'])
                if msg.get('content')!=content:gaps.append('notification content mismatch')
                mentions=set(re.findall(r'#user_mention#(\d+)',msg.get('content','')))
                if mentions!=set(e['target_or_creation_rule']['user_ids']):gaps.append('notification mention set mismatch')
                if msg.get('type')!='message':gaps.append('notification type mismatch')
                binding['observed_message']=msg;binding['assurance']='recorded message only; no recipient read/delivery claim; account actor not authorship proof'
        binding['valid']=not gaps
        b.setdefault('verification_bindings',[]).append(binding)
        # Contradictory content identity revokes its prerequisite for later deeper reads.
        if kind=='task_content' and 'task identity changed during content read' in gaps:
            b['verification_bindings'].append(dict(binding,effect_id=e['target_or_creation_rule']['task_effect_id'],kind='task_identity',valid=False))

    def _reserve_transfer(self,b,d):
        require(b.get('execution') and not b.get('imported_nondispatchable') and not b['cancelled'], 'transfer reservation needs active prospective execution')
        require(set(d)=={'transfer_id','call_id'} and all(d.values()), 'exact transfer reservation identity required')
        require(not any(x['transfer_id']==d['transfer_id'] or x['call_id']==d['call_id'] for x in b.get('transfers',[])), 'ticket/transfer already reserved; no hidden retry')
        calls=[c for c in b['calls'] if c['call_id']==d['call_id'] and c.get('verification_kind')=='attachment_download' and c['receipt'] and c['receipt']['status']=='success']
        require(len(calls)==1,'transfer needs sanitized download call receipt')
        c=calls[0];binding=self._binding(b,c['effect_id'],'attachment_download')
        require(binding['call_id']==d['call_id'],'ticket binding superseded')
        b.setdefault('transfers',[]).append(dict(d,status='reserved_uncertain',reserved_at=now(),effect_id=c['effect_id'],return_id=c['return_id'],valid=False,receipt=None))
        return True

    def _record_transfer(self,b,d):
        require(b.get('execution') and not b.get('imported_nondispatchable'),'transfer requires prospective execution')
        require(set(d)<= {'transfer_id','call_id','status','started_at','finished_at','file_path','error_ref'},'transfer record must not contain transient URLs/tokens or unknown fields')
        require(all(d.get(k) for k in ('transfer_id','call_id','status','started_at','finished_at')),'transfer identity/times/status required')
        prior=next((x for x in b.get('transfers',[]) if x['transfer_id']==d['transfer_id'] and x['call_id']==d['call_id']),None)
        require(prior,'HTTP attempt must be durably reserved first')
        if prior.get('receipt'):
            if prior['input_hash']!=digest(d):raise Conflict('changed same transfer identity')
            return False
        calls=[c for c in b['calls'] if c['call_id']==d['call_id'] and c.get('verification_kind')=='attachment_download' and c['receipt']]
        require(len(calls)==1 and calls[0]['receipt']['status']=='success','transfer requires accepted sanitized download receipt')
        c=calls[0];binding=self._binding(b,c['effect_id'],'attachment_download');require(binding['call_id']==d['call_id'],'transfer ticket superseded')
        require(d['status'] in {'success','error','uncertain'},'unknown HTTP transfer status')
        transfer=copy.deepcopy(d);transfer.update(input_hash=digest(d),recorded_at=now(),effect_id=c['effect_id'],return_id=c['return_id'],valid=False)
        if d['status']=='success':
            raw=Path(d['file_path']).read_bytes();expected=self._effect(b,c['effect_id'])['payload']
            transfer.update(bytes=len(raw),sha256=rawhash(raw),valid=(len(raw)==expected['size'] and rawhash(raw)==expected['sha256']))
        transfer['receipt']=copy.deepcopy(d);prior.update(transfer);return True

    def _reserve_continuation(self,b,d):
        require(b.get('execution') and not b.get('imported_nondispatchable') and not b['cancelled'],'only uncancelled prospective execution may continue')
        require(set(d)=={'call_id','continuation_id','effect_ids','authority_ref','authority_quote','assessment_id'},'exact continuation fields required; no caller replacement packet')
        require(d['authority_ref']==b['authority_ref'] and d['authority_quote'] and d['authority_quote'] in canonical(b['request']['request_provenance']),'continuation must quote original actual authority')
        require(b['provider_root'] and isinstance(d['effect_ids'],list) and d['effect_ids'] and len(d['effect_ids'])==len(set(d['effect_ids'])),'known root and exact subset required')
        require(not any(c.get('continuation_id')==d['continuation_id'] or c['call_id']==d['call_id'] for c in b['calls']),'continuation ID already reserved; never resend')
        applicable=[a for a in b['assessments'] if a['return_id']==b['latest_return_id']]
        assessment=applicable[-1] if applicable else None
        require(assessment and assessment['assessment_id']==d['assessment_id'],'newest applicable coordinator assessment required; old assessment superseded')
        require(not self._assessment_invalidation(b,assessment),'assessment invalidated by newer supporting evidence; re-review required')
        latest=b['returns'][-1]['effects'];selected=[]
        for eid in d['effect_ids']:
            effect=self._effect(b,eid);status=latest[eid]
            if effect['type']=='task_update':task_progress.validate(effect,b['request'])
            require(status['reported_status'] in {'blocked','pending'} and status.get('non_dispatch_quote'),'effect not explicitly pending/blocked without dispatch')
            require(not any(stage.get(eid,{}).get('reported_status')=='completed' for stage in b['effect_history']), 'previously completed effect cannot be replayed after later partial return')
            review=assessment['effects'][eid]
            require(review['evidence'],'continuation non-dispatch assessment needs checked evidence')
            require(review['verdict'] in {'partial','unresolved'} and review['checks'].get('non_dispatch_confirmed') is True,'coordinator must assess explicit non-dispatch evidence')
            require(not any(c.get('category')=='continuation' and eid in c.get('effect_ids',[]) for c in b['calls']),'effect already has a continuation reservation; reconcile, no duplicate')
            for dep in effect['depends_on']:self._verified_dependency(b,dep)
            selected.append(effect)
        excluded=[eid for eid,x in latest.items() if x['reported_status']=='completed']
        packet=canonical({'operation_id':b['id'],'attempt_id':b['request']['attempt_id'],'scope_revision':b['request']['scope_revision'],
           'continuation_id':d['continuation_id'],'original_authority_quote':d['authority_quote'],'selected_effects':selected,
           'do_not_repeat_completed_effects':excluded,'exclusions':b['request']['exclusions'],
           'verified_dependency_outputs':{eid:latest[eid]['reported_ids'] for effect in selected for eid in effect['depends_on']}})
        allb=self._all();total=self.config.get('carry_in',{}).get('charged',0)+sum(len(x['calls']) for x in allb)
        case=[c for x in allb if x['case']==b['case'] for c in x['calls']]
        reserve=max(0,b['verification_reserve']-sum(c['category']=='verify' for c in case))
        require(total<self.config['aggregate_cap'] and len(case)+1<=b['cap']-reserve,'continuation exceeds aggregate/case/protected reserve')
        args={'workspace_id':b['workspace_id'],'parent_message_id':b['provider_root'],'content':packet,'content_format':'text/md','type':'message'}
        call=dict(copy.deepcopy(d),category='continuation',tool='clickup_send_chat_message',arguments=args,arguments_hash=digest(args),reserved_at=now(),receipt=None)
        b['calls'].append(call);b.setdefault('continuations',[]).append({'continuation_id':d['continuation_id'],'call_id':d['call_id'],'effect_ids':d['effect_ids'],'packet':packet,'packet_hash':rawhash(packet.encode()),'state':'send_uncertain'})
        return True


    def _create_execution(self, operation, owner, d, imported=False):
        r=copy.deepcopy(d['request']); validate_execution(r)
        require(r['operation_id']==operation, 'execution operation identity mismatch')
        require(owner and d.get('authority_ref') and d.get('audience_ref') and d.get('semantic_key'), 'execution authority/audience/scope required')
        require(d.get('case') in self.config['cases'], 'execution budget case missing')
        require(d.get('evidence_class') in {'live','captured','imported'}, 'execution evidence class required')
        require(isinstance(d.get('packet'),str) and d['packet'], 'frozen execution packet required')
        audience=r['executor_audience']
        require(str(d.get('workspace_id'))==str(audience['workspace_id']), 'execution workspace mismatch')
        allb=self._all()
        require(not any(x['id']==operation for x in allb), 'operation exists')
        require(not any(x['semantic_key']==d['semantic_key'] for x in allb), 'execution semantic duplicate; continuation unsupported')
        if not imported:
            for effect in r['effects']:
                if effect['type']!='task_update':continue
                require(d['semantic_key']=='progress:'+effect['payload']['list_id']+':'+effect['payload']['milestone_id'], 'stable progress milestone semantic key required')
                target=effect['target_or_creation_rule']
                for old in allb:
                    if old['cancelled'] and not old['calls']:continue
                    same=[x for x in old['request'].get('effects',[]) if x['type']=='task_update' and all(x['target_or_creation_rule'][k]==target[k] for k in ('workspace_id','task_id'))]
                    for prior in same:
                        self._verified_dependency(old,prior['effect_id'])
        budget=self.config['cases'][d['case']]
        if not imported:
            require(r['parent_run_id']==self.config['run_id'], 'execution run mismatch')
            require(r['budget']['cumulative_operation_cap']==budget['cap'] and r['budget']['reserved_verification_reporting_calls']==budget['verification_reserve'], 'execution budget mismatch')
        return dict(id=operation,schema=FORMAT,revision=0,owner=owner,semantic_key=d['semantic_key'],case=d['case'],
                    request=r,request_hash=digest(r),packet=d['packet'],packet_hash=rawhash(d['packet'].encode()),
                    authority_ref=d['authority_ref'],audience_ref=d['audience_ref'],workspace_id=str(d['workspace_id']),
                    evidence_class=d['evidence_class'],previous_operation=None,state='prepared',cancelled=False,
                    calls=[],observation_ids=[],returns=[],criteria=[x.split()[0] for x in r['criteria']],
                    latest_return_id=None,last_good_return_id=None,last_good_operation=None,source_history=[],
                    cap=budget['cap'],verification_reserve=budget['verification_reserve'],provider_root=None,
                    channel_id=audience['channel_id'],handoffs=[],cancellation=None,
                    execution=True,imported_nondispatchable=imported,effect_history=[],assessments=[])

    def _execution_projection(self,b,projection,text):
        require(isinstance(projection,dict) and isinstance(projection.get('effects'),dict), 'execution effects projection required')
        effects={e['effect_id']:e for e in b['request']['effects']}
        require(set(projection['effects'])<=set(effects), 'unrequested reported effect')
        result={}
        for eid,effect in effects.items():
            item=copy.deepcopy(projection['effects'].get(eid,{'reported_status':'not-returned','reported_ids':{},'evidence':[],'remaining_gap':'not returned'}))
            require(set(item)<= {'reported_status','reported_ids','evidence','remaining_gap','next_permitted_step','non_dispatch_quote'}, 'AI effect projection cannot assert verification or authority')
            require(item.get('reported_status') in {'completed','blocked','failed','uncertain','not-returned','pending'}, 'unknown reported effect state')
            require(isinstance(item.get('reported_ids'),dict) and isinstance(item.get('evidence'),list), 'effect IDs/evidence required')
            output_keys={'task_update':{'task_id'},'task_create':{'task_id'},'report_create':{'reply_id'} if effect['target_or_creation_rule'].get('kind')=='brain_reply' else {'task_id'},'attachment_add':{'task_id','attachment_id'},'notify_people':{'message_id','channel_id'}}[effect['type']]
            require(set(item['reported_ids'])<=output_keys and all(isinstance(v,str) and v for v in item['reported_ids'].values()), 'reported output IDs outside requested effect type')
            if effect['type']=='task_update' and 'task_id' in item['reported_ids']:
                require(item['reported_ids']['task_id']==effect['target_or_creation_rule']['task_id'], 'reported progress task differs from frozen target')
            if item['reported_status']=='completed':require(item['evidence'], 'completed claim requires actual reply evidence')
            for ev in item['evidence']:
                require(set(ev)=={'quote','location'} and ev['quote'] and ev['quote'] in text and ev['location'], 'reported effect evidence not in retained reply')
            if item.get('non_dispatch_quote'):
                require(item['reported_status'] in {'pending','blocked'} and item['non_dispatch_quote'] in text and any(phrase in item['non_dispatch_quote'].lower() for phrase in ('not sent','not dispatched','not created','not attached','not executed')), 'explicit actual non-dispatch statement required')
            item['verification_status']='unverified'
            item['output_authority']='reported IDs are unverified outputs, not expanded input/read/write authority'
            result[eid]=item
        return result

    def _ingest_execution(self,b,d,c,o,reply):
        namespace='clickup/'+b['workspace_id']+'/'+b['channel_id']+'/'+b['provider_root']+'/reply'
        oid='reply:'+namespace+':'+str(reply['id'])
        previous=self.db.execute('SELECT * FROM observations WHERE namespace=? AND provider_id=?',(namespace,str(reply['id']))).fetchone()
        if previous:
            if json.loads(previous['metadata'])['reply_canonical_hash']!=digest(reply):raise Conflict('changed execution reply identity')
            return False
        projection=self._execution_projection(b,d.get('projection',{}),reply['content'])
        self._observe(b,oid,namespace,str(reply['id']),o['raw'],{'call_id':c['call_id'],'reply_canonical_hash':digest(reply),
                      'serialization_basis':'captured connector JSON bytes; reply identity canonical parsed object'})
        self._after_raw_insert()
        complete=all(x['reported_status']=='completed' for x in projection.values())
        result=dict(observation_id=oid,effects=projection,coverage={},parse_gap=None,provider_date=reply.get('date'),
                    fetched_at=c['receipt']['finished_at'],ingested_at=now(),generated_at=None,
                    source_versions=copy.deepcopy(b['request']['source_versions']),
                    independent_verification='not established by AI claims',evidence_class=b['evidence_class'])
        b['returns'].append(result);b['effect_history'].append(projection);b['latest_return_id']=oid
        b['source_history'].append(result['source_versions']);b['state']='reported' if complete else 'partial'
        return True

    def _record_execution_assessment(self,b,d):
        require(all(d.get(k) for k in ('assessment_id','return_id','reviewer','provenance','authority_ref','next_permitted_step')), 'execution assessment provenance required')
        old=next((x for x in b['assessments'] if x['assessment_id']==d['assessment_id']),None)
        if old:
            if old['input_hash']!=digest(d):raise Conflict('conflicting execution assessment')
            return False
        require(d['return_id']==b['latest_return_id'] and b['latest_return_id'], 'assessment must bind latest execution return')
        requested={x['effect_id']:x for x in b['request']['effects']};items=d.get('effects')
        require(isinstance(items,dict) and set(items)==set(requested), 'exact effect assessment map required')
        for eid,item in items.items():
            require(set(item)<= {'verdict','reason','evidence','checks','binding_call_ids','transfer_ids'} and {'verdict','reason','evidence','checks'}<=set(item) and item['verdict'] in {'verified','partial','unresolved','contradicted'} and item['reason'], 'invalid effect assessment')
            require(isinstance(item['evidence'],list) and isinstance(item['checks'],dict), 'effect evidence/checks required')
            for ev in item['evidence']:
                require(all(ev.get(k) for k in ('path','sha256','location')), 'effect evidence path/hash/location required')
                require(rawhash(Path(ev['path']).read_bytes())==ev['sha256'], 'effect evidence hash mismatch')
            if item['verdict']=='verified':
                require(item['evidence'], 'verified effect needs independent evidence')
                required_checks=set(requested[eid]['verification'])
                require(set(item['checks'])==required_checks and all(v is True for v in item['checks'].values()), 'all frozen per-type checks required')
                for dep in requested[eid]['depends_on']:
                    require(items[dep]['verdict']=='verified', 'effect dependency not independently verified')
                require(b['returns'][-1]['effects'][eid]['reported_status']=='completed', 'cannot verify unreturned effect')
                effect=requested[eid];kind=effect['type']
                if not b.get('imported_nondispatchable') and not (kind=='report_create' and effect['target_or_creation_rule'].get('kind')=='brain_reply'):
                    required_kind='task_identity' if kind=='task_create' else 'notification_message' if kind=='notify_people' else 'task_content'
                    binding=self._binding(b,eid,required_kind)
                    require(binding['call_id'] in item.get('binding_call_ids',[]),'assessment must reference accepted typed current readback')
                    if kind=='attachment_add':
                        transfers=[t for t in b.get('transfers',[]) if t['effect_id']==eid and t['return_id']==b['latest_return_id']]
                        require(transfers and transfers[-1].get('valid') and transfers[-1]['transfer_id'] in item.get('transfer_ids',[]),'attachment verified requires latest exact downloaded binary hash transfer')
                        require(self._binding(b,eid,'attachment_download')['call_id']==transfers[-1]['call_id'],'latest attachment ticket supersedes transferred bytes')
        overall='verified' if all(x['verdict']=='verified' for x in items.values()) else 'contradicted' if any(x['verdict']=='contradicted' for x in items.values()) else 'partial'
        assessment=copy.deepcopy(d);assessment.update(input_hash=digest(d),overall_verdict=overall,recorded_at=now(),
            assurance='reviewer assessment with locally checked evidence hashes; semantic adequacy remains reviewer responsibility')
        b['assessments'].append(assessment)
        if overall=='verified':b['last_good_return_id']=b['latest_return_id'];b['last_good_operation']=b['id']
        return True

    def _import_execution(self,operation,owner,d):
        """Import reviewed normalized evidence, never replay historical effects.

        Domain-specific conversion belongs outside this package. Original source
        artifacts are retained byte-for-byte (or explicitly labelled sanitized).
        Normalization and parent provenance are not provider authentication.
        """
        manifest=d['import']
        required={'schema','operation_id','original_request','normalized_request_hash','artifacts','correlation',
                  'stages','accounting','provenance','retained_parent_verdict','file_bindings'}
        require(set(manifest)==required and manifest['schema']=='captured-execution-import/0.1', 'exact generic import manifest required')
        require(manifest['operation_id']==operation and manifest['provenance'], 'import identity/provenance required')
        require(manifest['normalized_request_hash']==digest(d['request']), 'normalized request changed after reviewed conversion')
        require(isinstance(manifest['artifacts'],list) and manifest['artifacts'], 'source artifacts required')
        existing=self.db.execute('SELECT id FROM operations WHERE id=?',(operation,)).fetchone()
        artifacts={};raws={}
        for item in manifest['artifacts']:
            require(set(item)=={'artifact_id','path','sha256','serialization','provenance'} and all(item.values()), 'exact artifact descriptor required')
            require(item['serialization'] in {'original_file_bytes','captured_connector_json','parent_composed_json','sanitized_connector_json'}, 'unknown serialization provenance')
            aid=item['artifact_id'];require(isinstance(aid,str) and aid and aid not in artifacts, 'unique artifact identity required')
            raw=Path(item['path']).read_bytes()
            if rawhash(raw)!=item['sha256']:
                if existing:raise Conflict('existing imported source bytes changed')
                raise Invalid('import source artifact hash mismatch')
            artifacts[aid]=item;raws[aid]=raw
        def referenced(ref):
            require(isinstance(ref,dict) and set(ref)=={'artifact_id','pointer'}, 'exact artifact/pointer reference required')
            require(ref['artifact_id'] in artifacts and isinstance(ref['pointer'],str), 'unknown artifact reference')
            value=json.loads(raws[ref['artifact_id']])
            if ref['pointer']:
                require(ref['pointer'].startswith('/'), 'JSON pointer required')
                for token in ref['pointer'][1:].split('/'):
                    token=token.replace('~1','/').replace('~0','~')
                    value=value[int(token)] if isinstance(value,list) else value[token]
            return value
        original=manifest['original_request']
        require(set(original)=={'artifact_id','sha256','original_contract'} and original['artifact_id'] in artifacts and original['original_contract'], 'original request identity required')
        require(original['sha256']==artifacts[original['artifact_id']]['sha256'] and d['packet'].encode()==raws[original['artifact_id']], 'original request bytes differ from retained packet')
        fingerprint=digest({'package':d,'artifact_hashes':{k:rawhash(v) for k,v in raws.items()}})
        if existing:
            b=self._load(operation)
            if b['owner']!=owner or b.get('import_fingerprint')!=fingerprint:raise Conflict('changed historical import or owner')
            return b,False
        b=self._create_execution(operation,owner,d,imported=True)
        corr=manifest['correlation']
        require(set(corr)=={'workspace_id','channel_id','root_id','root_ref','actor_id','provenance','original_invocation_arguments','unknown_reason','continuation_refs'}, 'exact correlation evidence required')
        require(str(corr['workspace_id'])==b['workspace_id'] and corr['channel_id']==b['channel_id'] and corr['actor_id']=='-4' and corr['root_id'] and corr['provenance'], 'historical route/actor mismatch')
        require(str(referenced(corr['root_ref']))==str(corr['root_id']), 'historical root source mismatch')
        require(isinstance(corr['continuation_refs'],list), 'explicit continuation references required')
        for ref in corr['continuation_refs']:require(referenced(ref), 'missing continuation evidence')
        if corr['original_invocation_arguments'] is None:require(corr['unknown_reason'], 'unknown historical invocation requires reason')
        accounting=manifest['accounting']
        require(set(accounting)=={'categories','unknown_costs','provenance'} and isinstance(accounting['categories'],list) and isinstance(accounting['unknown_costs'],list) and accounting['provenance'], 'measured historical accounting required')
        totals={'connector_calls':0,'http_transfers':0};seen_costs=set()
        for cost in accounting['categories']:
            require(set(cost)=={'id','kind','count','source_ref'} and cost['kind'] in totals and cost['id'] not in seen_costs, 'unique cost category required')
            require(type(cost['count']) is int and cost['count']>=0 and referenced(cost['source_ref'])==cost['count'], 'historical count differs from retained source')
            key=(cost['source_ref']['artifact_id'],cost['source_ref']['pointer'])
            require(key not in seen_costs, 'same historical count charged twice')
            seen_costs.add(cost['id']);seen_costs.add(key);totals[cost['kind']]+=cost['count']
        b['historical_accounting']=dict(totals,source_counts=copy.deepcopy(accounting),prospective_charges=0,
            provenance=manifest['provenance'],reservation_status='none; retrospective parent evidence, not helper-mediated')
        b['import_fingerprint']=fingerprint;b['provider_root']=str(corr['root_id'])
        b['import_provenance']={'original_contract':original['original_contract'],
            'normalization':'reviewed retrospective conversion; never represented as originally sent execution schema',
            'original_invocation_arguments':copy.deepcopy(corr['original_invocation_arguments']),
            'original_invocation_arguments_reason':corr['unknown_reason'],'context_assurance':corr['provenance'],
            'continuation_refs':copy.deepcopy(corr['continuation_refs'])}
        for aid,raw in raws.items():self._observe(b,'import:'+operation+':'+aid,'captured-import/'+operation,aid,raw,artifacts[aid])
        self._after_raw_insert()
        effects={e['effect_id']:e for e in b['request']['effects']}
        require(isinstance(manifest['file_bindings'],list), 'explicit file bindings required')
        for binding in manifest['file_bindings']:
            require(set(binding)=={'effect_id','artifact_id'} and binding['effect_id'] in effects and binding['artifact_id'] in artifacts, 'invalid imported file binding')
            effect=effects[binding['effect_id']]
            require(effect['type']=='attachment_add' and rawhash(raws[binding['artifact_id']])==effect['payload']['sha256'] and len(raws[binding['artifact_id']])==effect['payload']['size'], 'imported file bytes differ from approved file identity')
        require(isinstance(manifest['stages'],list) and manifest['stages'], 'actual ordered stages required')
        seen_stages=set();seen_replies=set();last_date=None;output_history={}
        for stage in manifest['stages']:
            require(set(stage)=={'stage_id','reply_ref','effects','fetched_at','fetched_at_reason','source_versions','provenance'}, 'exact historical stage fields required')
            require(stage['stage_id'] and stage['stage_id'] not in seen_stages and stage['provenance'], 'unique stage identity/provenance required')
            seen_stages.add(stage['stage_id']);reply=referenced(stage['reply_ref'])
            require(isinstance(reply,dict) and str(reply.get('user_id'))==corr['actor_id'] and reply.get('id') and isinstance(reply.get('content'),str), 'historical reply actor/identity/content missing')
            require(str(reply['id']) not in seen_replies, 'duplicate historical reply identity')
            seen_replies.add(str(reply['id']));validate_echoes(reply,b['request'])
            date=reply.get('date')
            if date is not None:
                require(type(date) is int and (last_date is None or date>=last_date), 'nonmonotonic provider reply history')
                last_date=date
            if stage['fetched_at'] is None:require(stage['fetched_at_reason'], 'unknown fetched time needs reason')
            require(isinstance(stage['source_versions'],list) and set(stage['effects'])==set(effects), 'stage requires complete scoped effect map')
            statuses={}
            for eid,item in stage['effects'].items():
                require(set(item)=={'requested_effect_hash','reported_status','reported_ids','evidence_refs','independent_refs','remaining_gap'}, 'exact normalized effect observation required')
                require(item['requested_effect_hash']==digest(effects[eid]), 'imported effect differs from reviewed requested scope')
                require(item['reported_status'] in {'completed','blocked','failed','uncertain','not-returned','pending'} and isinstance(item['reported_ids'],dict), 'invalid imported effect state/output')
                require(isinstance(item['evidence_refs'],list) and isinstance(item['independent_refs'],list), 'actual evidence references required')
                if item['reported_status']=='completed':require(item['evidence_refs'], 'completed historical claim needs source evidence')
                for ref in item['evidence_refs']+item['independent_refs']:referenced(ref)
                allowed={'task_update':{'task_id'},'task_create':{'task_id'},'report_create':{'reply_id'} if effects[eid]['target_or_creation_rule'].get('kind')=='brain_reply' else {'task_id'},'attachment_add':{'task_id','attachment_id'},'notify_people':{'message_id','channel_id'}}[effects[eid]['type']]
                require(set(item['reported_ids'])<=allowed and all(isinstance(v,str) and v for v in item['reported_ids'].values()), 'imported output ID outside effect scope')
                if effects[eid]['type']=='task_update' and 'task_id' in item['reported_ids']:
                    require(item['reported_ids']['task_id']==effects[eid]['target_or_creation_rule']['task_id'], 'imported progress task differs from frozen target')
                for key,value in item['reported_ids'].items():
                    previous=output_history.get((eid,key))
                    require(previous is None or previous==value, 'conflicting historical output identity; explicit reconciliation needed')
                    output_history[(eid,key)]=value
                statuses[eid]=dict(copy.deepcopy(item),verification_status='parent_captured_readback' if item['independent_refs'] else 'unverified',
                    provenance='retrospective normalized parent evidence; not new provider verification')
            aid=stage['reply_ref']['artifact_id'];oid='import-stage:'+operation+':'+stage['stage_id']
            self._observe(b,oid,'captured-stage/'+operation,stage['stage_id'],raws[aid],{'reply_ref':stage['reply_ref'],'provenance':stage['provenance']})
            result={'observation_id':oid,'effects':statuses,'coverage':{},'parse_gap':None,'provider_date':date,
                'fetched_at':stage['fetched_at'],'fetched_at_reason':stage['fetched_at_reason'],'ingested_at':now(),
                'generated_at':None,'source_versions':copy.deepcopy(stage['source_versions']),
                'independent_verification':'parent-captured references; no new provider verification','evidence_class':'imported',
                'retained_source_ref':stage['reply_ref'],'import_stage_id':stage['stage_id']}
            b['returns'].append(result);b['effect_history'].append(statuses)
        b['latest_return_id']=b['returns'][-1]['observation_id'];b['state']='imported_reported'
        b['retained_parent_verdict']=copy.deepcopy(manifest['retained_parent_verdict'])
        return b,True

    def _create(self, operation, owner, d):
        if d.get('request',{}).get('contract_version') in {EXECUTION, task_progress.EXECUTION}:
            return self._create_execution(operation,owner,d)
        require(owner and d.get('authority_ref') and d.get('audience_ref'), 'authority/audience evidence required')
        require(d.get('case') in self.config['cases'] and d.get('semantic_key'), 'case and semantic key required')
        require(d.get('evidence_class') in {'live','captured'}, 'explicit evidence class required')
        r = copy.deepcopy(d['request'])
        required = ('parent_run_id','operation_id','attempt_id','scope_revision','request_provenance','canonical_work',
                    'source_versions','outcome','criteria','operation','permitted_effects','prohibited_effects',
                    'data_audience','budget','control','writeback_owner')
        require(r.get('contract_version') == 'dot-authoring-delegation/v1' and all(k in r for k in required), 'exact shared v1 required')
        require(r['operation_id'] == operation and r['operation']['name'] in ALLOWED, 'unsupported operation/identity')
        require(r['control'].get('cancelled') is False, 'cancelled scope')
        require(r['data_audience'].get('visibility') == 'PRIVATE' and r['data_audience'].get('type') == 'ASK_AI', 'private ASK_AI required')
        require(d.get('workspace_id') and r['data_audience'].get('channel'), 'transport scope required')
        require(isinstance(d.get('packet'), str) and d['packet'], 'frozen packet required')
        criteria = [x.split()[0] for x in r['criteria']]
        require(criteria and len(set(criteria)) == len(criteria), 'unique criteria required')
        existing = self._all()
        require(not any(x['id'] == operation for x in existing), 'operation already exists')
        same = [x for x in existing if x['semantic_key'] == d['semantic_key']]
        require(not any(x['state'] in {'prepared','send_uncertain','waiting','partial'} for x in same), 'pending semantic duplicate blocked')
        previous = d.get('previous_operation')
        if same:
            require(previous in [x['id'] for x in same] and d.get('refresh_authority_ref'), 'linked refresh authority required')
        prior = self._load(previous) if previous else None
        if prior:
            require(prior['state'] == 'complete' and d.get('refresh_authority_ref'), 'refresh only follows complete operation')
        budget = self.config['cases'][d['case']]
        cap, reserve = budget['cap'], budget['verification_reserve']
        if d['evidence_class'] == 'live':
            require(r['parent_run_id'] == self.config['run_id'], 'run identity mismatch')
            require(r['budget']['cumulative_operation_cap'] == cap and r['budget']['reserved_verification_reporting_calls'] == reserve, 'envelope/run budget mismatch')
        return dict(id=operation, schema=FORMAT, revision=0, owner=owner, semantic_key=d['semantic_key'],
                    case=d['case'], request=r, request_hash=digest(r), packet=d['packet'], packet_hash=rawhash(d['packet'].encode()),
                    authority_ref=d['authority_ref'], audience_ref=d['audience_ref'], workspace_id=str(d['workspace_id']),
                    evidence_class=d['evidence_class'], previous_operation=previous, refresh_authority_ref=d.get('refresh_authority_ref'),
                    state='prepared', cancelled=False, calls=[], observation_ids=[], returns=[], criteria=criteria,
                    latest_return_id=None, last_good_return_id=prior['last_good_return_id'] if prior else None,
                    last_good_operation=prior['id'] if prior else None, source_history=[], cap=cap, verification_reserve=reserve,
                    provider_root=None, channel_id=r['data_audience']['channel'], handoffs=[], cancellation=None)

    def _reserve_call(self, b, d):
        require(not b.get('imported_nondispatchable'), 'historical import is non-dispatchable; continuation unsupported')
        require(not b['cancelled'], 'cancelled; no new provider work')
        require(d.get('category') in {'send','reply_read','verify','preflight'}, 'unsupported call category')
        require(d.get('call_id') and d.get('tool') and isinstance(d.get('arguments'),dict), 'exact call intent required')
        if b.get('execution') and d['category']=='verify':
            self._validate_execution_read(b,d)
        allb = self._all()
        require(not any(c['call_id'] == d['call_id'] for x in allb for c in x['calls']), 'call id already reserved; never invoke twice')
        total = self.config.get('carry_in',{}).get('charged',0) + sum(len(x['calls']) for x in allb)
        case = [c for x in allb if x['case'] == b['case'] for c in x['calls']]
        require(total < self.config['aggregate_cap'] and len(case) < b['cap'], 'aggregate/case cap exhausted')
        unverified = max(0,b['verification_reserve'] - sum(c['category']=='verify' for c in case))
        require(d['category'] == 'verify' or len(case)+1 <= b['cap']-unverified, 'protected verification reserve')
        args = d['arguments']
        tool=d['tool'].split('__')[-1]
        allowed_tools={'send':{'clickup_send_chat_message'}, 'reply_read':{'clickup_get_chat_message_replies'},
                       'verify':{'clickup_get_task','clickup_get_task_comments','clickup_get_chat_channel_messages','clickup_download_task_attachment'},
                       'preflight':{'clickup_get_chat_channels','clickup_get_chat_channel_messages'}}
        require(tool in allowed_tools[d['category']], 'unsupported provider tool/effect')
        require(str(args.get('workspace_id')) == b['workspace_id'], 'wrong workspace scope')
        if d['category']=='send':
            for effect in b['request'].get('effects',[]):
                if effect['type']=='task_update':task_progress.validate(effect,b['request'])
            require(set(args) <= {'workspace_id','channel_id','content','content_format','type'}, 'unsupported send argument: possible audience/effect expansion')
            require(args.get('content_format','text/md') in {'text/md','text/plain'} and args.get('type','message') == 'message', 'unsupported send format/type')
            require(args.get('channel_id') == b['channel_id'] and not args.get('parent_message_id'), 'wrong channel or non-top-level send')
        if d['category']=='reply_read':
            require(set(args)<={'workspace_id','message_id','limit','cursor','include_reactions'} and args.get('include_reactions',False) is False, 'reply read forbids extra arguments/reaction fanout')
            require(type(args.get('limit',100)) is int and 1<=args.get('limit',100)<=100, 'invalid reply read limit')
            require('channel_id' not in args, 'reply-read tool has no channel_id argument; derive from send receipt')
        if d['category']=='preflight':
            if tool=='clickup_get_chat_channel_messages':
                require(args.get('channel_id')==b['channel_id'], 'preflight wrong channel')
            if tool=='clickup_get_chat_message_replies':
                require(b['provider_root'] and args.get('message_id')==b['provider_root'], 'preflight must reconcile exact existing root')
        if d['category']=='verify' and not b.get('execution'):
            require(tool in {'clickup_get_task','clickup_get_task_comments'} and args.get('task_id') in b['request']['operation']['targets'], 'verification outside named task scope')
        if d['category'] == 'send':
            require(b['state']=='prepared' and not any(c['category']=='send' for c in b['calls']), 'no resend permitted')
            require(args.get('content') == b['packet'], 'send content differs from frozen packet')
            b['state'] = 'send_uncertain'
        if d['category'] == 'reply_read':
            require(b['provider_root'] and args.get('message_id') == b['provider_root'], 'exact known root required')
            require(sum(c['category']=='reply_read' for c in b['calls']) < b['request']['budget']['reply_read_allowance'], 'reply read allowance exhausted')
        if d['category']=='verify':
            require(b['latest_return_id'] is not None, 'verification follows Brain return, not native pre-synthesis')
        b['calls'].append(dict(copy.deepcopy(d), arguments_hash=digest(args), reserved_at=now(), receipt=None))
        return True

    def _record_call(self, b, d):
        matches = [c for c in b['calls'] if c['call_id']==d.get('call_id')]
        require(len(matches)==1, 'receipt requires pre-reserved call')
        c = matches[0]
        require(d.get('status') in {'success','error','timeout'} and d.get('started_at') and d.get('finished_at'), 'timed receipt status required')
        require(d.get('evidence_class') == b['evidence_class'] and d.get('context_ref'), 'receipt provenance required')
        raw = Path(d['raw_path']).read_bytes()
        receipt = {k:copy.deepcopy(v) for k,v in d.items() if k!='raw_path'}
        receipt['raw_sha256'] = rawhash(raw)
        if c['receipt']:
            if c['receipt'] != receipt:
                raise Conflict('changed call receipt')
            return False
        if c.get('verification_kind')=='attachment_download':
            wrapper=json.loads(raw)
            require(set(wrapper)<={'sanitized','omitted_fields','structuredContent','isError'} and wrapper.get('sanitized') is True and wrapper.get('omitted_fields')==['url'] and set(payload(raw))<={'success','task_id','attachment_id','title','size','mimetype','extension','custom_id'}, 'download receipt must be sanitized with no URL/token persisted')
        oid = 'call:' + d['call_id']
        self._observe(b,oid,'local-call',d['call_id'],raw,receipt)
        if c['category']=='send' and d['status']=='success':
            p = payload(raw)
            require(p.get('success') is True and p.get('message_id') and p.get('channel_id')==b['channel_id'], 'invalid send receipt')
            b['provider_root']=str(p['message_id'])
            b['state']='waiting'
        elif c['category']=='send' and d['status']=='error':
            # Error may occur after dispatch. Never infer rejection/no dispatch.
            b['state']='send_uncertain'
        if b.get('execution') and c['category']=='verify' and d['status']=='success':
            self._record_execution_read(b,c,raw)
        if c['category']=='continuation' and d['status']=='success':
            p=payload(raw)
            require(p.get('success') is True and p.get('message_id') and p.get('channel_id')==b['channel_id'],'continuation receipt wrong root-derived channel')
            item=next(x for x in b['continuations'] if x['call_id']==c['call_id'])
            item.update(state='waiting',message_id=p['message_id'])
        c['receipt']=receipt
        return True

    def _ingest(self, b, d):
        calls = [c for c in b['calls'] if c['call_id']==d.get('call_id') and c['category']=='reply_read']
        require(len(calls)==1 and calls[0]['receipt'] and calls[0]['receipt']['status']=='success', 'successful exact reply-read receipt required')
        c=calls[0]; args=c['arguments']
        require(digest(args)==c['arguments_hash'], 'call argument hash mismatch')
        require(args.get('message_id')==b['provider_root'] and str(args.get('workspace_id'))==b['workspace_id'], 'uncorrelated reply-read')
        o=self.db.execute('SELECT * FROM observations WHERE id=?',('call:'+c['call_id'],)).fetchone()
        p=payload(o['raw']); replies=p.get('replies',[])
        replies=[x for x in replies if str(x.get('id'))==str(d.get('reply_id'))]
        require(len(replies)==1, 'reply id not uniquely present in actual receipt')
        reply=replies[0]
        require(str(reply.get('user_id'))=='-4', 'wrong Brain actor')
        text=reply.get('content','')
        require(isinstance(text,str), 'reply content must be text')
        r=b['request']
        validate_echoes(reply,r)
        if b.get('execution'):
            if reply.get('continuation_id'):
                require(reply['continuation_id'] in [x['continuation_id'] for x in b.get('continuations',[])], 'unknown continuation echo')
            for echoed in re.findall(r'\bcontinuation_id\s*:\s*`?([A-Za-z0-9_-]+)',text,re.I):
                require(echoed in [x['continuation_id'] for x in b.get('continuations',[])], 'unknown continuation text echo')
            return self._ingest_execution(b,d,c,o,reply)
        namespace='clickup/'+b['workspace_id']+'/'+b['channel_id']+'/'+b['provider_root']+'/reply'
        # Keep original complete connector capture, including unknown fields.
        oid='reply:'+namespace+':'+str(reply['id'])
        previous=self.db.execute('SELECT * FROM observations WHERE namespace=? AND provider_id=?',(namespace,str(reply['id']))).fetchone()
        if previous:
            if json.loads(previous['metadata'])['reply_canonical_hash'] != digest(reply):
                raise Conflict('same reply identity with different reply payload; quarantine externally, preserved original')
            return False
        supplied=d.get('projection',{})
        require(isinstance(supplied,dict) and isinstance(supplied.get('criteria',{}),dict), 'invalid projection')
        coverage={}
        targets=set(r['operation']['targets'])
        require(set(supplied.get('criteria',{}))<=set(b['criteria']), 'unknown criterion')
        for cid in b['criteria']:
            v=copy.deepcopy(supplied.get('criteria',{}).get(cid,{'status':'not-returned','claim':None,'evidence':[]}))
            require(v.get('status') in {'answered','unresolved','not-returned'}, 'invalid coverage status')
            require(not any(k in v for k in ('verified','independently_verified')), 'AI projection cannot confer independent verification')
            if v['status']=='answered':
                require(v.get('claim') and v.get('evidence'), 'answered requires claim and evidence')
            for ev in v.get('evidence',[]):
                require(ev.get('quote') and ev['quote'] in text and ev.get('source_id') in targets and ev.get('location'), 'evidence not grounded in retained reply/source scope')
            coverage[cid]=v
        self._observe(b,oid,namespace,str(reply['id']),o['raw'],{'call_id':c['call_id'],'provider_date':reply.get('date'),'serialization_basis':'captured connector JSON bytes','projection':supplied,'reply_canonical_hash':digest(reply),'reply_hash_basis':'canonical parsed reply object; full connector bytes retained separately'})
        # Tests may inject a failure here via subclass; production has no crash CLI.
        self._after_raw_insert()
        complete=all(v['status']=='answered' for v in coverage.values()) and not supplied.get('parse_gap')
        source_versions=copy.deepcopy(supplied.get('source_versions', r['source_versions']))
        require(isinstance(source_versions,list) and all(x.get('id') in targets for x in source_versions), 'invalid source version scope')
        result=dict(observation_id=oid, coverage=coverage, parse_gap=supplied.get('parse_gap'),
                    provider_date=reply.get('date'), fetched_at=c['receipt']['finished_at'], ingested_at=now(),
                    generated_at=supplied.get('generated_at'), source_versions=source_versions,
                    independent_verification='not established by helper', evidence_class=b['evidence_class'])
        b['returns'].append(result); b['latest_return_id']=oid
        b['source_history'].append(result['source_versions'])
        b['state']='complete' if complete else 'partial'
        if complete:
            b['last_good_return_id']=oid; b['last_good_operation']=b['id']
        return True

    def _after_raw_insert(self):
        pass

    def _record_assessment(self,b,d):
        if b.get('execution'):
            return self._record_execution_assessment(b,d)
        require(all(d.get(k) for k in ('assessment_id','return_id','reviewer','provenance','authority_ref','next_permitted_step')), 'assessment identity/provenance/next step required')
        existing=next((a for a in b.get('assessments',[]) if a['assessment_id']==d['assessment_id']),None)
        if existing:
            if existing['input_hash']!=digest(d):
                raise Conflict('changed assessment with same identity')
            return False
        require(d['return_id']==b['latest_return_id'] and b['latest_return_id'] is not None, 'assessment must bind latest retained return')
        criteria=d.get('criteria')
        require(isinstance(criteria,dict) and set(criteria)==set(b['criteria']), 'assessment requires exact full criterion map')
        for cid,item in criteria.items():
            require(isinstance(item,dict) and item.get('verdict') in {'verified','partial','unresolved','contradicted'} and item.get('reason'), 'invalid criterion assessment')
            require(isinstance(item.get('evidence'),list), 'explicit evidence list required')
            if item['verdict'] in {'verified','contradicted'}:
                require(item['evidence'], 'conclusive assessment requires actual evidence')
            for ev in item['evidence']:
                require(all(ev.get(k) for k in ('path','sha256','location')), 'evidence path/hash/location required')
                require(rawhash(Path(ev['path']).read_bytes())==ev['sha256'], 'assessment evidence hash mismatch')
        latest=b['returns'][-1]
        all_verified=all(v['verdict']=='verified' for v in criteria.values())
        all_answered=all(v['status']=='answered' for v in latest['coverage'].values()) and not latest['parse_gap']
        overall=('contradicted' if any(v['verdict']=='contradicted' for v in criteria.values()) else
                 'verified' if all_verified and all_answered else
                 'unresolved' if all(v['verdict']=='unresolved' for v in criteria.values()) else 'partial')
        a=copy.deepcopy(d)
        a.update(input_hash=digest(d),overall_verdict=overall,recorded_at=now(),
                 evidence_check='local bytes matched supplied SHA256 at recording; not source freshness/authentication')
        b.setdefault('assessments',[]).append(a)
        return True

    def _cancel(self,b,d):
        require(d.get('authority_ref'), 'cancellation authority required')
        require(not b['cancelled'], 'already cancelled')
        b['cancelled']=True; b['cancellation']=dict(d,at=now())
        return True

    def _handoff(self,b,d):
        require(d.get('authority_ref') and d.get('new_owner') and d['new_owner']!=b['owner'], 'explicit handoff authority/new owner required')
        b['handoffs'].append(dict(d,from_owner=b['owner'],at=now()))
        b['owner']=d['new_owner']
        return True

    def _retained_reply(self,b,result):
        if not result:return None
        row=self.db.execute('SELECT * FROM observations WHERE id=?',(result['observation_id'],)).fetchone()
        require(row is not None,'retained reply observation missing')
        metadata=json.loads(row['metadata']);reply=None
        if metadata.get('reply_canonical_hash'):
            candidates=payload(row['raw']).get('replies',[])
            matches=[x for x in candidates if digest(x)==metadata['reply_canonical_hash']]
            require(len(matches)==1,'retained reply identity/hash missing from captured payload')
            reply=matches[0]
        elif result.get('retained_source_ref'):
            value=json.loads(row['raw']);pointer=result['retained_source_ref']['pointer']
            for token in pointer.lstrip('/').split('/') if pointer else []:
                token=token.replace('~1','/').replace('~0','~');value=value[int(token)] if isinstance(value,list) else value[token]
            reply=value
        if reply is None:return None
        text=reply['content']
        return {'reply_id':str(reply['id']),'actor_id':str(reply.get('user_id')),'provider_date':reply.get('date'),
                'content':text,'content_sha256':rawhash(text.encode()),'observation_id':result['observation_id'],
                'basis':'actual retained correlated Brain reply text; not coordinator-authored synthesis; report body versus execution-summary distinction follows frozen effect destination'}

    def hydrate(self, operation=None, scope_key=None, export=False):
        self.db.execute('BEGIN')
        try:
            if not operation:
                rows=self.db.execute('SELECT id FROM operations WHERE semantic_key=? ORDER BY rowid DESC',(scope_key,)).fetchall()
                require(rows, 'unknown semantic scope; local recovery blocked')
                operation=rows[0][0]
            b=self._load(operation); allb=self._all()
            prior=self.config.get('carry_in',{}).get('charged',0)
            total=prior+sum(len(x['calls']) for x in allb)
            counts={'charged':len(b['calls']), 'confirmed_receipts':sum(c['receipt'] is not None for c in b['calls']),
                    'unresolved_reservations':sum(c['receipt'] is None for c in b['calls']), 'aggregate_charged':total,
                    'carry_in_charged':prior,'new_run_charged':total-prior,'carry_in_evidence':self.config.get('carry_in'),
                    'aggregate_cap':self.config['aggregate_cap'],'case_cap':b['cap'], 'case_charged':sum(len(x['calls']) for x in allb if x['case']==b['case']),
                    'reused_evidence':self.config['reused_evidence']}
            last_good=None
            if b['last_good_return_id']:
                good=self._load(b['last_good_operation'])
                last_good=next((x for x in good['returns'] if x['observation_id']==b['last_good_return_id']),None)
                require(last_good is not None, 'missing last-good result')
            latest=b['returns'][-1] if b['returns'] else None
            assessment=b.get('assessments',[])[-1] if b.get('assessments') else None
            assessment_gaps=self._assessment_invalidation(b,assessment)
            assessment_current=bool(assessment and not assessment_gaps)
            sends=[{'call_id':c['call_id'],'reserved_at':c['reserved_at'],'arguments_hash':c['arguments_hash'],
                    'receipt':c['receipt'],'provider_root':b['provider_root'],'channel_id':b['channel_id']}
                   for c in b['calls'] if c['category']=='send']
            result=dict(operation_id=b['id'],objective=b['request']['outcome'],
                        scope=b['request'].get('operation',{'effects':b['request'].get('effects',[])}),criteria=b['request']['criteria'],
                        material_decisions=b['request']['request_provenance'],
                        constraints={'permitted_effects':b['request'].get('permitted_effects',b['request'].get('effects',[])),
                                     'prohibited_effects':b['request'].get('prohibited_effects',b['request'].get('exclusions',[])),
                                     'request_time_control_snapshot':{'provenance':'immutable original request; NOT current operation control',
                                                                     'value':b['request']['control']},
                                     'data_audience':b['request'].get('data_audience',b['request'].get('executor_audience'))},
                        current_control={'provenance':'current persisted operation ledger', 'state':b['state'],
                                         'cancelled':b['cancelled'], 'provider_root':b['provider_root'],
                                         'scope_revision':b['request']['scope_revision']},
                        state=b['state'],execution_contract=b['request']['contract_version'],
                        verification_bindings=b.get('verification_bindings',[]),http_transfers=b.get('transfers',[]),continuations=b.get('continuations',[]),
                        historical_accounting=b.get('historical_accounting'),import_provenance=b.get('import_provenance'),
                        imported_nondispatchable=b.get('imported_nondispatchable',False),
                        prospective_execution_support='execution/0.1 four bounded effects; opt-in execution/0.2 progress update; typed readback and protected continuation; no native domain writes',
                        execution_continuation_support='explicit non-dispatched pending effects only; deterministic same-root reservation; no retry/resend' ,
                        cancelled=b['cancelled'],owner=b['owner'],
                        provider_root=b['provider_root'],channel_id=b['channel_id'],latest_return_id=b['latest_return_id'],
                        last_good_return_id=b['last_good_return_id'],last_good_operation=b['last_good_operation'],
                        latest_result=latest,last_good_result=last_good,budget=counts,
                        actual_brain_reply=self._retained_reply(b,latest),
                        last_good_brain_reply=self._retained_reply(self._load(b['last_good_operation']),last_good) if last_good else None,
                        latest_assessment=assessment,assessment_applies_to_latest_return=assessment_current,
                        assessment_invalidation_reasons=assessment_gaps,
                        send_receipt_summary=sends,
                        authority={'authority_ref':b['authority_ref'],'audience_ref':b['audience_ref'],
                                   'assurance':'coordinator-retained references, not authenticated authorization'},
                        hash_coverage={'snapshot_hash':'read_receipt.hash covers persisted operation including assessments, not this generated hydration projection',
                                       'projection_schema':FORMAT,'helper_source_sha256':rawhash(Path(__file__).read_bytes()),
                                       'raw_observations':'separate SHA256 over retained connector bytes; validated on hydrate'},
                        source_versions=latest['source_versions'] if latest else b['request']['source_versions'],
                        request_source_versions=b['request']['source_versions'],
                        latest_fetched_at=latest['fetched_at'] if latest else None,
                        last_successful_refresh=last_good['fetched_at'] if last_good else None,
                        evidence_class=b['evidence_class'],
                        freshness='last-known stored evidence, NOT current source truth',
                        next_step=('historical import: local review only; no dispatch or continuation supported' if b.get('imported_nondispatchable') else
                                   'local receipt reconciliation only; cancellation prohibits new calls' if b['cancelled'] else
                                   assessment['next_permitted_step'] if assessment_current else
                                   'independent re-review required: assessment invalidated by newer return or supporting evidence' if assessment else
                                   'reconcile existing send; NEVER resend' if b['state']=='send_uncertain' else
                                   'independent review/targeted verification required' if b['state']=='complete' else
                                   'continue existing root only within authority and budget' if b['provider_root'] else
                                   'authorized coordinator may reserve one send'),
                        read_receipt={'schema':FORMAT,'revision':b['revision'],'hash':digest(b),'loaded_at':now(),'provider_calls':0})
            if export:
                result['private_snapshot']=b
            self.db.execute('COMMIT')
            return result
        except BaseException:
            self.db.execute('ROLLBACK'); raise

def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command',choices=['init','create','import-captured-execution','reserve-call','record-call','ingest','record-assessment','reserve-continuation','reserve-transfer','record-transfer','hydrate','export','cancel','handoff'])
    parser.add_argument('--db',required=True);parser.add_argument('--operation');parser.add_argument('--scope-key')
    parser.add_argument('--owner');parser.add_argument('--revision',type=int);parser.add_argument('--input')
    a=parser.parse_args(); store=None
    try:
        if a.command=='init':
            require(a.input,'init input required'); result=initialize(a.db,json.loads(Path(a.input).read_text()))
        else:
            store=Store(a.db,readonly=a.command in {'hydrate','export'})
            if a.command in {'hydrate','export'}:
                require(bool(a.operation)!=bool(a.scope_key),'one operation or scope key required')
                result=store.hydrate(a.operation,a.scope_key,a.command=='export')
            else:
                require(a.operation and a.owner and a.revision is not None and a.input,'mutation requires operation/owner/revision/input')
                result=store.apply(a.command,a.operation,a.owner,a.revision,json.loads(Path(a.input).read_text()))
        print(canonical(result))
    except (Invalid,sqlite3.Error,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print(canonical({'error':type(exc).__name__,'detail':str(exc),'provider_calls':0})); return 2
    finally:
        if store: store.close()
    return 0

if __name__=='__main__':
    raise SystemExit(main())
