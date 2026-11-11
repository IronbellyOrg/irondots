#!/usr/bin/env python3
"""Fail-closed declaration checks; not proof of semantic truth or send authority."""
import argparse,hashlib,json,re,sys
from pathlib import Path
HARD=['identity','channel','authorization','meaning','privacy','exact_strings','current_context']
STYLE=['opening_closing','directness','request_framing','rhythm','length','structure','vocabulary_contractions','warmth_humor','punctuation','recipient_context_fit']
def validate_profile(profile,version):
    if not isinstance(profile,dict) or profile.get('schema')!='personal-writing-profile/1.0' or profile.get('version')!=version: raise ValueError('invalid profile schema/version')
    for key in ['owner','status','generated_at','source_date_range','retrieved_at','privacy','retention']:
        if not isinstance(profile.get(key),str) or not profile[key].strip(): raise ValueError('invalid profile field: '+key)
    if type(profile.get('human_style_validated')) is not bool: raise ValueError('invalid profile validation flag')
    for key in ['precedence','gaps','excluded','refresh_triggers']:
        if not isinstance(profile.get(key),list) or not profile[key] or any(not isinstance(v,str) or not v.strip() for v in profile[key]): raise ValueError('invalid profile list: '+key)
    for key in ['core','observations']:
        if not isinstance(profile.get(key),list) or not profile[key]: raise ValueError('invalid profile rules: '+key)
        for rule in profile[key]:
            if not isinstance(rule,dict) or any(not isinstance(rule.get(k),str) or not rule[k].strip() for k in ['id','status','rule','scope']): raise ValueError('invalid scoped rule')
    if not isinstance(profile.get('channels'),dict) or not profile['channels']: raise ValueError('invalid profile channels')
    for channel,record in profile['channels'].items():
        if not isinstance(record,dict) or any(not isinstance(record.get(k),str) or not record[k].strip() for k in ['status','guidance']): raise ValueError('invalid channel guidance')
    if not isinstance(profile.get('recipient_overrides'),list) or not isinstance(profile.get('purpose_overlays'),dict): raise ValueError('invalid profile overlays')
