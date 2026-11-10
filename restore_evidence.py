"""Restore selected lossless raw logs, checking original bytes and SHA256."""
from pathlib import Path
import argparse,gzip,hashlib,json,shutil
ROOT=Path(__file__).resolve().parent

def digest_stream(stream):
 h=hashlib.sha256();size=0
 for block in iter(lambda:stream.read(1024*1024),b''):h.update(block);size+=len(block)
 return h.hexdigest(),size

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--prefix',default='',help='Only paths beginning with this repository-relative prefix');ap.add_argument('--verify-only',action='store_true',help='Verify compressed contents without restoring CSVs');args=ap.parse_args();count=0
 for info in json.loads((ROOT/'evidence_compression.json').read_text(encoding='utf8')):
  if not info['path'].startswith(args.prefix.replace('\\','/')):continue
  target=ROOT/info['path'];compressed=ROOT/info['compressed_path']
  if target.exists():
   with target.open('rb') as source:h,size=digest_stream(source)
   if h!=info['sha256'] or size!=info['bytes']:raise ValueError('Existing raw file differs; refusing to overwrite '+info['path'])
  elif args.verify_only:
   with gzip.open(compressed,'rb') as source:h,size=digest_stream(source)
   if h!=info['sha256'] or size!=info['bytes']:raise ValueError('Compressed evidence differs '+info['compressed_path'])
  else:
   target.parent.mkdir(parents=True,exist_ok=True)
   with gzip.open(compressed,'rb') as source,target.open('wb') as output:shutil.copyfileobj(source,output)
   with target.open('rb') as source:h,size=digest_stream(source)
   if h!=info['sha256'] or size!=info['bytes']:raise ValueError('Restored evidence differs '+info['path'])
   print('Restored:',info['path'])
  count+=1
 if not count:ap.error('No evidence matches the prefix')
 print('Verified raw byte/SHA records:',count)
 return 0
if __name__=='__main__':raise SystemExit(main())
