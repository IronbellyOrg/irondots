"""Disabled native-coordinator adapter: exact commands and durable attempts, no tool calls.
Tools must be invoked by a separately authorized coordinator after live activation gates.
"""
from batch_stage import *
TOOLS={'human_reply':'clickup_send_chat_message','task_field_update':'clickup_update_task','task_comment':'clickup_create_comment'}

def command(batch,action_id,current):
    """Prepare exact allowlisted connector arguments; does not execute or approve."""
    validate(batch);a=action_map(batch)[action_id];t=a['target'];p=a['payload']
    require(isinstance(p,dict),'payload must be object')
    require(isinstance(t.get('workspace_id'),str) and t['workspace_id'].isdigit(),'exact workspace required')
    args={'workspace_id':t['workspace_id']}
    if a['kind']=='task_field_update':
        require(set(t)=={'workspace_id','task_id'},'unsupported task target fields')
        require(bool(p) and set(p)<= {'name','priority','status'},'unsupported writable fields; dates/assignment/body/custom fields require adapter extension')
        require(all(isinstance(v,str) and v for v in p.values()),'task values must be nonempty strings')
        if 'priority' in p:require(p['priority'] in {'urgent','high','normal','low','none'},'invalid priority')
        if 'status' in p:require(p['status'] in a['preconditions'].get('valid_statuses',[]),'status not verified for list')
        require(not conflicts(a['baseline'],current,p),'relevant source drift')
        args.update(task_id=t['task_id'],**p)
    elif a['kind']=='task_comment':
        require(set(t)=={'workspace_id','task_id'},'unsupported comment target')
        require(set(p)=={'comment_text','notify_all'} and isinstance(p['comment_text'],str) and p['comment_text'] and type(p['notify_all']) is bool,'exact comment and notify_all required')
        require(digest(current)==digest(a['baseline']),'comment context changed')
        args.update(entity_type='task',entity_id=t['task_id'],**p)
    else:
        require(set(p)=={'content','content_format'} and p['content_format'] in {'text/md','text/plain'} and isinstance(p['content'],str) and bool(p['content']),'exact message required')
        identity=a['recipient_evidence'];require(isinstance(identity,dict) and identity.get('kind')=='verified_humans' and identity.get('source_ref'),'verified human identity required')
        route=set(t)-{'workspace_id'};require(route in ({'user_ids'},{'channel_id'},{'parent_message_id'}),'exact one destination mode required')
        require(identity.get('target')==t,'recipient evidence target mismatch')
        if 'user_ids' in t: require(isinstance(t['user_ids'],list) and 1<=len(t['user_ids'])<=15 and all(isinstance(i,str) and i.isdigit() and int(i)>0 for i in t['user_ids']),'invalid human IDs')
        require(digest(current)==digest(a['baseline']),'message context changed')
        args.update({k:v for k,v in t.items() if k!='workspace_id'});args.update(p)
    for k in ('task_id','entity_id','channel_id','parent_message_id'):
        if k in args:require(isinstance(args[k],str) and bool(args[k]),'opaque target id required')
    return {'schema':'dot-native-command/0.1','batch_id':batch['batch_id'],'action_id':action_id,'tool':TOOLS[a['kind']],'arguments':args,'approval_fingerprint':fingerprint(a,batch),'command_hash':digest({'tool':TOOLS[a['kind']],'arguments':args}),'dispatch_enabled':False,'gates':readiness(batch,action_id,current)['gaps']}

def prepare_attempt(store,batch_id,owner,expected_revision,action_id,current,attempt_id):
    """Atomically record an exact approved command locally; no call budget consumed."""
    rev,actual_owner,b=store.load(batch_id);require(rev==expected_revision and owner==actual_owner,'stale owner/revision')
    a=action_map(b)[action_id];g=readiness(b,action_id,current)['gaps']
    local_gates=[x for x in g if x not in {'live_adapter_not_implemented','durable_execution_ownership_unverified','exact_live_write_acceptance_not_run'}]
    require(not local_gates,'preflight blocked: '+','.join(local_gates))
    require(not any(x['action_id']==action_id and x.get('state') in {'prepared','executing','uncertain','verified'} for x in b['attempts']),'existing attempt requires reconciliation')
    cmd=command(b,action_id,current);ap=next(x for x in reversed(b['approvals']) if x['action_id']==action_id and x['fingerprint']==fingerprint(a,b))
    b['attempts'].append({'id':attempt_id,'action_id':action_id,'state':'prepared','prepared_at':now(),'approval_id':ap['id'],'approval_fingerprint':ap['fingerprint'],'command':cmd,'provider_receipt':None,'network_dispatched':False})
    # Reservation is NOT a consumed provider call. Actual dispatch remains disabled.
    a['state']='preflight';newrev=store.save(b,owner,rev)
    return {'revision':newrev,'command':cmd,'dispatch_enabled':False,'network_calls':0}

def normalize_result(batch,attempt_id,provider_receipt,readback=None):
    """Normalize supplied actual evidence, never invoke transport or blindly replay.
    readback is a trusted coordinator observation, not text from Brain.
    """
    b=copy.deepcopy(batch);at=next((x for x in b['attempts'] if x['id']==attempt_id),None);require(at is not None,'unknown attempt');a=action_map(b)[at['action_id']]
    prior=[r for r in b['effect_receipts'] if r.get('attempt_id')==attempt_id]
    require(not any(r['state']=='verified' for r in prior),'already verified; do not replay')
    state='uncertain';reason='No authoritative matching readback; acknowledgment is not verified effect'
    provider_id=None
    if isinstance(provider_receipt,dict):provider_id=provider_receipt.get({'human_reply':'message_id','task_comment':'comment_id','task_field_update':'task_id'}[a['kind']])
    evidence=readback or {}
    route_ok=isinstance(provider_receipt,dict) and provider_receipt.get('success') is True
    if a['kind']=='task_field_update':route_ok=route_ok and provider_id==a['target']['task_id']
    if a['kind']=='human_reply':
        channel=(provider_receipt or {}).get('channel_id');route_ok=route_ok and bool(channel) and evidence.get('channel_id')==channel
        if 'channel_id' in a['target']:route_ok=route_ok and channel==a['target']['channel_id']
        if 'parent_message_id' in a['target']:route_ok=route_ok and evidence.get('parent_message_id')==a['target']['parent_message_id']
    if route_ok and provider_id and evidence.get('provider_id')==provider_id and evidence.get('target')==a['target'] and evidence.get('payload_hash')==digest(a['payload']) and evidence.get('independently_checked') is True and evidence.get('read_route') and evidence.get('observed_at'):
        state='verified';reason='Coordinator supplied correlated authoritative effect readback'
    rec={'id':'receipt:'+attempt_id+':'+str(len(prior)+1),'action_id':a['id'],'attempt_id':attempt_id,'state':state,'reason':reason,'provider_id':provider_id,'provider_receipt':copy.deepcopy(provider_receipt),'target':copy.deepcopy(a['target']),'payload_hash':digest(a['payload']),'independently_checked':state=='verified','observed_at':evidence.get('observed_at'),'read_route':evidence.get('read_route')}
    b['effect_receipts'].append(rec);a['state']=state;validate(b);return b
