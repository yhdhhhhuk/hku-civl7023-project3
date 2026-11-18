from pathlib import Path
import subprocess,re,json,zipfile
r=Path(__file__).resolve().parents[1];rx=re.compile('[\u3400-\u9fff]')
paths=subprocess.check_output(['git','ls-files','-z'],cwd=r).decode().split('\0');rows=[]
for name in paths:
 if not name:continue
 # Include all C-owned handoffs, runtime code, results, templates and copied C material.
 owned= any(t in name for t in ['AC回传/C/','AC回传模板/C/','C_仿真与装配/','runs/C_stage','/证据/C/']) or Path(name).name.startswith(('C_','C第','audit_c_'))
 if not owned:continue
 p=r/name; text='';kind='binary'
 if not p.exists():kind='not_checked_out'
 elif p.suffix.lower() in ['.pptx','.docx']:
  with zipfile.ZipFile(p) as z:text='\n'.join(z.read(n).decode('utf8',errors='replace') for n in z.namelist() if n.endswith('.xml'))
  kind='office_xml'
 elif p.suffix.lower() in ['.md','.txt','.csv','.json','.py','.cmd','.log']:
  text=p.read_text(encoding='utf-8-sig',errors='replace');kind='text'
 rows.append(dict(path=name,chinese_path=bool(rx.search(name)),chinese_content=len(rx.findall(text)),kind=kind,archive=any(t in name for t in ['runs/','/证据/','frozen_source','运行验证','提交/simulation/'])))
(r/'C_stage4/language_audit.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
print('C-scoped files:',len(rows),'Chinese paths:',sum(x['chinese_path'] for x in rows),'Chinese text/Office:',sum(x['chinese_content']>0 for x in rows))
for x in rows:
 if x['chinese_content'] and not x['archive'] and x['kind']=='text':print(x['path'],x['chinese_content'])
