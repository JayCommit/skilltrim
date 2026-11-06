from pathlib import Path
import subprocess,json,hashlib,sys
# Anchor to this repository. A cwd-relative src/ or .test-output/ missed clones when launched elsewhere.
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from skilltrim.core import parse_skill,optimize,TokenCounter,SkillError
result=[]
for collection in ['anthropic','openai']:
 root=ROOT/'.test-output'/collection
 revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
 rows=[]
 for p in sorted(root.rglob('SKILL.md')):
  text=p.read_text(encoding='utf-8')
  # Hash analyzed UTF-8 after universal newline normalization so LF git blobs match a CRLF checkout.
  row={'path':p.relative_to(root).as_posix(),'sha256':hashlib.sha256(text.encode('utf-8')).hexdigest()}
  try:
   skill=parse_skill(text,p.parent.name)
   safe,report=optimize(skill,TokenCounter())
   candidate,experimental=optimize(skill,TokenCounter(),experimental_cuts=True)
   assert safe==text
   row.update(before_tokens=report['before_tokens'],default_after_tokens=report['after_tokens'],experimental_after_tokens=experimental['after_tokens'],review_items=len(report['findings']))
   example=ROOT/'benchmarks'/'real-example.json'
   if experimental['saved_tokens'] and not example.exists():
    import difflib
    example.write_text(json.dumps(dict(collection=collection,revision=revision,**row,diff=''.join(difflib.unified_diff(text.splitlines(True),candidate.splitlines(True)))),indent=2))
  except SkillError as e: row['error']=str(e)
  rows.append(row)
 result.append(dict(collection=collection,revision=revision,skills=rows))
(ROOT/'benchmarks'/'real-results.json').write_text(json.dumps(result,indent=2))
for c in result: print(c['collection'],len(c['skills']),'files',sum('error' in r for r in c['skills']),'rejected')