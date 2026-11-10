"""Verify the downloaded stage3 files and lossless raw contents using stdlib only."""
from pathlib import Path
import gzip,hashlib,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'05_Project3_月面机器人装配/运行验证/B_第三阶段_2026-11-10'
def hash_stream(stream):
 h=hashlib.sha256();n=0
 for b in iter(lambda:stream.read(1024*1024),b''):h.update(b);n+=len(b)
 return h.hexdigest(),n
def main():
 m=json.loads((OUT/'publication_manifest.json').read_text(encoding='utf8'))
 for name,info in m['files'].items():
  with (ROOT/name).open('rb') as f:h,n=hash_stream(f)
  if (h,n)!=(info['sha256'],info['bytes']):raise ValueError('Published file mismatch: '+name)
 for info in m['compressed_evidence']:
  with gzip.open(ROOT/info['compressed_path'],'rb') as f:h,n=hash_stream(f)
  if (h,n)!=(info['sha256'],info['bytes']):raise ValueError('Lossless raw content mismatch: '+info['path'])
 for name,expected in m['expected_conditions'].items():
  r=json.loads((OUT/name/'result.json').read_text(encoding='utf8'))
  if r['success']!=expected['success'] or r['telemetry_rows']!=expected['rows']:raise ValueError(name+' result mismatch')
 print('Stage3 download verified:',len(m['files']),'files;',len(m['compressed_evidence']),'lossless logs; both16-piece runs successful.')
 return 0
if __name__=='__main__':raise SystemExit(main())
