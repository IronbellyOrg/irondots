import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_validate_record import record, validator, SCRIPT


def event(seq, typ, roles, packet=None, stage='independent'):
    return dict(seq=seq, type=typ, role_ids=roles, packet_id=packet, stage=stage, evidence='synthetic-receipt-%s' % seq)


def isolated():
    r = record(); r['contract_version'] = 'dot-adversarial-result/1.1'
    roles = [dict(id=rid, agent_id='agent-' + rid, role=role, fork_turns='none', fresh=True, history_state='none', dispatch_evidence='synthetic-dispatch-' + rid) for rid, role in [('c', 'coordinator'), ('a', 'advocate'), ('b', 'advocate')]]
    packet = dict(id='p', kind='original', source_snapshot_ids=['s1', 's2'], digest='a'*64, origin_run_id=None)
    r['isolation'] = dict(protocol_version='dot-debate-isolation/1.0', status='procedural_only', claim='independent_attempt', limitations=['Synthetic fixture: access boundary and full read audit are not established.'], plan=dict(depth='quick',reviewer_required=False), roles=roles, packets=[packet], events=[event(1,'dispatch',['c','a','b'],'p','initial'),event(2,'read',['c','a','b'],'p','initial'),event(3,'stage_complete',['a','b']),event(4,'verdict_lock',['c'],stage='lock')], controls=dict(access_boundary='unverified',read_audit='partial',evidence=[]), verdict_lock=dict(seq=4,digest='b'*64,artifact='synthetic-locked-verdict.json',evidence='synthetic-receipt-4'),prior_results=dict(state='not_present',reveal_seq=None))
    return r


