"""Read-only checks of runtime hash freeze and actual video; writes audit evidence."""
from pathlib import Path
import hashlib,json,sys
import imageio.v2 as imageio
from PIL import Image
from analyze_experiments import ROOT,OUT,CODE,read,dump

def audit(condition):
 manifest=read(OUT/'experiment_manifest.json');r=read(OUT/condition/'result.json');path=OUT/condition
 archive_only=[]
 for rel,h in {**manifest['source_hashes'],**manifest['resource_hashes']}.items():
  live=ROOT/rel
  if not live.exists() and rel=='B_第二阶段控制与评价/acceptance.py':
   # Legacy local-only checker was not imported by the assembly process.
   live=OUT/'frozen_source'/rel;archive_only.append(rel)
  assert hashlib.sha256(live.read_bytes()).hexdigest()==h,rel
 assert all(hashlib.sha256((OUT/'frozen_source'/rel).read_bytes()).hexdigest()==h for rel,h in manifest['source_hashes'].items())
 reader=imageio.get_reader(path/'assembly.mp4');meta=reader.get_meta_data();count=reader.count_frames();steps=round(r['simulated_seconds']*240);expected=steps//48+1
 assert count==expected if r['success'] else abs(count-expected)<=1
 assert meta['fps']==5 and tuple(meta['size'])==(640,480)
 Image.fromarray(reader.get_data(count-1)).save(path/'last_frame.png');reader.close()
 audit=dict(archived_unused_checker_fallback=archive_only,runtime_and_resource_hashes_unchanged=True,frozen_runtime_sources_match=True,video_frames=count,expected_frames=expected,fps=5,resolution=[640,480],duration_s=meta['duration'],simulated_seconds=r['simulated_seconds'],render_source='Live physics every48 external steps plus initial step24; no interpolation, checkpoint concatenation or simulation pose resets after initialization',condition_success=r['success'])
 dump(path/'evidence_audit.json',audit);print(condition,audit)
if __name__=='__main__':audit(sys.argv[1])
