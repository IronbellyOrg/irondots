"""Check that intentionally removed model gates cause failures, in disposable copies."""
import pathlib, tempfile, subprocess, json, datetime, shutil
root=pathlib.Path(__file__).resolve().parent
source=(root/'policy_model.py').read_text()
mutations={
 'pool_grant_removed': ("if not pool or team not in pool['grants']:","if not pool:"),
 'source_acl_removed': ("if user not in doc.readers or team not in doc.permitted_teams:","if team not in doc.permitted_teams:"),
 'inner_team_policy_removed': ("if user not in doc.readers or team not in doc.permitted_teams:","if user not in doc.readers:"),
 'review_gate_removed': ("if doc is None or not doc.reviewed:","if doc is None:"),
 'archive_gate_removed': ("for path in doc.containers:","for path in ():"),
 'discovery_grant_removed': ("if team in v['grants'])","if True)"),
}
results=[]
for name,(old,new) in mutations.items():
    assert source.count(old)==1,(name,source.count(old))
    with tempfile.TemporaryDirectory(prefix='synthetic-policy-mutation-') as temp:
        path=pathlib.Path(temp)
        (path/'policy_model.py').write_text(source.replace(old,new))
        shutil.copyfile(root/'test_policy_model.py',path/'test_policy_model.py')
        run=subprocess.run(['python3','-m','unittest','-v'],cwd=path,capture_output=True,text=True)
        # Failures must be assertion failures; a syntax/import crash is not a detected security mutant.
        detected=run.returncode!=0 and 'FAIL:' in run.stderr and 'SyntaxError' not in run.stderr and 'ImportError' not in run.stderr
        results.append({'mutation':name,'detected':detected,'exit_code':run.returncode,'output':run.stdout+run.stderr})
now=datetime.datetime.now(datetime.timezone.utc)
payload={'generated_at':now.isoformat(),'kind':'synthetic missing-gate sensitivity checks','results':results,'all_detected':all(x['detected'] for x in results)}
out=root/'runs';out.mkdir(exist_ok=True)
(out/(now.strftime('%Y%m%dT%H%M%S%fZ')+'-mutations.json')).write_text(json.dumps(payload,indent=2))
print(json.dumps({k:v for k,v in payload.items() if k!='results'},indent=2))
print([(r['mutation'],r['detected']) for r in results])
raise SystemExit(0 if payload['all_detected'] else 1)
