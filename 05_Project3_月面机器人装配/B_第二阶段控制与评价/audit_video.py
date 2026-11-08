"""Check rendered video frame count and save the actual last frame."""
from pathlib import Path
import json,sys
import imageio.v2 as imageio
from PIL import Image
out=Path(__file__).resolve().parents[1]/'运行验证/B_第二阶段_2026-11-04'/sys.argv[1]
r=json.loads((out/'result.json').read_text());reader=imageio.get_reader(out/'assembly.mp4');meta=reader.get_meta_data();count=reader.count_frames()
expected=round(r['simulated_seconds']*240)//48+1
assert count==expected and meta['fps']==5 and tuple(meta['size'])==(640,480)
last=reader.get_data(count-1);Image.fromarray(last).save(out/'last_frame.png');reader.close()
(out/'视频核对.json').write_text(json.dumps(dict(frames=count,expected_frames=expected,fps=5,resolution=[640,480],video_duration_seconds=meta['duration'],simulation_seconds=r['simulated_seconds'],note='One extra initial frame at step24, subsequent frames every48 external steps; actual physics render, no interpolation or checkpoint concatenation.'),ensure_ascii=False,indent=2),encoding='utf8')
print('Video verified',count)
