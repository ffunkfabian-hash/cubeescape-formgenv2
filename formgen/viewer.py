"""Offline-Galerie, angepasst an Formgen v1 make_viewer.py; keine Rasteraufrufe."""
from __future__ import annotations
import argparse, hashlib, html, json
from pathlib import Path
from .versions import VIEWER as VERSION
from .cache import Artifact,canonical,run_artifacts


def render(artifact):
    cards=[]
    for item in artifact.params['items']:
        sid=html.escape(item['id']);name=html.escape(item['name'])
        cards.append(f'<a class="card" href="sheets/{sid}.dc.html"><img src="previews/{sid}.webp" alt="{name}" loading="lazy"><div><b>{sid}</b><span>{name}</span></div></a>')
    count=len(cards)
    return '''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Formgen · Bibliothek</title>
<style>*{box-sizing:border-box}body{margin:0;background:#171c22;color:#eee9df;font:16px system-ui}header{padding:44px 6vw 28px;border-bottom:1px solid #3c424a}h1{font-size:42px;margin:0 0 8px}header p{color:#aab3bd;margin:8px 0}input{margin:22px 0 0;padding:12px 16px;width:min(480px,100%);background:#262e37;border:1px solid #697480;color:#fff;border-radius:6px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:24px;padding:32px 6vw}.card{background:#252d36;border:1px solid #3e4853;border-radius:12px;overflow:hidden;color:inherit;text-decoration:none}.card:hover{border-color:#dc8d50}.card img{width:100%;aspect-ratio:1.5;object-fit:contain;background:#808080}.card div{padding:20px;display:flex;gap:14px}.card b{color:#ed9857}.card span{color:#cbd0d5}footer{padding:24px 6vw;color:#aab3bd}a:focus-visible{outline:3px solid #ed9857}</style>
<header><h1>FORMGEN <small style="font-size:.45em;color:#dc8d50">02</small></h1><p>Modelle, Materialien und Baugruppen.</p><p>'''+str(count)+''' Konzeptblätter · lokal verfügbar</p><input type="search" aria-label="Modelle filtern" placeholder="Name oder Kennung suchen …"></header><main class="grid">'''+''.join(cards)+'''</main><footer>Maße und Herkunft stehen auf den jeweiligen Blättern. Offene Prüfungen sind dort ausgewiesen.</footer><script>document.querySelector('input').addEventListener('input',e=>{for(const c of document.querySelectorAll('.card'))c.hidden=!c.textContent.toLowerCase().includes(e.target.value.toLowerCase())})</script></html>'''


def build(out,cache):
    out=Path(out);items=[]
    for p in sorted((out/'sheets').glob('*.dc.html')):
        sid=p.name.removesuffix('.dc.html')
        if not (out/'previews'/f'{sid}.webp').exists():continue
        sp=out/'specs'/f'{sid}.spec.json';s=json.loads(sp.read_text()) if sp.exists() else {}
        name=s.get('weapon',{}).get('name_de') or s.get('figure',{}).get('name_de') or sid
        items.append({'id':sid,'name':name})
    source=hashlib.sha256(canonical(items)).hexdigest()
    a=Artifact('INDEX','viewer',source,{'items':items},{'VIEWER':VERSION},'index.html','formgen.viewer:render',{})
    return run_artifacts([a],out,Path(cache))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1]/'out');p.add_argument('--cache',type=Path,default=Path.home()/'Library/Caches/CubeEscapeFormgen/artifacts');a=p.parse_args()
    results=build(a.out,a.cache);print(f'{sum(r.built for r in results)} Viewer gebaut')