class IsolationTests(unittest.TestCase):
    def invalid(self, mutate):
        r=isolated(); mutate(r); self.assertTrue(validator.validate(r))

    def test_valid_procedural_record(self): self.assertEqual(validator.validate(isolated()), [])
    def test_legacy_record_is_readable(self): self.assertEqual(validator.validate(record()), [])
    def test_new_record_requires_isolation(self): self.invalid(lambda r:r.pop('isolation'))
    def test_missing_each_isolation_field(self):
        for key in isolated()['isolation']:
            with self.subTest(key=key): self.invalid(lambda r:r['isolation'].pop(key))
    def test_verified_declarations(self):
        r=isolated(); i=r['isolation']; i.update(status='verified',claim='controlled_comparison'); i['controls'].update(access_boundary='verified',read_audit='complete',evidence=['synthetic-control-receipt'])
        self.assertEqual(validator.validate(r), [])
    def test_unverified_control_claim(self): self.invalid(lambda r:r['isolation'].update(claim='controlled_comparison'))
    def test_incomplete_audit_control_claim(self):
        def change(r):
            i=r['isolation']; i.update(status='verified',claim='controlled_comparison');i['controls'].update(access_boundary='verified',evidence=['receipt'])
        self.invalid(change)
    def test_verified_no_control_evidence(self):
        def change(r):
            i=r['isolation']; i.update(status='verified',claim='controlled_comparison');i['controls'].update(access_boundary='verified',read_audit='complete')
        self.invalid(change)
    def test_procedural_limit_required(self): self.invalid(lambda r:r['isolation'].update(limitations=[]))
    def test_unknown_cannot_complete(self): self.invalid(lambda r:r['isolation'].update(status='unknown'))
    def test_inherited_history(self): self.invalid(lambda r:r['isolation']['roles'][0].update(history_state='present'))
    def test_fork_all(self): self.invalid(lambda r:r['isolation']['roles'][0].update(fork_turns='all'))
    def test_reused_agent(self): self.invalid(lambda r:r['isolation']['roles'][0].update(fresh=False))
    def test_same_agent_multiple_roles(self): self.invalid(lambda r:r['isolation']['roles'][0].update(agent_id='agent-a'))
    def test_missing_coordinator(self): self.invalid(lambda r:r['isolation']['roles'][0].update(role='advocate'))
    def test_not_enough_advocates(self): self.invalid(lambda r:r['isolation']['roles'][1].update(role='generator'))
    def test_probe_needs_reviewer(self): self.invalid(lambda r:r['invariant_probe'].update(state='performed',reviewer_provenance='receipt'))
    def test_unverified_history_procedural_only(self):
        r=isolated();r['isolation']['roles'][0]['history_state']='unverified';self.assertEqual(validator.validate(r), [])
    def test_truthful_contaminated_partial(self):
        r=isolated();r.update(state='partial',reason='Inherited history invalidated the clean attempt.');i=r['isolation'];i.update(status='contaminated',claim='contaminated');i['roles'][0]['history_state']='present'
        self.assertEqual(validator.validate(r), [])
    def test_complete_contamination_forbidden(self): self.invalid(lambda r:r['isolation'].update(status='contaminated',claim='contaminated'))
    def test_blocked_without_dispatch_is_honest(self):
        r=isolated();r.update(state='blocked',reason='No fresh worker capacity.');i=r['isolation'];i.update(status='unknown',roles=[],packets=[],events=[],verdict_lock=None)
        self.assertEqual(validator.validate(r), [])
    def test_invalid_hash(self): self.invalid(lambda r:r['isolation']['packets'][0].update(digest='not-a-hash'))
    def test_source_id_mismatch(self): self.invalid(lambda r:r['isolation']['packets'][0].update(source_snapshot_ids=['other']))
    def test_current_run_wrong_identity(self):
        self.invalid(lambda r:r['isolation']['packets'].append(dict(id='x',kind='current_run',source_snapshot_ids=[],digest='c'*64,origin_run_id='other')))
    def test_initial_prior_packet(self):
        def change(r): r['isolation']['packets'][0].update(kind='prior_run',origin_run_id='old')
        self.invalid(change)
    def test_initial_current_packet(self):
        def change(r):r['isolation']['packets'][0].update(kind='current_run',origin_run_id='r1')
        self.invalid(change)
    def test_duplicate_sequence(self): self.invalid(lambda r:r['isolation']['events'][1].update(seq=1))
    def test_boolean_sequence(self): self.invalid(lambda r:r['isolation']['events'][0].update(seq=True))
    def test_unknown_event_role(self): self.invalid(lambda r:r['isolation']['events'][1].update(role_ids=['unknown']))
    def test_unknown_event_packet(self): self.invalid(lambda r:r['isolation']['events'][1].update(packet_id='unknown'))
    def test_missing_lock(self): self.invalid(lambda r:r['isolation'].update(verdict_lock=None))
    def test_lock_sequence_mismatch(self): self.invalid(lambda r:r['isolation']['verdict_lock'].update(seq=3))
    def test_advocate_cannot_lock(self): self.invalid(lambda r:r['isolation']['events'][-1].update(role_ids=['a']))
    def test_missing_independent_output(self): self.invalid(lambda r:r['isolation']['events'][2].update(role_ids=['a']))
    def test_lock_before_independent_output(self):
        def change(r):
            i=r['isolation'];i['events'][2],i['events'][3]=i['events'][3],i['events'][2];i['events'][2]['seq']=3;i['events'][3]['seq']=4;i['verdict_lock']['seq']=3
        self.invalid(change)
    def test_unequal_initial_packets(self):
        def change(r):
            i=r['isolation'];i['packets'].append(dict(i['packets'][0],id='p2'));i['events'][0]['role_ids']=['c','a'];i['events'].insert(1,event(2,'dispatch',['b'],'p2','initial'))
            for n,e in enumerate(i['events'],1):e['seq']=n
            i['verdict_lock']['seq']=5
        self.invalid(change)
    def add_prior(self,r,before=False):
        i=r['isolation'];i['packets'].append(dict(id='old',kind='prior_run',source_snapshot_ids=[],digest='d'*64,origin_run_id='r0'))
        e=event(5,'prior_reveal',['c'],'old','post_lock')
        if before:
            i['events'].insert(3,e)
            for n,x in enumerate(i['events'],1):x['seq']=n
            i['verdict_lock']['seq']=5;i['prior_results'].update(state='revealed',reveal_seq=4)
        else:i['events'].append(e);i['prior_results'].update(state='revealed',reveal_seq=5)
    def test_post_lock_reveal(self):
        r=isolated();self.add_prior(r);self.assertEqual(validator.validate(r), [])
    def test_prior_read_is_exposure(self):
        r=isolated();self.add_prior(r);r['isolation']['events'][-1]['type']='read';self.assertEqual(validator.validate(r), [])
    def test_prelock_reveal_rejected(self): self.invalid(lambda r:self.add_prior(r,True))
    def test_truthful_prelock_contamination(self):
        r=isolated();self.add_prior(r,True);r.update(state='partial',reason='Accidental early read.');r['isolation'].update(status='contaminated',claim='contaminated');self.assertEqual(validator.validate(r), [])
    def test_prior_exposure_not_withheld(self):
        def change(r):self.add_prior(r);r['isolation']['prior_results'].update(state='withheld',reveal_seq=None)
        self.invalid(change)
    def test_reveal_needs_actual_event(self): self.invalid(lambda r:r['isolation']['prior_results'].update(state='revealed',reveal_seq=10))
    def add_current(self,r,early=False,reviewer=False):
        i=r['isolation'];i['packets'].append(dict(id='new',kind='current_run',source_snapshot_ids=[],digest='e'*64,origin_run_id='r1'))
        i['roles'].append(dict(id='v',agent_id='agent-v',role='reviewer',fork_turns='none',fresh=True,history_state='none',dispatch_evidence='receipt-v'))
        i['events'][0]['role_ids'].append('v');i['events'][1]['role_ids'].append('v')
        if not (early and reviewer):i['events'][2]['role_ids'].append('v')
        i['plan'].update(depth='quick' if reviewer else 'normal',reviewer_required=True)
        r['invariant_probe'].update(state='performed',reviewer_provenance='receipt-v')
        x=event(0,'disclose',['v'] if reviewer else ['a','b'],'new','probe_challenge' if reviewer else 'rebuttal')
        i['events'].insert(2 if early and not reviewer else 3,x)
        i['events'].insert(-1,event(0,'stage_complete',['v'] if reviewer else ['a','b'],stage='probe_challenge' if reviewer else 'rebuttal'))
        self.renumber(r)
    def renumber(self,r):
        i=r['isolation']
        for n,e in enumerate(i['events'],1):e['seq']=n
        if i['verdict_lock'] is not None:i['verdict_lock']['seq']=next(e['seq'] for e in i['events'] if e['type']=='verdict_lock')
    def test_staged_rebuttal(self):
        r=isolated();self.add_current(r);self.assertEqual(validator.validate(r), [])
    def test_early_rebuttal(self):self.invalid(lambda r:self.add_current(r,True))
    def test_staged_review(self):
        r=isolated();self.add_current(r,reviewer=True);self.assertEqual(validator.validate(r), [])
    def test_anchored_review(self):self.invalid(lambda r:self.add_current(r,True,True))
    def test_round_not_all_advocates_ready(self):
        def change(r):self.add_current(r);r['isolation']['events'][2]['role_ids']=['a']
        self.invalid(change)
    def test_unequal_rebuttal_packets(self):
        def change(r):
            self.add_current(r);i=r['isolation'];i['packets'].append(dict(i['packets'][1],id='other-current'));i['events'][3]['role_ids']=['a'];i['events'].insert(4,event(0,'disclose',['b'],'other-current','rebuttal'))
            for n,e in enumerate(i['events'],1):e['seq']=n
            i['verdict_lock']['seq']=len(i['events'])
        self.invalid(change)
    def test_round_must_finish_before_lock(self):
        def change(r):self.add_current(r);r['isolation']['events'][-2]['stage']='unrelated'
        self.invalid(change)
    def test_review_challenge_must_finish(self):
        def change(r):self.add_current(r,reviewer=True);r['isolation']['events'][-2]['stage']='unrelated'
        self.invalid(change)
    def test_normal_cannot_skip_review(self):self.invalid(lambda r:r['isolation']['plan'].update(depth='normal'))
    def test_required_review_cannot_be_skipped(self):self.invalid(lambda r:r['isolation']['plan'].update(reviewer_required=True))
    def test_normal_cannot_skip_rebuttal(self):
        def change(r):
            self.add_current(r,reviewer=True);r['invariant_probe'].update(state='performed',reviewer_provenance='receipt-v');r['isolation']['plan'].update(depth='normal',reviewer_required=True)
        self.invalid(change)
    def test_verified_reads_after_lock_rejected(self):
        def change(r):
            i=r['isolation'];i.update(status='verified',claim='controlled_comparison');i['controls'].update(access_boundary='verified',read_audit='complete',evidence=['receipt']);i['events'].append(i['events'].pop(1));self.renumber(r)
        self.invalid(change)
    def test_verified_reads_after_output_before_lock_rejected(self):
        def change(r):
            i=r['isolation'];i.update(status='verified',claim='controlled_comparison');i['controls'].update(access_boundary='verified',read_audit='complete',evidence=['receipt']);i['events'][1],i['events'][2]=i['events'][2],i['events'][1];self.renumber(r)
        self.invalid(change)
    def test_round_output_before_disclosure_rejected(self):
        def change(r):
            self.add_current(r);i=r['isolation'];i['events'][3],i['events'][4]=i['events'][4],i['events'][3];self.renumber(r)
        self.invalid(change)
    def test_unequal_extra_original_exposure_rejected(self):
        def change(r):
            i=r['isolation'];i['packets'].append(dict(i['packets'][0],id='different',digest='f'*64));i['events'].insert(2,event(0,'disclose',['a'],'different','initial'));self.renumber(r)
        self.invalid(change)
    def test_extra_original_other_stage_cannot_bypass_equality(self):
        def change(r):
            i=r['isolation'];i['packets'].append(dict(i['packets'][0],id='different',digest='f'*64));i['events'].insert(2,event(0,'read',['a'],'different','source_check'));self.renumber(r)
        self.invalid(change)
    def test_new_packet_invalidates_round_completion(self):
        def change(r):
            self.add_current(r);i=r['isolation'];i['packets'].append(dict(i['packets'][1],id='late',digest='f'*64));i['events'].insert(-1,event(0,'disclose',['a','b'],'late','rebuttal'));self.renumber(r)
        self.invalid(change)
    def test_new_packet_with_renewed_outputs_is_valid(self):
        r=isolated();self.add_current(r);i=r['isolation'];i['packets'].append(dict(i['packets'][1],id='late',digest='f'*64));i['events'].insert(-1,event(0,'disclose',['a','b'],'late','rebuttal'));i['events'].insert(-1,event(0,'stage_complete',['a','b'],stage='rebuttal'));self.renumber(r)
        self.assertEqual(validator.validate(r),[])
    def test_repeat_same_packet_read_does_not_invalidate_output(self):
        r=isolated();self.add_current(r);r['isolation']['events'].insert(-1,event(0,'read',['a','b'],'new','rebuttal'));self.renumber(r)
        self.assertEqual(validator.validate(r),[])
    def test_new_original_invalidates_independent_outputs(self):
        def change(r):
            i=r['isolation'];i['packets'].append(dict(i['packets'][0],id='late-original',digest='f'*64));i['events'].insert(-1,event(0,'disclose',['c','a','b'],'late-original','source_check'));self.renumber(r)
        self.invalid(change)
    def test_new_original_with_renewed_outputs_is_valid(self):
        r=isolated();i=r['isolation'];i['packets'].append(dict(i['packets'][0],id='late-original',digest='f'*64));i['events'].insert(-1,event(0,'disclose',['c','a','b'],'late-original','source_check'));i['events'].insert(-1,event(0,'stage_complete',['a','b']));self.renumber(r)
        self.assertEqual(validator.validate(r),[])
    def test_quick_cannot_add_rebuttal(self):
        def change(r):self.add_current(r);r['isolation']['plan']['depth']='quick'
        self.invalid(change)
    def add_final(self,r):
        self.add_current(r);i=r['isolation'];i['packets'].append(dict(i['packets'][1],id='final',digest='f'*64));i['events'].insert(-1,event(0,'disclose',['a','b'],'final','final_round'));i['events'].insert(-1,event(0,'stage_complete',['a','b'],stage='final_round'));self.renumber(r)
    def test_normal_cannot_add_final_round(self):self.invalid(self.add_final)
    def test_deep_one_final_round_valid(self):
        r=isolated();self.add_final(r);r['isolation']['plan']['depth']='deep';self.assertEqual(validator.validate(r),[])
    def test_deep_second_final_packet_cycle_rejected(self):
        def change(r):
            self.add_final(r);i=r['isolation'];i['plan']['depth']='deep';i['packets'].append(dict(i['packets'][-1],id='final-again',digest='1'*64));i['events'].insert(-1,event(0,'disclose',['a','b'],'final-again','final_round'));i['events'].insert(-1,event(0,'stage_complete',['a','b'],stage='final_round'));self.renumber(r)
        self.invalid(change)
    def test_review_challenge_waits_for_all_advocate_statements(self):
        def change(r):
            self.add_current(r,reviewer=True);i=r['isolation'];i['events'][2]['role_ids']=['a','v'];i['events'].insert(-1,event(0,'stage_complete',['b']));self.renumber(r)
        self.invalid(change)
    def test_deep_final_round_after_lock_rejected(self):
        def change(r):
            self.add_current(r);i=r['isolation'];i['plan']['depth']='deep';i['events'].append(event(0,'disclose',['a','b'],'new','final_round'));self.renumber(r)
        self.invalid(change)
    def test_reviewer_challenge_after_lock_rejected(self):
        def change(r):
            self.add_current(r,reviewer=True);i=r['isolation'];i['events'].append(event(0,'disclose',['v'],'new','probe_challenge'));self.renumber(r)
        self.invalid(change)
    def test_post_lock_appendix_current_material_allowed(self):
        r=isolated();self.add_current(r);r['isolation']['events'].append(event(0,'disclose',['a','b','v'],'new','post_lock'));self.renumber(r)
        self.assertEqual(validator.validate(r),[])
    def test_generation_only_partial_is_valid(self):
        r=isolated();r.update(state='partial',reason='Only one candidate generated; comparison never dispatched.');i=r['isolation'];i['roles']=[dict(id='g',agent_id='fresh-g',role='generator',fork_turns='none',fresh=True,history_state='none',dispatch_evidence='receipt-g')];i['events']=[event(1,'dispatch',['g'],'p','initial'),event(2,'stage_complete',['g'])];i['verdict_lock']=None
        self.assertEqual(validator.validate(r),[])
    def test_nested_shapes_never_crash(self):
        r=isolated()
        for key in r['isolation']:
            for malformed in (None,{},[],True,0,''):
                with self.subTest(key=key,value=malformed):
                    bad=copy.deepcopy(r);bad['isolation'][key]=malformed;validator.validate(bad)
    def test_omitted_source_in_initial_packet(self):self.invalid(lambda r:r['isolation']['packets'][0].update(source_snapshot_ids=['s1']))
    def test_read_before_dispatch(self):
        def change(r):
            i=r['isolation'];i['events'][0],i['events'][1]=i['events'][1],i['events'][0];i['events'][0]['seq']=1;i['events'][1]['seq']=2
        self.invalid(change)
    def test_verified_needs_role_read_receipts(self):
        def change(r):
            i=r['isolation'];i.update(status='verified',claim='controlled_comparison');i['controls'].update(access_boundary='verified',read_audit='complete',evidence=['receipt']);i['events'][1]['role_ids']=['a','b']
        self.invalid(change)
    def test_result_contract_and_docs_match_new_version(self):
        root=SCRIPT.parents[1]
        content=(root/'assets/debate-result.md').read_text()
        self.assertIn('Return `dot-adversarial-result/1.1`',content)
        self.assertIn('exact string `dot-adversarial-result/1.1`',content)
        self.assertIn('Version **1.1.0**',(root/'SKILL.md').read_text())
    def test_cli_new_contract(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'record.json';path.write_text(json.dumps(isolated()))
            p=subprocess.run([sys.executable,'-B',str(SCRIPT),str(path)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout)


if __name__=='__main__':unittest.main()
