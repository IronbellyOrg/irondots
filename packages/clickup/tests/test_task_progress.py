"""Synthetic deterministic local tests only. No fixtures confer live capability."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import brain_state as m
import task_progress as p

def fixture():
    payload={'profile':p.PROFILE,'list_id':'logical','space_file_id':'space','milestone_id':'m1','milestone':'material','state':'in_progress',
             'body_requirements':['AI summarizes evidenced milestone, no private raw logs'],'status_change':None}
    payload['payload_id']=p.payload_identity(payload);payload['marker']=p.marker(payload,'op','E1')
    fields={'name':'Existing human task','status':'active','assignees':['human'],'due_date':'date','start_date':None,'priority':None,'dependencies':['existing']}
    e={'effect_id':'E1','type':'task_update','target_or_creation_rule':{'workspace_id':'w','list_id':'l','task_id':'t'},'payload':payload,
       'baseline':{'revision':'r1','description':'Human text','description_sha256':p.sha('Human text'),'fields':fields,'evidence_ref':'synthetic baseline','fetched_at':'2026-11-02'},
       'authority_ref':'synthetic authority','depends_on':[],'side_effects':[],'verification':sorted(p.CHECKS),'capability_state':'bounded_supported'}
    r={'contract_version':p.EXECUTION,'operation_id':'op','parent_run_id':'run','scope_revision':1,'attempt_id':'1','predecessor':None,
       'request_provenance':{'original':'Synthetic offline tests only'},'coordinator':'owner','executor_audience':{'workspace_id':'w','channel_id':'c','type':'ASK_AI','visibility':'PRIVATE','evidence_ref':'synthetic'},
       'canonical_work':{'task_id':'t'},'outcome':'test','criteria':['C1 verified milestone'],'exclusions':['No unapproved changes'],'effects':[e],
       'input_files':[],'source_versions':[],'budget':{'reply_read_allowance':1,'cumulative_operation_cap':8,'reserved_verification_reporting_calls':2},'control':{'cancelled':False},'report_requirements':{'AI':'authors'}}
    return r

def reseal(r):
    e=r['effects'][0];e['payload']['payload_id']=p.payload_identity(e['payload']);e['payload']['marker']=p.marker(e['payload'],r['operation_id'],e['effect_id'])

def observed(e):
    return dict(e['baseline']['fields'],id='t',list={'id':'l'},date_updated='r2',markdown_description=e['baseline']['description']+'\n\n'+e['payload']['marker']+'\nSynthetic AI fixture text')

class ProgressTests(unittest.TestCase):
    def test_01_valid_v02_legacy_v01_rejected(self):
        r=fixture();m.validate_execution(r);r['contract_version']=m.EXECUTION
        with self.assertRaises(m.Invalid):m.validate_execution(r)
    def test_02_unknown_effect_fields_and_mutations(self):
        for mutate in [lambda e:e['payload'].update(owner='x'),lambda e:e['payload'].update(due_date='x'),lambda e:e.update(type='checklist_update'),lambda e:e['target_or_creation_rule'].update(task_id=''),lambda e:e['baseline']['fields'].pop('dependencies')]:
            r=fixture();mutate(r['effects'][0])
            with self.assertRaises(m.Invalid):m.validate_execution(r)
    def test_03_payload_marker_binding(self):
        for mutate in [lambda r:r.update(operation_id='other'),lambda r:r['effects'][0].update(effect_id='other'),lambda r:r['effects'][0]['payload'].update(list_id='other'),lambda r:r['effects'][0]['payload']['body_requirements'].append('changed')]:
            r=fixture();mutate(r)
            with self.assertRaises(m.Invalid):m.validate_execution(r)
    def test_04_existing_marker_and_bad_hash_rejected(self):
        for duplicate in (False,True):
            r=fixture();b=r['effects'][0]['baseline']
            if duplicate:b['description']+=r['effects'][0]['payload']['marker'];b['description_sha256']=p.sha(b['description'])
            else:b['description_sha256']='0'*64
            with self.assertRaises(m.Invalid):m.validate_execution(r)
    def test_05_valid_readback_preserves_fields(self):
        e=fixture()['effects'][0];self.assertTrue(p.observe(e,observed(e))['valid'])
    def test_06_readback_drift_missing_or_wrong_fields(self):
        e=fixture()['effects'][0]
        for field in p.FIELDS:
            a=observed(e);a.pop(field);self.assertFalse(p.observe(e,a)['valid'])
            a=observed(e);a[field]='unexpected';self.assertFalse(p.observe(e,a)['valid'])
        for mutate in [lambda a:a.update(id='other'),lambda a:a.update(list={'id':'other'}),lambda a:a.update(date_updated='r1'),lambda a:a.pop('date_updated'),lambda a:a.update(markdown_description='replaced human text'),lambda a:a.update(markdown_description=a['markdown_description']+e['payload']['marker'])]:
            a=observed(e);mutate(a);self.assertFalse(p.observe(e,a)['valid'])
    def test_07_status_proposal_without_real_evidence_blocked(self):
        r=fixture();r['effects'][0]['payload']['status_change']={'from':'active','to':'complete','semantic_state':'done','authority_ref':'approved','capability_evidence':{},'acceptance_ref':'checks passed','target_terminal':True};r['effects'][0]['payload']['state']='done';reseal(r)
        with self.assertRaises(m.Invalid):m.validate_execution(r)
    def test_08_status_bound_evidence_and_negative_scope(self):
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/'proof.json'
            proof={'schema':'dot-status-capability-evidence/0.1','evidence_class':'actual','independently_verified':True,'workspace_id':'w','list_id':'l','task_id':'t','before_status':'active','after_status':'complete','target_terminal':True,'authority_ref':'approved','operation_id':'synthetic-pilot','reply_id':'synthetic','verified_at':'synthetic','independent_readback_ref':'synthetic','before_ref':'synthetic','after_ref':'synthetic','reviewer':'synthetic'}
            # Shape test only: these synthetic bytes are NOT actual capability evidence.
            file.write_text(json.dumps(proof));r=fixture();pl=r['effects'][0]['payload'];pl['state']='done'
            pl['status_change']={'from':'active','to':'complete','semantic_state':'done','authority_ref':'approved','capability_evidence':{'path':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()},'acceptance_ref':'synthetic passed checks','target_terminal':True};reseal(r);m.validate_execution(r)
            a=observed(r['effects'][0]);a['status']='complete';self.assertTrue(p.observe(r['effects'][0],a)['valid'])
            for key,value in [('workspace_id','other'),('task_id','other'),('before_status','other'),('after_status','other'),('authority_ref','other'),('independently_verified',False),('evidence_class','synthetic'),('before_ref',None)]:
                bad=copy.deepcopy(proof);bad[key]=value;file.write_text(json.dumps(bad));pl['status_change']['capability_evidence']['sha256']=hashlib.sha256(file.read_bytes()).hexdigest();reseal(r)
                with self.assertRaises(m.Invalid):m.validate_execution(r)
    def test_09_cancelled_cannot_map_terminal(self):
        r=fixture();pl=r['effects'][0]['payload'];pl['state']='cancelled';pl['status_change']={'from':'active','to':'complete','semantic_state':'cancelled','authority_ref':'approved','capability_evidence':{},'acceptance_ref':'x','target_terminal':True};reseal(r)
        with self.assertRaises(m.Invalid):m.validate_execution(r)
    def test_10_registry_restart_dedup_and_unresolved_successor(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'state.db';m.initialize(db,{'run_id':'run','coordinator':'owner','authority_ref':'synthetic','aggregate_cap':8,'cases':{'P':{'cap':8,'verification_reserve':2}},'reused_evidence':[]})
            pack={'case':'P','semantic_key':'progress:logical:m1','request':fixture(),'packet':'synthetic never sent','authority_ref':'synthetic','audience_ref':'synthetic','workspace_id':'w','evidence_class':'captured'}
            store=m.Store(db);store.apply('create','op','owner',0,pack);store.close();store=m.Store(db)
            h=store.hydrate('op');self.assertEqual(h['read_receipt']['provider_calls'],0);self.assertEqual(h['scope']['effects'][0]['type'],'task_update')
            other=copy.deepcopy(pack);other['request']['operation_id']='op2';reseal(other['request'])
            with self.assertRaises(m.Invalid):store.apply('create','op2','owner',0,other)
            other['semantic_key']='progress:logical:m2';other['request']['effects'][0]['payload']['milestone_id']='m2';reseal(other['request'])
            with self.assertRaises(m.Invalid):store.apply('create','op2','owner',0,other)
            other['request']['effects'][0]['target_or_creation_rule']['list_id']='moved-list'
            with self.assertRaises(m.Invalid):store.apply('create','op2','owner',0,other)
            other['request']['effects'][0]['target_or_creation_rule']['list_id']='l'
            store.apply('cancel','op','owner',h['read_receipt']['revision'],{'authority_ref':'synthetic cancellation'})
            with self.assertRaises(m.Invalid):store.apply('reserve-call','op','owner',store.hydrate('op')['read_receipt']['revision'],{'call_id':'send','category':'send','tool':'clickup_send_chat_message','arguments':{'workspace_id':'w','channel_id':'c','content':pack['packet']}})
            store.apply('create','op2','owner',0,other)
            self.assertEqual(store.hydrate('op2')['read_receipt']['provider_calls'],0)
            store.close()
    def test_11_typed_progress_readback_binds_exact_target(self):
        e=fixture()['effects'][0];b={'execution':True,'request':fixture(),'latest_return_id':'r','workspace_id':'w','returns':[{'effects':{'E1':{'reported_ids':{'task_id':'t'}}}}]}
        d={'effect_id':'E1','effect_hash':m.digest(e),'return_id':'r','verification_kind':'task_content','tool':'clickup_get_task','arguments':{'workspace_id':'w','task_id':'t','include':['description']}}
        store=m.Store.__new__(m.Store);store._validate_execution_read(b,d)
        d['arguments']['task_id']='other'
        with self.assertRaises(m.Invalid):store._validate_execution_read(b,d)
        c={'effect_id':'E1','verification_kind':'task_content','return_id':'r','call_id':'v','arguments':{'workspace_id':'w','task_id':'t','include':['description']}}
        store._record_execution_read(b,c,json.dumps({'structuredContent':observed(e)}).encode());self.assertTrue(b['verification_bindings'][-1]['valid'])


    def test_12_changed_marker_content_conflict(self):
        e=fixture()['effects'][0];b={'execution':True,'request':fixture(),'latest_return_id':'r','workspace_id':'w','returns':[{'effects':{'E1':{'reported_ids':{'task_id':'t'}}}}]}
        c={'effect_id':'E1','verification_kind':'task_content','return_id':'r','call_id':'v','arguments':{'workspace_id':'w','task_id':'t','include':['description']}}
        store=m.Store.__new__(m.Store);a=observed(e)
        store._record_execution_read(b,c,json.dumps({'structuredContent':a}).encode())
        a['markdown_description']+=' changed';c['call_id']='v2'
        store._record_execution_read(b,c,json.dumps({'structuredContent':a}).encode())
        self.assertFalse(b['verification_bindings'][-1]['valid']);self.assertIn('same marker content changed; conflict',b['verification_bindings'][-1]['gaps'])
    def test_13_wrong_reported_task_rejected(self):
        store=m.Store.__new__(m.Store);b={'request':fixture()}
        projection={'effects':{'E1':{'reported_status':'completed','reported_ids':{'task_id':'wrong'},'evidence':[{'quote':'completed','location':'synthetic'}]}}}
        with self.assertRaises(m.Invalid):store._execution_projection(b,projection,'completed')
    def test_14_one_update_per_envelope(self):
        r=fixture();other=copy.deepcopy(r['effects'][0]);other['effect_id']='E2';other['payload']['marker']=p.marker(other['payload'],'op','E2');r['effects'].append(other)
        with self.assertRaises(m.Invalid):m.validate_execution(r)
    def test_15_send_revalidates_capability(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'state.db';m.initialize(db,{'run_id':'run','coordinator':'owner','authority_ref':'synthetic','aggregate_cap':8,'cases':{'P':{'cap':8,'verification_reserve':2}},'reused_evidence':[]})
            pack={'case':'P','semantic_key':'progress:logical:m1','request':fixture(),'packet':'synthetic never sent','authority_ref':'synthetic','audience_ref':'synthetic','workspace_id':'w','evidence_class':'captured'}
            store=m.Store(db);store.apply('create','op','owner',0,pack)
            with patch.object(p,'validate',side_effect=m.Invalid('changed retained capability artifact')) as gate:
                with self.assertRaises(m.Invalid):store.apply('reserve-call','op','owner',store.hydrate('op')['read_receipt']['revision'],{'call_id':'send','category':'send','tool':'clickup_send_chat_message','arguments':{'workspace_id':'w','channel_id':'c','content':pack['packet']}})
                gate.assert_called_once()
            self.assertEqual(store.hydrate('op')['budget']['charged'],0);store.close()
    def test_16_continuation_revalidates_capability(self):
        store=m.Store.__new__(m.Store);r=fixture();r['request_provenance']={'original':'approved exact scope'}
        b={'execution':True,'cancelled':False,'authority_ref':'authority','request':r,'provider_root':'root','calls':[],
           'latest_return_id':'ret','assessments':[{'return_id':'ret','assessment_id':'a'}],
           'returns':[{'effects':{'E1':{'reported_status':'pending'}}}]}
        d={'call_id':'next','continuation_id':'next','effect_ids':['E1'],'authority_ref':'authority','authority_quote':'approved exact scope','assessment_id':'a'}
        with patch.object(store,'_assessment_invalidation',return_value=[]),patch.object(p,'validate',side_effect=m.Invalid('changed retained capability artifact')) as gate:
            with self.assertRaises(m.Invalid):store._reserve_continuation(b,d)
            gate.assert_called_once()

if __name__=='__main__':unittest.main()
