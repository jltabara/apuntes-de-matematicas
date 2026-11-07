#!/usr/bin/env python3
"""Genera el catálogo y los paquetes conservando intactos los originales."""
from pathlib import Path
import hashlib, json, os, re, shutil, subprocess, unicodedata, zipfile
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'web/docs'
EXCLUDED_PATH=ROOT/'web/excluidos.json'
EXCLUDED=set(json.loads(EXCLUDED_PATH.read_text())) if EXCLUDED_PATH.exists() else set()
CATEGORIES={'Apuntes de Matematicas':'Apuntes de Matemáticas','Matematicas':'Matemáticas','Ficcion':'Ficción'}
def norm(s): return unicodedata.normalize('NFC',s).casefold()
TEXT_EXTENSIONS={'.tex','.bib','.sty','.cls'}
encoding_report={}
def read(p):
 raw=p.read_bytes()
 try:
  text=raw.decode('utf-8-sig'); encoding='utf-8'
 except UnicodeDecodeError:
  # C1 bytes in these legacy files are Windows punctuation, not Latin-1 text.
  encoding='cp1252' if any(128 <= byte < 160 for byte in raw) else 'latin1'
  text=raw.decode(encoding)
 return text

def utf8_source(p):
 text=read(p).replace('\r\n','\n').replace('\r','\n')
 # Repair two BibTeX syntax/key errors only in the downloadable copy.
 if p.relative_to(ROOT).as_posix().casefold()=='apuntes de matematicas/simplectica.bib':
  text=text.replace('publisher={Internet}\n\tyear={2000}', 'publisher={Internet},\n\tyear={2000}')
  pos=text.find('@book{marint,',text.find('@book{marint,')+1)
  if pos>=0:text=text[:pos]+text[pos:].replace('@book{marint,','@book{marint1998,',1)
 damaged=text.count('\ufffd')
 controls=sorted({ord(c) for c in text if ord(c)<32 and c not in '\n\r\t'})
 text=re.sub(r'(\\(?:usepackage|RequirePackage)\s*\[)[^\]]+(\]\s*\{inputenc\})',lambda m:m[1]+'utf8'+m[2],text)
 text=re.sub(r'\\inputencoding\s*\{[^}]+\}',lambda m:r'\inputencoding{utf8}',text)
 encoding_report[p.relative_to(ROOT).as_posix()]={'caracteres_irrecuperables':damaged,'controles_existentes':controls}
 return text.replace('\r\n','\n').replace('\r','\n').encode('utf-8')
files=[p for folder in [*CATEGORIES,'Imagenes'] for p in (ROOT/folder).rglob('*') if p.is_file()]
index={}
for p in files: index.setdefault(norm(p.name),[]).append(p)
def resolve(name,parent,exts):
 for ext in ['',*exts]:
  n=name+ext
  for base in [parent,ROOT/'Imagenes']:
   q=base/n
   if q.is_file(): return q
  matches=index.get(norm(Path(n).name),[])
  if len(matches)==1:return matches[0]
 return None
def page_count(pdf):
 result=subprocess.run(['pdfinfo',str(pdf)],capture_output=True,text=True,check=True,env={**os.environ,'LC_ALL':'C'})
 match=re.search(r'^Pages:\s+(\d+)',result.stdout,re.MULTILINE)
 if not match: raise ValueError(f'No se pudo contar las páginas: {pdf}')
 return int(match.group(1))
def metadata(p):
 s=p.stem
 s=re.sub(r'\[[^\]]*\]','',s).strip(' .')
 author=''
 m=re.search(r'\(([^)]+)\)',s)
 if m: author=m[1].replace('.',' ').strip();s=s[:m.start()]
 elif p.parts[-2]=='Ficcion' and '_' in s:
  parts=s.split('_');known={'Lovecraft':('H. P. Lovecraft',1),'Poe':('Edgar Allan Poe',1),'Heinlein':('Robert A. Heinlein',1),'H':('H. G. Wells',3),'Arthur':('Arthur Conan Doyle',3),'Stephen':('Stephen Baxter',2),'Pierre':('Pierre Boulle',2),'Isabel':('Isabel Allende',2),'Alejandro':('Alejandro Jodorowsky',2),'Poul':('Poul Anderson',2),'Dick':('Philip K. Dick',1),'London':('Jack London',1),'Stevenson':('Robert Louis Stevenson',1),'Bloch':('Robert Bloch',1)}
  if parts[0] in known:author,n=known[parts[0]];s=' '.join(parts[n:])
 s=re.sub(r'[._]+',' ',s).strip()
 s=re.sub(r'(?<=[a-záéíóúñ])(?=[A-ZÁÉÍÓÚÑ])',' ',s)
 s=re.sub(r'\s+',' ',s)
 if p.parent.name=='Einstein. Sobre la teoria de la relatividad':
  s='Sobre la teoría de la relatividad'+(' · versión a' if p.stem=='a' else '');author='Albert Einstein'
 return s,author
