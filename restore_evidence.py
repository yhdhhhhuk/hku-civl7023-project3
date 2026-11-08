"""Restore archived raw telemetry and verify its original SHA256."""
from pathlib import Path
import gzip,hashlib,json,shutil
root=Path(__file__).resolve().parent
for info in json.loads((root/'evidence_compression.json').read_text(encoding='utf8')):
 target=root/info['path']
 if target.exists():
  assert hashlib.sha256(target.read_bytes()).hexdigest()==info['sha256'];continue
 with gzip.open(root/info['compressed_path'],'rb') as source,target.open('wb') as output:shutil.copyfileobj(source,output)
 assert target.stat().st_size==info['bytes'] and hashlib.sha256(target.read_bytes()).hexdigest()==info['sha256']
 print('Restored:',info['path'])
