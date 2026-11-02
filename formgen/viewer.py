"""Offline-Galerie out/index.html nach dem Prinzip von Formgen v1 make_viewer.py; keine Rasteraufrufe.

Liest nur vorhandene Blätter, Vorschauen und Specs. Waffenblätter (Spec `formgenv2/weapon-sheet-spec`) werden nach
BASIC-Typ gruppiert und tragen Variante und Namen; übrige Blätter (Contour-Piloten, R01) stehen in „Weitere“.
"""
from __future__ import annotations
import argparse, hashlib, html, json
from pathlib import Path
from .versions import VIEWER as VERSION
from .cache import Artifact,canonical,run_artifacts

CSS = ('*{box-sizing:border-box}body{margin:0;background:#171c22;color:#eee9df;font:16px system-ui}'
       'header{padding:44px 6vw 28px;border-bottom:1px solid #3c424a}h1{font-size:42px;margin:0 0 8px}header p{color:#aab3bd;margin:8px 0}'
       '.tools{display:flex;gap:12px;flex-wrap:wrap;margin-top:22px}input,select{padding:12px 16px;background:#262e37;border:1px solid #697480;color:#fff;border-radius:6px}'
       'input{width:min(480px,100%)}h2{font-size:22px;margin:0;padding:28px 6vw 0;color:#ed9857}h2 small{color:#aab3bd;font-weight:400;margin-left:10px}'
       '.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:20px;padding:16px 6vw 8px}'
       '.card{background:#252d36;border:1px solid #3e4853;border-radius:12px;overflow:hidden;color:inherit;text-decoration:none}.card:hover{border-color:#dc8d50}'
       '.card img{width:100%;aspect-ratio:1.5;object-fit:contain;background:#808080;display:block}.card div{padding:14px 16px;display:flex;flex-direction:column;gap:4px}'
       '.card b{color:#ed9857}.card span{color:#cbd0d5}.card em{color:#8f99a4;font-style:normal;font-size:13px}footer{padding:24px 6vw;color:#aab3bd}a:focus-visible{outline:3px solid #ed9857}')


def render(artifact):
    items = artifact.params['items']
    groups = {}
    for item in items:
        groups.setdefault(item.get('group') or 'Weitere', []).append(item)
    letters = sorted({i['variant'] for i in items if i.get('variant')})
    names = {i['variant']: i['variant_name'] for i in items if i.get('variant')}
    sections = []
    for group, entries in groups.items():
        cards = []
        for item in entries:
            sid = html.escape(item['id'])
            cards.append(f'<a class="card" data-variant="{html.escape(item.get("variant") or "")}" href="sheets/{sid}.dc.html">'
                         f'<img src="previews/{sid}.webp" alt="{html.escape(item["name"])}" loading="lazy"><div><b>{sid}</b>'
                         f'<span>{html.escape(item["name"])}</span><em>{html.escape(item.get("note") or "")}</em></div></a>')
        sections.append(f'<section><h2>{html.escape(group)}<small>{len(entries)} Blätter</small></h2><div class="grid">{"".join(cards)}</div></section>')
    options = '<option value="">alle Varianten</option>' + ''.join(
        f'<option value="{html.escape(v)}">{html.escape(v)} · {html.escape(names[v])}</option>' for v in letters)
    return ('<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Formgen 2 · Bibliothek</title><style>{CSS}</style><header><h1>FORMGEN <small style="font-size:.45em;color:#dc8d50">02</small></h1>'
            f'<p>Waffen-Varianten auf den 17 BALLON-Grundformen.</p><p>{len(items)} Konzeptblätter · {len(letters)} Varianten · lokal verfügbar</p>'
            f'<div class="tools"><input type="search" aria-label="Blätter filtern" placeholder="Name, Typ oder Kennung …"><select aria-label="Variante">{options}</select></div></header>'
            f'<main>{"".join(sections)}</main><footer>Maße, Herkunft (BALLON-Commit und Quellhash) und Generatorschritte stehen in Blatt und Spec.</footer>'
            '<script>const q=document.querySelector("input"),s=document.querySelector("select");function f(){for(const c of document.querySelectorAll(".card"))'
            'c.hidden=!(c.textContent.toLowerCase().includes(q.value.toLowerCase())&&(!s.value||c.dataset.variant===s.value));'
            'for(const g of document.querySelectorAll("section"))g.hidden=![...g.querySelectorAll(".card")].some(c=>!c.hidden)}'
            'q.addEventListener("input",f);s.addEventListener("change",f)</script></html>')


def items(out):
    out = Path(out); result = []
    for p in sorted((out/'sheets').glob('*.dc.html')):
        sid = p.name.removesuffix('.dc.html')
        if not (out/'previews'/f'{sid}.webp').exists():
            continue
        sp = out/'specs'/f'{sid}.spec.json'; s = json.loads(sp.read_text()) if sp.exists() else {}
        if s.get('format') == 'formgenv2/weapon-sheet-spec':
            t, v = s['type'], s['variant']
            result.append({'id': sid, 'name': s['name_de'], 'variant': v['letter'], 'variant_name': v['name'],
                           'group': f"BASIC-{t['num']} · {t['type_de']} ({t['type_en']})",
                           'note': f"{v['letter']} · {v['name']} · {s['dimensions_mm']['length']:.0f} mm"})
        else:
            name = s.get('weapon', {}).get('name_de') or s.get('figure', {}).get('name_de') or sid
            result.append({'id': sid, 'name': name})
    weapons = sorted((i for i in result if i.get('variant')), key=lambda i: (i['group'], i['variant']))
    return weapons + [i for i in result if not i.get('variant')]


def build(out, cache, force=False):
    found = items(out)
    source = hashlib.sha256(canonical(found)).hexdigest()
    code = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a = Artifact('INDEX', 'viewer', source, {'items': found, 'code': code}, {'VIEWER': VERSION}, 'index.html', 'formgen.viewer:render', {})
    return run_artifacts([a], Path(out), Path(cache), force=force)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1]/'out');p.add_argument('--cache',type=Path,default=Path.home()/'Library/Caches/CubeEscapeFormgen/artifacts');a=p.parse_args()
    results=build(a.out,a.cache);print(f'{sum(r.built for r in results)} Viewer gebaut')
