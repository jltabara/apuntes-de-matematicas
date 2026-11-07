#!/usr/bin/env python3
"""Compila las descargas UTF-8 sin PDF; publica solo compilaciones exitosas."""
from pathlib import Path
import argparse,concurrent.futures,json,os,subprocess,tempfile,zipfile,shutil,re
ROOT=Path(__file__).resolve().parents[2]
DOCS=ROOT/'web/docs'; REPORT=ROOT/'web/compilacion'; REPORT.mkdir(exist_ok=True)
data=json.loads((DOCS/'catalogo.js').read_text().removeprefix('window.CATALOGO = ').strip().removesuffix(';'))
parser=argparse.ArgumentParser();parser.add_argument('--bar-style',type=Path);args=parser.parse_args()
targets=[x for x in data if not x['pdf']]
previous=json.loads((REPORT/'resultados.json').read_text()) if (REPORT/'resultados.json').exists() else []
BUILD=Path(tempfile.mkdtemp(prefix='libros-latex-'))
def compile_one(x):
 work=BUILD/x['id'];work.mkdir()
 with zipfile.ZipFile(DOCS/x['source']) as z:z.extractall(work)
 main=work/x['original']; source=main.read_text()
 if args.bar_style and r'\usepackage{bar}' in source:shutil.copyfile(args.bar_style,main.parent/'bar.sty')
 # Stable ASCII job name avoids shell quoting bugs in legacy TeX tools.
 (main.parent/'main.tex').write_text(source)
 env={**os.environ,'PATH':'/Library/TeX/texbin:'+os.environ['PATH'],'TEXINPUTS':str(work)+'//:','BIBINPUTS':str(work)+'//:'}
 cmd=['/Library/TeX/texbin/latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','-file-line-error','-pdflatex=pdflatex -no-shell-escape %O %S','main.tex']
 try:
  r=subprocess.run(cmd,cwd=main.parent,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=150)
  output=r.stdout.decode('utf-8','replace');ok=r.returncode==0 and (main.parent/'main.pdf').exists()
 except subprocess.TimeoutExpired as e:output=(e.stdout or b'').decode('utf-8','replace')+'\nTIMEOUT';ok=False
 (REPORT/(x['id']+'.log')).write_text(output)
 if ok:shutil.copyfile(main.parent/'main.pdf',(ROOT/x['original']).with_suffix('.pdf'))
 result=dict(id=x['id'],archivo=x['original'],ok=ok,build=str(main.parent),errores=[l for l in output.splitlines() if 'Error' in l or l.startswith('!') or 'not found' in l or 'Undefined control' in l][-8:])
 print(json.dumps(result,ensure_ascii=False),flush=True)
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(compile_one,targets))
merged={x['id']:x for x in previous};merged.update({x['id']:x for x in results})
(REPORT/'resultados.json').write_text(json.dumps(list(merged.values()),ensure_ascii=False,indent=2))
print('RESULTADO',sum(x['ok'] for x in results),'/',len(results),'directorio',BUILD,flush=True)
