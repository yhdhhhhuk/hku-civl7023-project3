"""Describe exactly the stage3 download, including lossless/log-only exclusions."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT/'05_Project3_月面机器人装配';OUT=PROJECT/'运行验证/B_第三阶段_2026-11-10'
def digest(f):
 h=hashlib.sha256()
 with f.open('rb') as src:
  for b in iter(lambda:src.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 compression=[x for x in json.loads((ROOT/'evidence_compression.json').read_text()) if x['path'].startswith(OUT.relative_to(ROOT).as_posix()+'/')]
 raw={x['path'] for x in compression};files={};local=[]
 dirs=[PROJECT/'B_第三阶段正式评价',PROJECT/'B_第三阶段报告',OUT,PROJECT/'运行验证/B_第三阶段复核_2026-11-10']
 for folder in dirs:
  for f in sorted(folder.rglob('*')):
   if not f.is_file() or '__pycache__' in f.parts or f.name=='.DS_Store' or f.name in ['publication_manifest.json','publication_check.json']:continue
   rel=f.relative_to(ROOT).as_posix()
   if rel in raw:continue
   if f.name in ['checkpoint.json','checkpoint.bullet','derived_signals.npz']:
    local.append(dict(path=rel,bytes=f.stat().st_size,sha256=digest(f),reason='Local recovery checkpoint or reproducible derived cache; not needed for published analysis'))
   else:files[rel]=dict(bytes=f.stat().st_size,sha256=digest(f))
 for name in ['第三阶段入口.py','第三阶段_B执行与验收计划.md','restore_evidence.py','evidence_compression.json','scripts/prepare_stage3_logs.py','scripts/build_stage3_manifest.py','scripts/verify_stage3_package.py']:
  f=ROOT/name;files[name]=dict(bytes=f.stat().st_size,sha256=digest(f))
 result=dict(schema_version=1,path_base='repository root',description='Published stage3 evidence; original raw CSV bytes restored from gzip. Local archive SHA also covers excluded recovery/cache files; use this manifest to verify a download.',files=files,compressed_evidence=compression,local_only=local,expected_conditions={'compensation_off':{'success':True,'rows':145676},'compensation_on':{'success':True,'rows':145712}})
 (OUT/'publication_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('Published stage3 files:',len(files),'compressed raw logs:',len(compression),'local-only caches:',len(local))
if __name__=='__main__':main()
