"""Local validation for opt-in progress. No provider calls; evidence is not authentication."""
import hashlib
import json
from pathlib import Path
from batch_stage import digest, require

PROFILE = 'dot-task-list-progress/0.1'
EXECUTION = 'dot-brain-execution/0.2'
FIELDS = {'name', 'status', 'assignees', 'due_date', 'start_date', 'priority', 'dependencies'}
CHECKS = {'ai_authorship', 'complete_content', 'approved_destination', 'excluded_private_data',
          'baseline_precondition', 'human_content_preserved', 'owned_marker', 'no_unapproved_fields', 'status_mapping'}

def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()

def payload_identity(p):
    return digest({k:v for k,v in p.items() if k not in {'payload_id','marker'}})

def marker(p, operation, effect):
    return '<!-- dot-progress:' + digest({'list':p['list_id'], 'operation':operation, 'effect':effect, 'payload':p['payload_id']}) + ' -->'

def validate(e, r):
    t,p,b=e['target_or_creation_rule'],e['payload'],e['baseline']
    require(set(t)=={'workspace_id','list_id','task_id'} and all(isinstance(v,str) and v for v in t.values()), 'exact existing progress target required')
    require(t['workspace_id']==str(r['executor_audience']['workspace_id']), 'progress workspace mismatch')
    require(set(p)=={'profile','list_id','space_file_id','milestone_id','milestone','state','body_requirements','payload_id','marker','status_change'}, 'exact progress payload required')
    require(p['profile']==PROFILE and all(isinstance(p[k],str) and p[k] for k in ('list_id','space_file_id','milestone_id')), 'stable list/file/milestone identities required')
    require(p['milestone'] in {'initial','material','final'} and p['state'] in {'backlog','in_progress','blocked','done','cancelled'}, 'invalid milestone/state')
    require(isinstance(p['body_requirements'],list) and p['body_requirements'] and all(isinstance(x,str) and x for x in p['body_requirements']), 'AI content requirements required')
    require(p['payload_id']==payload_identity(p) and p['marker']==marker(p,r['operation_id'],e['effect_id']), 'progress payload/marker identity mismatch')
    require(set(b)=={'revision','description','description_sha256','fields','evidence_ref','fetched_at'} and b['revision'] and b['evidence_ref'] and b['fetched_at'], 'observed revision/evidence required')
    require(isinstance(b['description'],str) and b['description_sha256']==sha(b['description']), 'full baseline description hash required')
    require(p['marker'] not in b['description'], 'marker already present; reconcile existing effect, never append again')
    require(isinstance(b['fields'],dict) and set(b['fields'])==FIELDS, 'all preserved source fields must be observed, not omitted')
    s=p['status_change']
    if s is not None:
        require(isinstance(s,dict) and set(s)=={'from','to','semantic_state','authority_ref','capability_evidence','acceptance_ref','target_terminal'}, 'exact conditional status change required')
        require(s['from']==b['fields']['status'] and s['to'] and s['from']!=s['to'] and s['semantic_state']==p['state'] and s['authority_ref'], 'status baseline/mapping/authority mismatch')
        require(type(s['target_terminal']) is bool, 'observed terminal classification required')
        require(not s['target_terminal'] or (p['state']=='done' and s['acceptance_ref']), 'only accepted done maps to terminal success')
        require(p['state']!='done' or (s['target_terminal'] and s['acceptance_ref']), 'done needs suitable terminal mapping and acceptance')
        ev=s['capability_evidence']
        require(isinstance(ev,dict) and set(ev)=={'path','sha256'}, 'actual retained capability artifact required')
        raw=Path(ev['path']).read_bytes()
        require(hashlib.sha256(raw).hexdigest()==ev['sha256'], 'capability artifact hash mismatch')
        proof=json.loads(raw)
        require(proof.get('schema')=='dot-status-capability-evidence/0.1' and proof.get('evidence_class')=='actual' and proof.get('independently_verified') is True, 'status capability not actual independently verified evidence')
        require(proof.get('workspace_id')==t['workspace_id'] and proof.get('task_id')==t['task_id'] and proof.get('list_id')==t['list_id'], 'status capability target applicability mismatch')
        require(proof.get('before_status')==s['from'] and proof.get('after_status')==s['to'] and proof.get('target_terminal') is s['target_terminal'], 'status capability transition mismatch')
        require(proof.get('authority_ref')==s['authority_ref'] and all(proof.get(k) for k in ('operation_id','reply_id','verified_at','independent_readback_ref','before_ref','after_ref','reviewer')), 'status capability provenance incomplete')
    require(set(e['verification'])==CHECKS, 'exact progress verification criteria required')

def observe(e, actual):
    """Typed readback; semantic AI authorship/precondition review remains independent."""
    t,p,b=e['target_or_creation_rule'],e['payload'],e['baseline'];gaps=[]
    if actual.get('id')!=t['task_id'] or actual.get('list',{}).get('id')!=t['list_id']:gaps.append('progress task/container mismatch')
    text=actual.get('markdown_description')
    prefix=b['description']+'\n\n'+p['marker']+'\n'
    if not isinstance(text,str) or not text.startswith(prefix) or text.count(p['marker'])!=1 or not 1<=len(text[len(prefix):])<=3000:
        gaps.append('full human prefix/unique owned marker/compact append mismatch')
    if not actual.get('date_updated') or actual['date_updated']==b['revision']:gaps.append('updated revision not observed')
    for key in FIELDS:
        expected=p['status_change']['to'] if key=='status' and p['status_change'] else b['fields'][key]
        if key not in actual or actual[key]!=expected:gaps.append('missing/changed unapproved field: '+key)
    return {'valid':not gaps,'gaps':gaps,'task_id':t['task_id'],'list_id':t['list_id'],
            'observed_revision':actual.get('date_updated'),'description_sha256':sha(text) if isinstance(text,str) else None,
            'progress_text':text[len(prefix):] if isinstance(text,str) and text.startswith(prefix) else None}
