"""Check final Markdown links and reported numeric tables against accepted data."""
from pathlib import Path
import csv
import hashlib
import json
import re
from urllib.parse import unquote

OUT = Path(__file__).resolve().parent
PROJECT = OUT.parents[1]
REPORT = PROJECT / 'B_第三阶段报告'
EVIDENCE = PROJECT / '运行验证/B_第三阶段_2026-11-10'
summary = json.loads((PROJECT/'B_第三阶段正式评价/第三阶段结果摘要.json').read_text())
independent = json.loads((OUT/'独立验收结果.json').read_text())
chapter = (REPORT/'B_第三阶段技术章节.md').read_text()

def table(prefix):
    lines = chapter.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(prefix))
    rows = []
    for line in lines[start+2:]:
        if not line.startswith('|'):
            break
        rows.append([x.strip() for x in line.strip('|').split('|')])
    return rows

checks = {}
with (EVIDENCE/'final_component_comparison.csv').open(encoding='utf-8-sig', newline='') as f:
    raw = list(csv.DictReader(f))
rows = table('| 表B3 件号')
assert len(rows) == len(raw) == 16
for cells, entry in zip(rows, raw):
    assert int(cells[0]) == int(entry['item'])
    for value, field in zip(cells[1:], ['off_position_mm', 'on_position_mm', 'off_orientation_deg', 'on_orientation_deg']):
        assert abs(float(value)-float(entry[field])) <= 0.000000501
checks['final_component_values'] = 64

off = summary['conditions']['compensation_off']['torque']
on = summary['conditions']['compensation_on']['torque']
for prefix, fields in [
    ('| 表B9 原始', ['raw_peak_abs_Nm', 'raw_RMS_Nm']),
    ('| 表B10 最后', ['last_substep_equivalent_peak_abs_Nm', 'last_substep_equivalent_RMS_Nm']),
]:
    rows = table(prefix)
    assert len(rows) == 6
    for j, cells in enumerate(rows):
        expected = [off[j][fields[0]], on[j][fields[0]], off[j][fields[1]], on[j][fields[1]]]
        assert cells[0] == f'J{j+1}'
        assert all(abs(float(v)-e) <= 0.000000000501 for v,e in zip(cells[1:],expected))
checks['whole_task_torque_values'] = 48
common = independent['common_completed_items_torque']
rows = table('| 表B12 不含')
assert len(rows) == 6
for j,cells in enumerate(rows):
    a=common['compensation_off']['last_substep_equivalent_RMS_Nm'][j]
    b=common['compensation_on']['last_substep_equivalent_RMS_Nm'][j]
    assert all(abs(float(v)-e) <= 0.000000000501 for v,e in zip(cells[1:],[a,b,b-a]))
checks['matched_phase_torque_values'] = 18

links = []
files = list(REPORT.glob('*.md')) + [OUT/'第三阶段独立验收说明.md']
for path in files:
    text = path.read_text()
    assert not re.search(r'待接入|待填写|尚缺本轮|结果尚未收到', text), path
    for href in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text):
        href=href.strip('<>')
        if href.startswith(('http://', 'https://', '#', 'mailto:')):
            continue
        target=(path.parent/unquote(href.split('#')[0])).resolve()
        assert target.exists(), (path.name, href)
        links.append({'document':str(path.relative_to(PROJECT)), 'href':href})
checks['local_links_valid'] = len(links)
checks['documents_sha256'] = {str(p.relative_to(PROJECT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
checks['passed'] = True
(OUT/'文档终检结果.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(checks,ensure_ascii=False,indent=2))