for d in ['pdf','fuentes']:(OUT/d).mkdir(parents=True,exist_ok=True)
compilation_path=ROOT/'web/compilacion/resultados.json'
compiled={x['id']:x for x in json.loads(compilation_path.read_text())} if compilation_path.exists() else {}
items=[]; report=[]
for folder,category in CATEGORIES.items():
 for p in sorted((ROOT/folder).rglob('*.tex')):
  if p.relative_to(ROOT).as_posix() in EXCLUDED:continue
  rel=p.relative_to(ROOT).as_posix(); uid=hashlib.sha256(rel.encode()).hexdigest()[:14]
  title,author=metadata(p)
  assets={p};pending=[p];missing=set()
  while pending:
   f=pending.pop();text=re.sub(r'(?<!\\)%[^\n]*','',read(f))
   refs=[]
   for cmd, names in re.findall(r'\\(includegraphics|input|include|bibliography|usepackage)\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}',text):
    for name in names.split(','):
     name=name.strip()
     exts={'includegraphics':['.pdf','.png','.jpg','.jpeg','.eps'],'input':['.tex'],'include':['.tex'],'bibliography':['.bib'],'usepackage':['.sty']}[cmd]
     q=resolve(name,f.parent,exts)
     if q:
      if q not in assets:
       assets.add(q)
       if q.suffix=='.tex':pending.append(q)
     elif cmd!='usepackage':missing.add(name)
  # Include nearby auxiliary resources, including legacy image commands.
  for base in [p.parent,ROOT/'Imagenes']:
   assets.update(q for q in base.iterdir() if q.is_file() and q.suffix.lower() in {'.png','.jpg','.jpeg','.eps','.svg','.bib','.sty','.cls'})
  pdf=p.with_suffix('.pdf');pdfurl=None;pages=None
  if pdf.exists():
   pages=page_count(pdf)
   pdfurl=f'pdf/{uid}.pdf';shutil.copyfile(pdf,OUT/pdfurl)
  zipurl=f'fuentes/{uid}.zip'
  with zipfile.ZipFile(OUT/zipurl,'w',zipfile.ZIP_DEFLATED) as z:
   for asset in sorted(assets):
    name=asset.relative_to(ROOT).as_posix()
    if asset.suffix.lower() in TEXT_EXTENSIONS:z.writestr(name,utf8_source(asset))
    else:z.write(asset,name)
   warnings=[name for name in (asset.relative_to(ROOT).as_posix() for asset in assets) if name in encoding_report and (encoding_report[name]['caracteres_irrecuperables'] or encoding_report[name]['controles_existentes'])]
   if warnings:z.writestr('AVISOS-CODIFICACION.txt','Estos archivos ya contenían caracteres perdidos o controles en el original. La conversión a UTF-8 no los repara; necesitan revisión:\n'+'\n'.join(warnings)+'\n')
   z.writestr('LEEME.txt','Archivo principal: '+rel+'\n\nFuentes de texto convertidas a UTF-8 y declaraciones inputenc actualizadas. En Overleaf: Nuevo proyecto > Subir proyecto, selecciona este ZIP y establece como documento principal el archivo indicado arriba. Se conserva la estructura original. Se incluyen recursos locales y compartidos. El estado de compilación y las advertencias se indican en la ficha de la web. Diagramas de barras requiere el paquete externo bar.sty (https://ctan.org/pkg/bar), no incluido en el ZIP. Para imágenes compartidas, puede ser necesario añadir ../Imagenes/ a la ruta de búsqueda de LaTeX.\n\nReferencias no encontradas: '+(', '.join(sorted(missing)) or 'Ninguna detectada')+'\n')
  item=dict(id=uid,title=title,author=author,category=category,original=rel,pdf=pdfurl,pages=pages,source=zipurl,missing=sorted(missing),encodingWarnings=warnings,compiled=bool(compiled.get(uid,{}).get('ok')),compileWarnings=compiled.get(uid,{}).get('advertencias',[]))
  items.append(item)
  if missing:report.append({'archivo':rel,'referencias_no_encontradas':sorted(missing)})
items.sort(key=lambda x:norm(x['title']))
(OUT/'catalogo.js').write_text('window.CATALOGO = '+json.dumps(items,ensure_ascii=False)+';\n')
(ROOT/'web/informe-recursos.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(OUT/'.nojekyll').touch()
print(f'{len(items)} entradas, {sum(bool(x["pdf"]) for x in items)} PDF, {len(report)} entradas con referencias pendientes.')

(ROOT/'web/informe-codificacion.json').write_text(json.dumps(encoding_report,ensure_ascii=False,indent=2),encoding='utf-8')
