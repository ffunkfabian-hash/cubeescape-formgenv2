"""Website unter out/: Start, Waffen, Roboter und eine 3D-Seite; läuft offline per file://, ohne node und ohne Netz.

Jede Datei ist ein Artefakt aus formgen/cache.py; ohne --force entsteht nur Fehlendes. Blätter (out/sheets) bleiben unberührt.
Es erscheinen nur Blätter mit bekanntem Spec-Format, Waffen (`formgenv2/weapon-sheet-spec`) und Roboter (`formgenv2/robot-sheet-spec`).
Beschreibung: docs/website.md. Die GLBs liegen je Blatt als Base64 in out/models3d/<ID>.js, weil fetch unter file:// scheitert.
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
from pathlib import Path

from .. import wspec
from ..cache import Artifact, canonical, file_hash, run_artifacts
from ..versions import VIEWER

SITE = 1
HERE = Path(__file__).resolve().parent
from ..robot.spec import FORMAT as ROBOT_FORMAT, VERSION as ROBOT_VERSION
ROBOT_FIELDS = ('id', 'name_de', 'kind', 'line', 'skin', 'dimensions_mm', 'parts', 'assemblies')
THREE = json.loads((HERE/'vendor/three.json').read_text(encoding='utf-8'))
WEB_FILES = {'site.css': 'site.css', 'site.js': 'site.js', 'viewer3d.js': 'viewer3d.js', 'markierung.js': 'markierung.js',
             'change-request.js': 'change-request.js', THREE['file']: f"vendor/{THREE['file']}",
             THREE['license_file']: f"vendor/{THREE['license_file']}"}
PAGES = {'index.html': 'start', 'waffen.html': 'waffen', 'roboter.html': 'roboter', '3d.html': 'modell'}
NAV = (('index.html', 'Start', 'start'), ('waffen.html', 'Waffen', 'waffen'), ('roboter.html', 'Roboter', 'roboter'))
esc = html.escape


def robot_spec(doc: dict) -> dict:
    """Roboter-Blatt prüfen; neuere oder unvollständige Specs brechen ab statt still angenommen zu werden."""
    if doc.get('version') != ROBOT_VERSION:
        raise ValueError(f"Unbekannte Version von {ROBOT_FORMAT}: {doc.get('version')!r}")
    missing = [k for k in ROBOT_FIELDS if k not in doc]
    if missing or doc['kind'] != 'robot':
        raise ValueError(f'Roboter-Spec unvollständig: {missing or "kind"}')
    return doc


def count(value) -> int:
    return len(value) if isinstance(value, (list, dict)) else int(value)


def part_labels(spec: dict) -> dict:
    parts = spec['parts'] if isinstance(spec['parts'], list) else []
    return {'parts': {p['id']: p['name_de'] for p in parts if isinstance(p, dict) and p.get('id') and p.get('name_de')},
            'assemblies': {a['id']: a['de'] for a in spec['assemblies']}}


def collect(out) -> list[dict]:
    """Waffen nach BASIC-Typ und Variante, dann Roboter; Blätter ohne Vorschau oder bekanntes Spec-Format fehlen."""
    out, found = Path(out), []
    for path in sorted((out/'sheets').glob('*.dc.html')):
        sid = path.name.removesuffix('.dc.html')
        spec_path = out/'specs'/f'{sid}.spec.json'
        if not (out/'previews'/f'{sid}.webp').exists() or not spec_path.exists():
            continue
        spec = json.loads(spec_path.read_text(encoding='utf-8'))
        has_3d = (out/'assets'/f'{sid}.glb').is_file()
        if spec.get('format') == wspec.FORMAT:
            spec = wspec.migrate(spec)   # unbekannte oder neuere Versionen brechen ab
            t, v = spec['type'], spec['variant']
            found.append({'id': sid, 'kind': 'weapon', 'name': spec['name_de'], 'has_3d': has_3d, 'labels': part_labels(spec),
                          'variant': v['letter'], 'variant_name': v['name'],
                          'group': f"BASIC-{t['num']} · {t['type_de']} ({t['type_en']})",
                          'note': f"{v['letter']} · {v['name']} · {spec['dimensions_mm']['length']:.0f} mm"})
        elif spec.get('format') == ROBOT_FORMAT:
            spec = robot_spec(spec)
            found.append({'id': sid, 'kind': 'robot', 'name': spec['name_de'], 'has_3d': has_3d, 'labels': part_labels(spec),
                          'line': spec['line'], 'skin': spec.get('skin_de', spec['skin']), 'dimensions_mm': spec['dimensions_mm'],
                          'parts': count(spec['parts']), 'assemblies': spec['assemblies']})
    weapons = sorted((i for i in found if i['kind'] == 'weapon'), key=lambda i: (i['group'], i['variant']))
    return weapons + sorted((i for i in found if i['kind'] == 'robot'), key=lambda i: (i['line'], i['id']))


def page(title: str, current: str, main: str, *, scripts: tuple = ('site.js',), footer: str = '') -> str:
    links = ''.join(f'<a href="{href}"{" aria-current=page" if key == current else ""}>{label}</a>' for href, label, key in NAV)
    tags = ''.join(f'<script defer src="web/{name}"></script>' for name in scripts)
    return ('<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)} · Formgen 2</title><link rel="stylesheet" href="web/site.css">'
            f'<nav class="bar" aria-label="Hauptnavigation"><a class="brand" href="index.html">FORMGEN <small>02</small></a>{links}</nav>'
            f'{main}<footer>{footer}</footer>{tags}</html>')


def shot(item: dict) -> str:
    sid = esc(item['id'])
    return f'<a class="shot" href="sheets/{sid}.dc.html"><img src="previews/{sid}.webp" alt="{esc(item["name"])}" loading="lazy"></a>'


def actions(item: dict) -> str:
    sid = esc(item['id'])
    three = f'<a href="3d.html?id={sid}">3D und Markierung</a>' if item['has_3d'] else '<span>3D fehlt</span>'
    return f'<p class="actions"><a href="sheets/{sid}.dc.html">Blatt</a>{three}</p>'


def start_page(items: list[dict]) -> str:
    weapons = [i for i in items if i['kind'] == 'weapon']
    robots = [i for i in items if i['kind'] == 'robot']
    variants = len({i['variant'] for i in weapons})

    def door(href, title, text, sample):
        image = f'<img src="previews/{esc(sample["id"])}.webp" alt="" loading="lazy">' if sample else '<div class="empty"></div>'
        return f'<a class="door" href="{href}">{image}<div><b>{title}</b><span>{text}</span></div></a>'
    robot_text = f'{len(robots)} Roboter' if robots else 'Noch kein Roboter gebaut'
    return page('Start', 'start', '<header><h1>Bibliothek</h1><p>Konzeptblätter, Modelle in 3D und Änderungswünsche direkt am Modell.</p></header>'
                '<main class="doors">' +
                door('waffen.html', 'Waffen', f'{len(weapons)} Blätter · {variants} Varianten', weapons[0] if weapons else None) +
                door('roboter.html', 'Roboter', robot_text, robots[0] if robots else None) + '</main>',
                footer='Läuft lokal ohne Netz. Maße und Herkunft stehen in Blatt und Spec.')


def weapons_page(items: list[dict]) -> str:
    weapons = [i for i in items if i['kind'] == 'weapon']
    groups = {}
    for item in weapons:
        groups.setdefault(item['group'], []).append(item)
    names = {i['variant']: i['variant_name'] for i in weapons}
    sections = []
    for group, entries in groups.items():
        cards = ''.join(f'<article class="card" data-variant="{esc(i["variant"])}">{shot(i)}<div><b>{esc(i["id"])}</b>'
                        f'<span>{esc(i["name"])}</span><em>{esc(i["note"])}</em>{actions(i)}</div></article>' for i in entries)
        sections.append(f'<section><h2>{esc(group)}<small>{len(entries)} Blätter</small></h2><div class="grid">{cards}</div></section>')
    options = '<option value="">alle Varianten</option>' + ''.join(
        f'<option value="{esc(v)}">{esc(v)} · {esc(names[v])}</option>' for v in sorted(names))
    return page('Waffen', 'waffen', f'<header><h1>Waffen</h1><p>Waffen-Varianten auf den 17 BALLON-Grundformen.</p>'
                f'<p>{len(weapons)} Konzeptblätter · {len(names)} Varianten · lokal verfügbar</p>'
                '<div class="tools"><input type="search" aria-label="Blätter filtern" placeholder="Name, Typ oder Kennung …">'
                f'<select aria-label="Variante">{options}</select></div></header><main>{"".join(sections)}</main>',
                footer='Maße, Herkunft (BALLON-Commit und Quellhash) und Generatorschritte stehen in Blatt und Spec.')


def robots_page(items: list[dict]) -> str:
    robots = [i for i in items if i['kind'] == 'robot']
    lines = {}
    for item in robots:
        lines.setdefault(item['line'], []).append(item)
    sections = []
    for line, entries in lines.items():
        cards = []
        for item in entries:
            sid, size = esc(item['id']), item['dimensions_mm']
            facts = [('Höhe', f"{size['height']:.0f} mm"), ('Breite', f"{size['width']:.0f} mm"), ('Tiefe', f"{size['depth']:.0f} mm"),
                     ('Bauteile', str(item['parts'])), ('Baugruppen', str(len(item['assemblies']))), ('Skin', item['skin'])]
            chips = ''.join((f'<li><a href="3d.html?id={sid}&amp;baugruppe={esc(a["id"])}">{esc(a["de"])}</a></li>' if item['has_3d']
                             else f'<li><span>{esc(a["de"])}</span></li>') for a in item['assemblies'])
            cards.append(f'<article class="robot">{shot(item)}<div><b>{sid}</b><h3>{esc(item["name"])}</h3><dl>' +
                         ''.join(f'<div><dt>{k}</dt><dd>{esc(str(v))}</dd></div>' for k, v in facts) + f'</dl>{actions(item)}</div>'
                         f'<section class="parts"><h3>Baugruppen</h3><ul class="chips">{chips}</ul></section></article>')
        sections.append(f'<section><h2>Linie {esc(line.title())}<small>{len(entries)} Roboter</small></h2><div class="robots">{"".join(cards)}</div></section>')
    body = ''.join(sections) or '<p class="note">Noch kein Roboter gebaut.</p>'
    return page('Roboter', 'roboter', f'<header><h1>Roboter</h1><p>Roboter nach Linien.</p></header><main>{body}</main>',
                footer='Baugruppen öffnen die 3D-Ansicht nur mit dieser Baugruppe.')


ICONS = {'orbit': '<path d="M3 11c0-3 4-5 9-5s9 2 9 5-4 5-9 5"/><path d="m5 7-2 4 4 1"/><circle cx="12" cy="11" r="2"/>',
         'point': '<circle cx="12" cy="12" r="4"/><path d="M12 2v4m0 12v4M2 12h4m12 0h4"/>',
         'line': '<path d="m5 18 13-13"/><circle cx="4" cy="19" r="2"/><circle cx="19" cy="4" r="2"/>',
         'brush': '<path d="m9 13 9-10c2-2 4 0 2 2l-9 11M10 14c-5-3-6 1-6 4 0 2-2 2-2 2 7 2 12-2 8-6Z"/>',
         'undo': '<path d="m8 5-6 5 6 5M3 10h10c5 0 7 3 7 8"/>', 'redo': '<path d="m16 5 6 5-6 5m5-5H11c-5 0-7 3-7 8"/>'}


def tool(key: str, label: str, attrs: str) -> str:
    icon = (f'<svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[key]}</svg>')
    return f'<button type="button" {attrs} disabled>{icon} {label}</button>'


def model_page() -> str:
    tools = ''.join(tool(k, label, f'data-tool="{k}" aria-pressed="false"')
                    for k, label in (('orbit', 'Drehen'), ('point', 'Punkt'), ('line', 'Strich'), ('brush', 'Pinsel')))
    tools += tool('undo', 'Rückgängig', 'data-undo title="Rückgängig (Strg/⌘ Z)"')
    tools += tool('redo', 'Wiederholen', 'data-redo title="Wiederholen (Strg/⌘ Umschalt Z)"')
    panel = ('<aside data-annotation><div class="fg-tools" role="group" aria-label="Markierungswerkzeuge">' + tools + '</div>'
             '<label data-size hidden>Pinselbreite <input data-width type="range" min="2" max="60" step="1"><output></output></label>'
             '<p class="state"><span data-count></span> · <span role="status" aria-live="polite"></span></p>'
             '<button type="button" data-open>Datei öffnen …</button><input type="file" data-file accept=".json,application/json" hidden>'
             '<div data-editor hidden><label>Markierungen<select data-list size="4"></select></label>'
             '<label>Kommentar zur Auswahl<textarea data-note rows="2"></textarea></label>'
             '<button type="button" data-remove>Auswahl entfernen</button>'
             '<label>Gemeinsamer Änderungswunsch<textarea data-global rows="2"></textarea></label>'
             '<button type="button" data-export disabled>Änderungsdatei speichern</button></div></aside>')
    guide = ('<div data-guide hidden><svg width="100%" height="100%"><line stroke="#ff652a" stroke-width="3" stroke-dasharray="6 4"/></svg></div>')
    main = ('<main class="model"><header class="model-head"><div><b data-id></b><h1 data-name>3D-Ansicht</h1></div>'
            '<nav class="actions" aria-label="Blatt"><a data-prev hidden>← Vorheriges</a><a data-next hidden>Nächstes →</a><a data-sheet hidden>Blatt</a></nav></header>'
            '<p id="error" class="note" hidden></p><div class="workspace" data-workspace hidden><div>'
            f'<div class="stage" data-orbit>{guide}</div><div class="stage-foot"><small>Mausrad gedrückt ziehen: drehen · mit Umschalt: verschieben · '
            'Scrollen: zoomen</small><label data-view hidden>Ansicht <select data-assembly></select></label>'
            '<button type="button" data-reset disabled>Ansicht zurücksetzen</button></div></div>' + panel + '</div></main>')
    license_link = f'<a href="web/{THREE["license_file"]}">Three.js {THREE["version"]} (MIT)</a>'
    return page('3D-Ansicht', 'modell', main, footer=f'Änderungsdateien: Format formgen/change-request. {license_link}',
                scripts=(THREE['file'], 'change-request.js', 'catalog.js', 'markierung.js', 'viewer3d.js'))


def catalog_js(items: list[dict]) -> str:
    rows = [{k: i[k] for k in ('id', 'kind', 'name', 'has_3d')} for i in items]
    return 'window.formgenCatalog=' + json.dumps({'items': rows}, ensure_ascii=False, separators=(',', ':')) + ';\n'


def render_page(artifact: Artifact) -> str:
    items = artifact.inputs['items']
    return {'start': start_page, 'waffen': weapons_page, 'roboter': robots_page,
            'modell': lambda _: model_page(), 'catalog': catalog_js}[artifact.params['page']](items)


def copy_file(artifact: Artifact) -> bytes:
    return Path(artifact.inputs['path']).read_bytes()


def render_model(artifact: Artifact) -> str:
    raw = Path(artifact.inputs['glb']).read_bytes()
    sid = artifact.model_id
    meta = {'id': sid, 'asset': f'{sid}.glb', 'asset_sha256': hashlib.sha256(raw).hexdigest(), 'labels': artifact.inputs['labels']}
    return 'window.formgenModel=' + json.dumps({**meta, 'glb': base64.b64encode(raw).decode('ascii')}, ensure_ascii=False) + ';\n'


def artifacts(out) -> list[Artifact]:
    out = Path(out)
    found = collect(out)
    versions = {'VIEWER': VIEWER, 'SITE': SITE}
    source = hashlib.sha256(canonical(found)).hexdigest()
    code = file_hash(Path(__file__))
    plan = [Artifact('SITE', 'viewer', source, {'page': key, 'code': code}, versions, name, 'formgen.web.site:render_page', {'items': found})
            for name, key in PAGES.items()]
    plan.append(Artifact('SITE', 'viewer', source, {'page': 'catalog', 'code': code}, versions, 'web/catalog.js',
                         'formgen.web.site:render_page', {'items': found}))
    for name, relative in WEB_FILES.items():
        path = HERE/relative
        plan.append(Artifact('SITE', 'web', file_hash(path), {'file': name}, versions, f'web/{name}', 'formgen.web.site:copy_file', {'path': str(path)}))
    for item in found:
        if item['has_3d']:
            glb = out/'assets'/f"{item['id']}.glb"
            key = hashlib.sha256(canonical({'glb': file_hash(glb), 'labels': item['labels']})).hexdigest()
            plan.append(Artifact(item['id'], 'models3d', key, {}, versions, f"models3d/{item['id']}.js", 'formgen.web.site:render_model',
                                 {'glb': str(glb), 'labels': item['labels']}))
    return plan


def build(out, cache, force: bool = False):
    return run_artifacts(artifacts(out), Path(out), Path(cache), force=force)
