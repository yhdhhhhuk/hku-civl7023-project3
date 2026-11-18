"""Compress stage3 large CSVs without removing or changing the raw evidence."""
from pathlib import Path
import gzip,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'05_Project3_月面机器人装配/运行验证/B_第三阶段_2026-11-10'
manifest_path=ROOT/'evidence_compression.json'
entries=json.loads(manifest_path.read_text(encoding='utf8'))
entries=[x for x in entries if not x['path'].startswith(STAGE.relative_to(ROOT).as_posix()+'/')]
for f in sorted(STAGE.glob('compensation_*/*.csv')):
 if f.stat().st_size<1_000_000:continue
 dest=f.with_suffix(f.suffix+'.gz')
 with f.open('rb') as source,dest.open('wb') as target:
  with gzip.GzipFile(filename='',mode='wb',fileobj=target,compresslevel=9,mtime=0) as compressed:shutil.copyfileobj(source,compressed)
 h=hashlib.sha256(f.read_bytes()).hexdigest();digest=hashlib.sha256();size=0
 with gzip.open(dest,'rb') as compressed:
  for block in iter(lambda:compressed.read(1024*1024),b''):digest.update(block);size+=len(block)
 assert digest.hexdigest()==h and size==f.stat().st_size
 assert dest.stat().st_size<100*1024*1024,'GitHub file limit exceeded'
 entries.append(dict(path=f.relative_to(ROOT).as_posix(),compressed_path=dest.relative_to(ROOT).as_posix(),sha256=h,bytes=size,compressed_bytes=dest.stat().st_size,compressed_sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
 print(f.relative_to(STAGE),size,'->',dest.stat().st_size,flush=True)
manifest_path.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
