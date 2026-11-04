#!/usr/bin/env python3
"""ClickUp local staging. No connector/network/dispatch adapter. Python stdlib only."""
import argparse, copy, datetime, hashlib, json, sqlite3
from pathlib import Path
SCHEMA='dot-approved-batch/0.1'
MATERIAL=('id','kind','target','recipient_evidence','payload','baseline','depends_on','preconditions','side_effects','verification')
KINDS={'human_reply','task_field_update','task_comment'}
STATES={'proposed','reviewed','approved','preflight','executing','verified','failed','uncertain','skipped','cancelled','needs_decision'}
class Invalid(ValueError): pass
class Conflict(Invalid): pass

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def canonical(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def digest(v): return hashlib.sha256(canonical(v).encode()).hexdigest()
def require(ok,msg):
    if not ok: raise Invalid(msg)
def material_hash(action): return digest({k:action[k] for k in MATERIAL})
def fingerprint(action,batch): return digest({'batch_id':batch['batch_id'],'scope_revision':batch['scope_revision'],'scope':batch['scope'],'privacy':batch['privacy'],**{k:action[k] for k in MATERIAL}})
def field(raw,key):
    if key not in raw:return {'state':'not-returned'}
    v=raw[key]
    return {'state':'explicit-null' if v is None else 'empty' if v in ('',[],{}) else 'value','value':copy.deepcopy(v)}
def observation(kind,raw,workspace,*,fetched_at=None,source_updated_at=None,endpoint=None,coverage='partial',principal=None,query=None):
    require(isinstance(raw,dict) and isinstance(raw.get('id'),str),'opaque string source id required')
    return {'schema':'source-observation/1.0','key':['clickup',str(workspace),kind,raw['id']], 'raw':copy.deepcopy(raw),'payload_hash':digest(raw),'present_fields':sorted(raw),'source_updated_at':source_updated_at,'fetched_at':fetched_at,'endpoint':endpoint,'principal':principal,'query':query,'coverage':coverage,'adapter_version':'1.0','privacy':'source-restricted','visibility':'observed','errors':[]}
def conflicts(baseline,current,patch): return [k for k in patch if digest(field(baseline,k))!=digest(field(current,k))]
def action_map(batch):return {a['id']:a for a in batch['actions']}
def validate(b):
    require(b.get('schema')==SCHEMA,'unsupported schema')
    for k in ('batch_id','scope_revision','scope','privacy','observations','projections','relationships','coverage_checkpoints','actions','approvals','attempts','effect_receipts','handoffs','budget','persistence','dispatch_enabled'):require(k in b,'missing '+k)
    require(isinstance(b['batch_id'],str) and b['batch_id'] and b['batch_id']!='REPLACE','batch identity required')
    require(type(b['scope_revision']) is int and b['scope_revision']>0,'invalid scope revision')
    require(b['dispatch_enabled'] is False,'this release cannot enable dispatch')
    for key in ('observations','projections','relationships','coverage_checkpoints','actions','approvals','attempts','effect_receipts','handoffs'):require(isinstance(b[key],list),'expected list '+key)
    for o in b['observations']:
        require(o['payload_hash']==digest(o['raw']),'source payload hash mismatch')
        require(o['present_fields']==sorted(o['raw']),'presence mismatch')
        require(len(o['key'])==4 and all(isinstance(x,str) and x for x in o['key']),'invalid source key')
        require(o['raw']['id']==o['key'][3],'source identity mismatch')
    acts=action_map(b)
    require(len(acts)==len(b['actions']),'duplicate action id')
    for a in b['actions']:
        require(all(k in a for k in MATERIAL),'missing material action fields')
        require(isinstance(a['id'],str) and a['id'],'invalid action id')
        require(a['kind'] in KINDS,'unsupported effect kind')
        require(a.get('state') in STATES,'unsupported action state')
        require(isinstance(a['target'],dict) and bool(a['target']),'exact target required')
        require(isinstance(a['depends_on'],list) and all(d in acts and d!=a['id'] for d in a['depends_on']),'invalid dependency')
    visited=set();active=set()
    def visit(i):
        require(i not in active,'dependency cycle')
        if i in visited:return
        active.add(i)
        for d in acts[i]['depends_on']:visit(d)
        active.remove(i);visited.add(i)
    for i in acts:visit(i)
    for collection in ('approvals','attempts','effect_receipts'):
        ids=[x['id'] for x in b[collection]]
        require(len(ids)==len(set(ids)),'duplicate '+collection+' id')
        for r in b[collection]:require(r['action_id'] in acts,'unknown action reference')
    for ap in b['approvals']:
        require(bool(ap.get('user_instruction_ref')) and bool(ap.get('approved_at')),'actual approval evidence required')
        require(bool(ap.get('fingerprint')) and bool(ap.get('material_hash')),'approval fingerprint missing')
    for r in b['effect_receipts']:
        require(r.get('state') in {'verified','pending','failed','uncertain','not_run'},'invalid receipt state')
        if r['state']=='verified':
            require(r.get('independently_checked') is True,'uncorroborated effect')
            for k in ('provider_id','observed_at','read_route','target','payload_hash','attempt_id'): require(bool(r.get(k)),'receipt missing '+k)
            a=acts[r['action_id']]
            require(r['target']==a['target'] and r['payload_hash']==digest(a['payload']),'receipt effect mismatch')
            attempt=next((x for x in b['attempts'] if x['id']==r['attempt_id'] and x['action_id']==a['id']),None)
            require(attempt is not None,'receipt attempt mismatch')
            require(any(ap['id']==attempt.get('approval_id') and ap['action_id']==a['id'] and ap['material_hash']==material_hash(a) and ap['fingerprint']==attempt.get('approval_fingerprint') for ap in b['approvals']),'receipt lacks frozen approval correlation')
    for a in b['actions']:
        if a['state']=='verified':
            require(any(r['action_id']==a['id'] and r['state']=='verified' for r in b['effect_receipts']),'verified action lacks receipt')
            require(any(ap['action_id']==a['id'] and ap['material_hash']==material_hash(a) for ap in b['approvals']),'verified action lacks material approval')
    budget=b['budget']
    for k in ('limit','reserve','consumed'):require(type(budget[k]) is int and budget[k]>=0,'invalid budget')
    require(budget['reserve']<=budget['limit'] and budget['consumed']<=budget['limit'],'budget overflow')
    require(sum(x['count'] for x in budget['events'])==budget['consumed'],'budget ledger mismatch')
    for e in budget['events']:require(type(e['count']) is int and e['count']>=0,'invalid call count')
    for rel in b['relationships']:
        for k in ('type','source','target','resolution'):require(k in rel,'relationship missing '+k)
        require(rel['resolution'] in {'resolved','unresolved','inaccessible','not-fetched'},'invalid relationship resolution')
    for projection in b['projections']:
        for k in ('schema','source_key','fields'):require(k in projection,'projection missing '+k)
        require(any(o['key']==projection['source_key'] for o in b['observations']),'projection source missing')
    for handoff in b['handoffs']:
        for k in ('id','schema','batch_id','status','scope_revision','action_states','generated_at','source_versions','receipt_ids','unresolved','next_step','audience'):require(k in handoff,'handoff missing '+k)
        require(handoff['schema']=='dot-batch-handoff/0.1' and handoff['batch_id']==b['batch_id'],'handoff identity/schema mismatch')
        require(handoff['status'] in {'verified','partial','failed','cancelled'},'handoff status invalid')
        require(type(handoff['scope_revision']) is int and 0<handoff['scope_revision']<=b['scope_revision'],'handoff revision invalid')
        snapshot=handoff['action_states']
        require(isinstance(snapshot,dict) and all(i in acts and v in STATES for i,v in snapshot.items()),'invalid handoff action snapshot')
        receipts=[r for r in b['effect_receipts'] if r['id'] in handoff['receipt_ids']]
        require(len(receipts)==len(handoff['receipt_ids']),'handoff receipt missing/duplicate')
        for i,state in snapshot.items():
            if state=='verified': require(any(r['action_id']==i and r['state']=='verified' for r in receipts),'handoff verified effect missing receipt')
        pending={i for i,state in snapshot.items() if state not in {'verified','cancelled','skipped'}}
        require({u['action_id'] for u in handoff['unresolved']}==pending,'handoff unresolved coverage mismatch')
        for u in handoff['unresolved']:
            require(all(u.get(k) for k in ('owner','blocker','next_step')),'unresolved handoff lacks ownership/recovery')
        if handoff['status']=='verified':require(all(v=='verified' for v in snapshot.values()) and not handoff['unresolved'],'handoff overclaims completion')
    return True

def approve(b,action_id,user_instruction_ref,approval_id):
    b=copy.deepcopy(b);a=action_map(b)[action_id]
    require(a['state'] in {'proposed','reviewed','approved','needs_decision'},'cannot approve completed/in-flight action')
    b['approvals'].append({'id':approval_id,'action_id':action_id,'fingerprint':fingerprint(a,b),'material_hash':material_hash(a),'scope_snapshot':{'batch_id':b['batch_id'],'scope_revision':b['scope_revision'],'scope':copy.deepcopy(b['scope']),'privacy':copy.deepcopy(b['privacy'])},'user_instruction_ref':user_instruction_ref,'approved_at':now()});a['state']='approved';validate(b);return b

def readiness(b,action_id,current=None):
    validate(b);a=action_map(b)[action_id];gaps=[]
    if a['state']!='approved':gaps.append('action_not_approved')
    if b.get('cancellation'):gaps.append('batch_cancelled')
    if not any(x['action_id']==action_id and x['fingerprint']==fingerprint(a,b) for x in b['approvals']):gaps.append('exact_approval_missing_or_drifted')
    if any(action_map(b)[d]['state']!='verified' for d in a['depends_on']):gaps.append('dependency_not_verified')
    if current is None:gaps.append('live_preflight_missing')
    elif a['kind']=='task_field_update' and conflicts(a['baseline'],current,a['payload']):gaps.append('source_conflict')
    elif a['kind']!='task_field_update' and digest(current)!=digest(a['baseline']):gaps.append('context_changed')
    gaps+=['live_adapter_not_implemented','durable_execution_ownership_unverified','exact_live_write_acceptance_not_run']
    return {'action_id':action_id,'dispatch_ready':False,'gaps':gaps}

def consume(b,category,count=1,reserved=False):
    b=copy.deepcopy(b);q=b['budget'];require(type(count) is int and count>=0,'invalid count')
    require(not reserved or category in {'verification','reporting'},'reserve limited to verification/reporting')
    ceiling=q['limit'] if reserved else q['limit']-q['reserve'];require(q['consumed']+count<=ceiling,'budget exhausted')
    q['events'].append({'category':category,'count':count,'at':now()});q['consumed']+=count;validate(b);return b

class Store:
    """Local SQLite CAS snapshots + immutable event history. Not a network publisher lock."""
    def __init__(self,path):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path,timeout=2,isolation_level=None)
        require(self.db.execute('PRAGMA user_version').fetchone()[0] in {0,1},'unsupported database schema')
        self.db.execute('PRAGMA journal_mode=DELETE');self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,revision INTEGER NOT NULL,owner TEXT NOT NULL,body TEXT NOT NULL); CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,id TEXT NOT NULL,revision INTEGER NOT NULL,owner TEXT NOT NULL,at TEXT NOT NULL,body TEXT NOT NULL,UNIQUE(id,revision));')
        self.db.execute('PRAGMA user_version=1')
    def close(self):self.db.close()
    def load(self,batch_id):
        row=self.db.execute('SELECT revision,owner,body FROM batches WHERE id=?',(batch_id,)).fetchone()
        require(row is not None,'unknown batch');return row[0],row[1],json.loads(row[2])
    def save(self,b,owner,expected_revision=0):
        validate(b);require(isinstance(owner,str) and bool(owner),'owner required')
        body=canonical(b);self.db.execute('BEGIN IMMEDIATE')
        try:
            row=self.db.execute('SELECT revision,owner,body FROM batches WHERE id=?',(b['batch_id'],)).fetchone()
            if row:
                if row[0]!=expected_revision or row[1]!=owner:raise Conflict('revision/owner conflict')
                old=json.loads(row[2])
                for k in ('observations','approvals','attempts','effect_receipts','handoffs'):
                    require(digest(b[k][:len(old[k])])==digest(old[k]),'immutable history altered: '+k)
                require(b['budget']['events'][:len(old['budget']['events'])]==old['budget']['events'],'budget history altered')
                require(b['scope_revision']>=old['scope_revision'],'scope revision regressed')
                new_actions=action_map(b)
                for previous in old['actions']:
                    require(previous['id'] in new_actions,'action history removed')
                    updated=new_actions[previous['id']]
                    if previous['state'] in {'verified','executing','uncertain'}:
                        require(material_hash(updated)==material_hash(previous),'in-flight/completed intent changed')
                        allowed={'verified':{'verified'},'executing':{'executing','verified','uncertain'},'uncertain':{'uncertain','verified'}}
                        require(updated['state'] in allowed[previous['state']],'unsafe action replay/reversion')
            elif expected_revision!=0:raise Conflict('missing baseline')
            prior_count=len(json.loads(row[2])['handoffs']) if row else 0
            for handoff in b['handoffs'][prior_count:]:
                require(handoff['scope_revision']==b['scope_revision'],'new handoff revision mismatch')
                require(handoff['action_states']=={a['id']:a['state'] for a in b['actions']},'new handoff must cover actual full action state')
            rev=expected_revision+1
            self.db.execute('INSERT INTO events(id,revision,owner,at,body) VALUES(?,?,?,?,?)',(b['batch_id'],rev,owner,now(),body))
            self.db.execute('INSERT INTO batches VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET revision=excluded.revision,body=excluded.body',(b['batch_id'],rev,owner,body))
            self.db.execute('COMMIT');return rev
        except BaseException:
            self.db.execute('ROLLBACK');raise

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('command',choices=['validate','stage','export','readiness']);ap.add_argument('--input');ap.add_argument('--db');ap.add_argument('--batch');ap.add_argument('--owner');ap.add_argument('--revision',type=int,default=0);ap.add_argument('--action');args=ap.parse_args()
    b=json.loads(Path(args.input).read_text()) if args.input else None
    if args.command=='validate':validate(b);print('{"valid":true,"dispatch_ready":false}')
    elif args.command=='readiness':print(json.dumps(readiness(b,args.action),indent=2))
    else:
        s=Store(args.db)
        try:
            if args.command=='stage': print(json.dumps({'revision':s.save(b,args.owner,args.revision),'dispatch_ready':False}))
            else:
                revision,owner,b=s.load(args.batch);print(json.dumps({'revision':revision,'owner':owner,'batch':b},indent=2))
        finally:s.close()
if __name__=='__main__':main()