def assess(r,draft,root=None,input_bytes=None):
    h=hashlib.sha256(draft).hexdigest(); errors=[]; input_verified=False
    try: draft.decode('utf-8')
    except UnicodeDecodeError: errors.append('draft must be UTF-8')
    def fail(m): errors.append(m)
    def result(): return {'input_binding_verified':input_verified,'draft_sha256':h,'declared_send_gates_pass':not errors,'errors':errors,'notice':'Declaration checks only; independent source evidence and channel authorization required. No send performed.'}
    if not isinstance(r,dict): fail('receipt must be object'); return result()
    required=['input_sha256','loaded_rule_ids','schema','profile_version','profile_read_verified','profile_sha256','draft_sha256','channel','recipient_verified','scope','read_evidence','hard_gates','style_dimensions','material_style_mismatch','style_exception','mode','send_eligible','limitations']
    for key in required:
        if key not in r: fail('missing field: '+key)
    if r.get('schema')!='personal-writing-receipt/1.0': fail('wrong schema')
    if not isinstance(r.get('input_sha256'),str) or not re.fullmatch(r'[0-9a-f]{64}',r['input_sha256']): fail('input identity missing/invalid')
    if input_bytes is not None:
        input_verified=hashlib.sha256(input_bytes).hexdigest()==r.get('input_sha256')
        if not input_verified: fail('input digest mismatch')
    if not isinstance(r.get('loaded_rule_ids'),list) or any(not isinstance(v,str) or not v.strip() for v in r.get('loaded_rule_ids',[])): fail('loaded rule identifiers invalid')
    if r.get('draft_sha256')!=h: fail('draft digest mismatch')
    for key in ['profile_read_verified','recipient_verified','material_style_mismatch','send_eligible']:
        if type(r.get(key)) is not bool: fail('boolean required: '+key)
    if r.get('send_eligible') is not True: fail('declared send_eligible is not true')
    if r.get('recipient_verified') is not True: fail('recipient not verified')
    if r.get('channel') not in ['email','slack-dm','slack-channel','clickup-dm','clickup-channel','text','document']: fail('unsupported or missing channel')
    scope=r.get('scope',{})
    if not isinstance(scope,dict): scope={};fail('scope must be object')
    for key in ['purpose','account','recipient','thread']:
        if not isinstance(scope.get(key),str) or not scope[key].strip(): fail('scope string missing: '+key)
    # thread may explicitly be not-applicable for a new message/document.
    if not isinstance(r.get('limitations'),list) or any(not isinstance(v,str) or not v.strip() for v in r.get('limitations',[])): fail('limitations must be nonempty strings in a list')
    hard=r.get('hard_gates',{})
    if not isinstance(hard,dict): hard={};fail('hard_gates must be object')
    for k in HARD:
        if hard.get(k)!='pass': fail('hard gate: '+k)
    reads=r.get('read_evidence')
    if not isinstance(reads,list) or any(not isinstance(v,str) or not v.strip() for v in reads): fail('read_evidence must be string list')
    ex=r.get('style_exception',{})
    if not isinstance(ex,dict): ex={};fail('style_exception must be object')
    for k in ['explicit','limitation_disclosed']:
        if type(ex.get(k)) is not bool: fail('exception boolean required: '+k)
    waived=ex.get('explicit') is True and ex.get('limitation_disclosed') is True and ex.get('draft_sha256')==h and isinstance(ex.get('evidence'),str) and bool(ex['evidence'].strip()) and isinstance(ex.get('limitation'),str) and bool(ex['limitation'].strip())
    dims=r.get('style_dimensions',{})
    if not isinstance(dims,dict): dims={};fail('style_dimensions must be object')
    mismatch=False
    for k in STYLE:
        v=dims.get(k)
        if not isinstance(v,dict) or v.get('status') not in ['matches','acceptable-with-limitation','mismatch'] or not isinstance(v.get('reason',v.get('evidence')),str) or not v.get('reason',v.get('evidence','')).strip(): fail('style dimension incomplete: '+k)
        elif v['status']=='mismatch': mismatch=True
        elif v['status']=='acceptable-with-limitation' and not r.get('limitations'): fail('limited dimension needs recorded limitation: '+k)
    if (mismatch or r.get('material_style_mismatch') is True) and not waived: fail('unresolved style mismatch')
    if r.get('profile_read_verified') is not True:
        if not waived: fail('profile unavailable without exact informed exception')
    else:
        reads=r.get('read_evidence')
        if not isinstance(reads,list) or not reads or any(not isinstance(v,str) or not v.strip() for v in reads): fail('profile read evidence must be nonempty strings')
        root=Path(root) if root else Path(__file__).resolve().parents[1]
        try:
            manifest=strict_load((root/'assets/profile-manifest.json').read_text())
            if not isinstance(manifest,dict) or manifest.get('schema')!='personal-writing-manifest/1.0' or not isinstance(manifest.get('active_version'),str) or not re.fullmatch(r'\d+\.\d+\.\d+',manifest['active_version']): raise ValueError('invalid manifest schema/version')
            active=manifest['active_version']
            active_file=root/'assets'/('profile-v'+active+'.json')
            active_raw=active_file.read_bytes();active_profile=strict_load(active_raw)
            validate_profile(active_profile,active)
            if manifest.get('resource')!=active_file.name or manifest.get('sha256')!=hashlib.sha256(active_raw).hexdigest(): raise ValueError('active manifest target invalid')
            version=r.get('profile_version')
            # Retain exact older version only if artifact is present and independently validated.
            if not isinstance(version,str) or not re.fullmatch(r'\d+\.\d+\.\d+',version): raise ValueError('invalid version')
            f=root/'assets'/('profile-v'+version+'.json');raw=f.read_bytes();profile=strict_load(raw)
            validate_profile(profile,version)
            known={rule['id'] for rule in profile['core']+profile['observations']}
            if not r.get('loaded_rule_ids') or any(k not in known for k in r['loaded_rule_ids']): raise ValueError('loaded rules missing or unknown')
            digest=hashlib.sha256(raw).hexdigest()
            if digest!=r.get('profile_sha256') or profile.get('version')!=version: raise ValueError('profile digest/version mismatch')
            if version==manifest.get('active_version'):
                if manifest.get('resource')!=f.name or manifest.get('sha256')!=digest: raise ValueError('manifest/profile mismatch')
            else:
                basis=r.get('prior_validated_basis')
                if not isinstance(basis,dict) or basis.get('draft_sha256')!=h or basis.get('profile_sha256')!=digest or basis.get('profile_version')!=version or basis.get('latest_context_reviewed') is not True or not isinstance(basis.get('receipt_id'),str) or not basis['receipt_id'].strip(): raise ValueError('older version needs exact prior validated basis')
        except (OSError,ValueError,TypeError,KeyError) as e: fail('profile validation: '+str(e))
    if r.get('mode')!='send-authorized': fail('not a send-authorized route')
    return result()
def unique_pairs(pairs):
    out={}
    for key,value in pairs:
        if key in out: raise ValueError("duplicate JSON key: "+key)
        out[key]=value
    return out
def strict_load(raw):
    return json.loads(raw,object_pairs_hook=unique_pairs,parse_constant=lambda s: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
def main():
    a=argparse.ArgumentParser();a.add_argument('receipt');a.add_argument('draft');a.add_argument('--input',dest='input_file');x=a.parse_args()
    try:
        r=strict_load(Path(x.receipt).read_text())
        result=assess(r,Path(x.draft).read_bytes(),input_bytes=Path(x.input_file).read_bytes() if x.input_file else None)
    except (OSError,ValueError,TypeError) as e: result={'declared_send_gates_pass':False,'errors':['input error: '+str(e)],'notice':'No send performed.'}
    print(json.dumps(result,indent=2))
    sys.exit(0 if result["declared_send_gates_pass"] else 1)
if __name__=='__main__': main()
