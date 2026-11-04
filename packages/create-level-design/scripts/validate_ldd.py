#!/usr/bin/env python3
"""Check Markdown LDD structure, not gameplay quality or runtime readiness."""
import argparse, json, re
from pathlib import Path
HEADINGS = ['Level design brief', 'Learning and mechanic boundaries', 'Spatial layout and circulation', 'Encounter flow and pacing', 'Interaction and sensory direction', 'Prototype scope and tuning', 'Validation and review handoff']
def outside_fences(text):
    lines=[]; fence=None
    for line in text.splitlines():
        match=re.match(r'^ {0,3}(`{3,}|~{3,})',line)
        if match:
            marker=match.group(1)
            if fence is None: fence=(marker[0],len(marker))
            elif marker[0]==fence[0] and len(marker)>=fence[1] and re.fullmatch(r' {0,3}'+re.escape(marker)+r'[ \t]*',line): fence=None
            continue
        if fence is None: lines.append(line)
    return '\n'.join(lines)
def validate(text):
    text=outside_fences(text)
    errors=[]
    found=re.findall(r'^## ([1-7])\. (.+?)\s*$',text,re.M)
    expected=[(str(i+1),s) for i,s in enumerate(HEADINGS)]
    if found != expected: errors.append('Required seven numbered headings must occur exactly once in order.')
    for i,label in enumerate(HEADINGS):
        token=f'## {i+1}. {label}'
        if token in text:
            body=text.split(token,1)[1].split('\n## ',1)[0].strip()
            if not body: errors.append(f'Empty section: {label}')
    for field in ['level_id','document_version','template_version','lifecycle_state','source_manifest']:
        if not re.search(r'(?mi)^'+field+r'[ \t]*:[ \t]*[^\s]' ,text): errors.append(f'Missing metadata: {field}')
    state=re.search(r'(?mi)^lifecycle_state[ \t]*:[ \t]*([^\n]+)',text)
    if state:
        value=state.group(1).strip()
        required={'draft':[], 'static_validated':['static_validation_evidence'], 'independently_reviewed':['independent_review_evidence'], 'human_accepted':['human_acceptance_evidence'], 'blockout_validated':['blockout_test_evidence'], 'implementation_ready':['human_acceptance_evidence','blockout_test_evidence','discipline_readiness_evidence']}
        if value not in required: errors.append('Unknown lifecycle_state.')
        else:
            for key in required[value]:
                evidence=re.search(r'(?mi)^'+key+r'[ \t]*:[ \t]*([^\n]+)',text)
                if not evidence or evidence.group(1).strip().lower() in ('','unknown','pending','none','not_run','n/a'):
                    errors.append(f'Missing declared promotion evidence: {key}')
    if re.search(r'\{\{[^}]+\}\}|\bTODO\b',text): errors.append('Unexplained template placeholder remains.')
    return {'state':'fail' if errors else 'pass','errors':errors,'scope':'structure_only','not_verified':['source truth','semantic coverage','diagram consistency','visual rendering','playability','human approval','authenticity of declared promotion evidence']}
def main():
    p=argparse.ArgumentParser(); p.add_argument('document'); args=p.parse_args()
    result=validate(Path(args.document).read_text()); print(json.dumps(result,indent=2)); return bool(result['errors'])
if __name__=='__main__': raise SystemExit(main())
