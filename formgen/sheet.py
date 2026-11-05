"""HTML concept sheets using existing, separately cached image files only.

Layout requirements adapted from cubeescape-formgen/claude/generator/xl.py
and views.py (read-only v1 reference, 2026-10-26). No v1 model code or
rendering is copied. Typography: bundled Barlow (SIL Open Font License).
"""
from __future__ import annotations

from html import escape
import math
from pathlib import Path
import re
import tomllib

from .versions import SHEET as VERSION

ORTHOS = (("side_left", "Seite links"), ("side_right", "Seite rechts"),
          ("front", "Vorn"), ("back", "Hinten"), ("top", "Oben"), ("bottom", "Unten"))
SKINS = ("standard", "nacht", "polar", "kobalt")
PRIORITY = ("Gehäuse", "Oberes Gehäuse", "Griff", "Abzug", "Magazin", "Lauf", "Mündung", "Schaft")

CSS = """
@font-face{font-family:Barlow;src:url('../fonts/Barlow-Regular.ttf') format('truetype');font-weight:400;font-display:swap}
@font-face{font-family:Barlow;src:url('../fonts/Barlow-SemiBold.ttf') format('truetype');font-weight:600;font-display:swap}
:root{color-scheme:light;--paper:#f3f1ec;--ink:#22252a;--muted:#64696f;--rule:#d3d1ca;--accent:#995021;--stage:#777;--white:#fffefa}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:Barlow,Arial,sans-serif;font-size:16px;line-height:1.5}main{max-width:1680px;margin:auto;padding:44px 48px 32px}a{color:inherit}h1,h2,h3,p,figure{margin:0}h1{font-size:clamp(32px,4vw,64px);font-weight:600;line-height:1.05;letter-spacing:-.03em}h2{font-size:21px;font-weight:600}h3{font-size:17px;font-weight:600}.eyebrow{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}.topline{display:flex;justify-content:space-between;gap:20px;padding-bottom:18px;border-bottom:1px solid var(--rule)}.masthead{display:flex;align-items:end;gap:28px;justify-content:space-between;padding:28px 0}.model-id{font-size:64px;line-height:1;font-weight:600;color:var(--accent);letter-spacing:-.06em}.subtitle{color:var(--muted);max-width:68ch;margin-top:12px}.facts{display:flex;gap:25px;flex-wrap:wrap;margin:0;padding:0 0 24px}.facts div{border-left:2px solid var(--rule);padding-left:12px}.facts dt{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}.facts dd{margin:2px 0 0;font-weight:600}.section{margin-top:30px}.section-head{display:flex;justify-content:space-between;align-items:baseline;gap:18px;margin-bottom:12px}.section-head p,.note{font-size:13px;color:var(--muted)}.hero-layout{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(0,1fr);gap:20px}.hero-panel{align-self:start}.orthos{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.panel{min-width:0;background:var(--white);border:1px solid var(--rule);break-inside:avoid}.stage{position:relative;background:var(--stage);overflow:hidden}.stage img{display:block;width:100%;height:100%;object-fit:contain}.overlay{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}.references line{stroke:#ece9e1;stroke-width:1;stroke-dasharray:7 7;opacity:.65}.callout line,.callout circle{stroke:#fffefa;stroke-width:1.3}.callout circle{fill:#303337}.callout text{fill:#fffefa;font-family:Barlow,Arial,sans-serif;font-size:19px;font-weight:600;text-anchor:middle;dominant-baseline:central}.panel figcaption{padding:10px 14px;font-size:13px;display:flex;gap:14px;justify-content:space-between}.caption-tag{color:var(--muted);font-size:11px}.missing{display:flex;align-items:center;justify-content:center;min-height:140px;height:100%;text-align:center;padding:25px;color:#fffefa;background:repeating-linear-gradient(135deg,#777,#777 12px,#747474 12px,#747474 24px)}.legend{margin:0;padding:14px 16px;list-style:none;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px 16px;font-size:13px}.legend li{display:flex;gap:8px}.number{color:var(--accent);font-weight:600;font-variant-numeric:tabular-nums}.legend-note{padding:0 16px 14px;color:var(--muted);font-size:12px}.detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.sight-grid,.skin-grid,.figure-grid,.pose-grid{display:grid;gap:16px;grid-template-columns:repeat(2,minmax(0,1fr))}.skin-grid{grid-template-columns:repeat(4,minmax(0,1fr))}.materials{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}.material{border:1px solid var(--rule);padding:12px;background:var(--white);display:grid;gap:7px}.swatch{height:38px;border:1px solid #0002;border-radius:2px}.material p{font-size:12px;color:var(--muted)}.prompts{display:grid;grid-template-columns:1fr 1fr;gap:22px}.prompt{padding:20px;background:var(--white);border-top:2px solid var(--rule)}.prompt p{margin-top:10px;font-size:14px;line-height:1.65;white-space:pre-wrap;overflow-wrap:anywhere}.warnings{border:1px solid #b18b58;background:#f2e8d9;margin:0 0 20px;padding:10px 15px;font-size:13px}.warnings summary{cursor:pointer;font-weight:600}.warnings ul{margin:10px 0 4px;padding-left:20px}.warnings li+li{margin-top:5px}.assembly{margin-top:30px;padding-top:24px;border-top:1px solid var(--rule);break-before:page}.assembly-layout{display:grid;grid-template-columns:1fr 1fr;gap:20px}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:13px}th{text-align:left;color:var(--muted);font-size:11px;letter-spacing:.05em;text-transform:uppercase}th,td{padding:9px 10px;border-bottom:1px solid var(--rule);vertical-align:top}td{overflow-wrap:anywhere}.anchor-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;padding:0;list-style:none}.anchor-list li{padding:10px 12px;border-left:2px solid var(--rule);font-size:13px}.anchor-list small{display:block;color:var(--muted)}footer{border-top:1px solid var(--rule);margin-top:32px;padding-top:14px;display:flex;justify-content:space-between;gap:24px;font-size:12px;color:var(--muted)}.empty{padding:20px;border:1px dashed var(--rule);color:var(--muted)}
@media(max-width:1000px){main{padding:25px}.hero-layout{grid-template-columns:1fr}.skin-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.assembly-layout{grid-template-columns:1fr}}
@media(max-width:600px){main{padding:18px}.masthead{align-items:start;gap:12px}.model-id{font-size:42px}.detail-grid,.prompts,.figure-grid,.pose-grid{grid-template-columns:1fr}.legend,.anchor-list{grid-template-columns:1fr}.section-head{display:block}.topline,footer{font-size:11px}.facts{gap:16px}.panel figcaption{padding:8px;font-size:12px}.skin-grid{gap:10px}}
@media print{body{background:white}main{max-width:none;padding:15mm}.warnings{break-inside:avoid}.stage,.swatch{-webkit-print-color-adjust:exact;print-color-adjust:exact}details.warnings ul{display:block}.prompt{break-inside:avoid}.assembly{page-break-before:always}}
"""


def esc(value):
    return escape(str(value if value is not None else ""), quote=True)


def _number(value, fallback=0):
    try:
        result = float(value)
        return result if math.isfinite(result) else fallback
    except (TypeError, ValueError):
        return fallback


def metadata(views, key):
    return views.get("_meta", {}).get(key, {})


def selected_labels(views, key):
    meta = metadata(views, key)
    labels = meta.get("labels")
    if labels is None:
        labels = [{"label": label, "x": xy[0], "y": xy[1]}
                  for label, xy in meta.get("anchors", {}).items()]
    labels = [entry for entry in labels if entry.get("label")]
    return sorted(labels, key=lambda item: (PRIORITY.index(item["label"])
                  if item["label"] in PRIORITY else len(PRIORITY), item["label"]))[:8]


def _overlay(views, key, width, height, callouts=False, references=False):
    meta = metadata(views, key)
    elements = []
    if references:
        lines = meta.get("reference_lines", {})
        for y in lines.get("horizontal", []):
            y = _number(y)
            elements.append(f'<line x1="0" y1="{y:g}" x2="{width:g}" y2="{y:g}"/>')
        for x in lines.get("vertical", []):
            x = _number(x)
            elements.append(f'<line x1="{x:g}" y1="0" x2="{x:g}" y2="{height:g}"/>')
    result = '<g class="references">' + ''.join(elements) + '</g>'
    if callouts:
        # Number badges keep translated/long names out of the image. Leaders are
        # short; full names live in a flowing legend, never clipped into a pill.
        for index, entry in enumerate(selected_labels(views, key), 1):
            x, y = _number(entry.get("x")), _number(entry.get("y"))
            bx = max(20, min(width-20, x+27))
            by = max(20, min(height-20, y-27))
            result += (f'<g class="callout"><line x1="{x:g}" y1="{y:g}" x2="{bx:g}" y2="{by:g}"/>'
                       f'<circle cx="{bx:g}" cy="{by:g}" r="16"/><text x="{bx:g}" y="{by:g}">{index}</text></g>')
    return f'<svg class="overlay" viewBox="0 0 {width:g} {height:g}" aria-hidden="true">{result}</svg>'


def panel(views, key, title, *, size=(960, 480), callouts=False, references=False, note=""):
    meta = metadata(views, key)
    width = max(1, _number(meta.get("width"), size[0]))
    height = max(1, _number(meta.get("height"), size[1]))
    path = views.get(key)
    if path and not isinstance(path, str):
        raise TypeError(f"Bildpfad für {key} muss Text sein")
    if path and (path.startswith('//') or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", path)):
        raise ValueError("Blätter benötigen separate lokale Bilddateien, keine eingebetteten oder entfernten Bilder")
    image = (f'<img src="{esc(path)}" width="{width:g}" height="{height:g}" alt="{esc(title)}" decoding="async">'
             + _overlay(views, key, width, height, callouts, references) if path else
             '<div class="missing">Ansicht ausstehend</div>')
    return (f'<figure class="panel" data-view="{esc(key)}"><div class="stage" style="aspect-ratio:{width:g}/{height:g}">{image}</div>'
            f'<figcaption><span>{esc(title)}</span><span class="caption-tag">{esc(note)}</span></figcaption></figure>')


def warnings_html(warnings):
    items = list(dict.fromkeys(str(w) for w in warnings if w))
    if not items:
        return ''
    first = items[0]
    if len(first) > 150:
        first = first[:147] + '…'
    return (f'<details class="warnings"><summary>{len(items)} offene Hinweise · {esc(first)}</summary><ul>'
            + ''.join(f'<li>{esc(item)}</li>' for item in items) + '</ul></details>')


def header(document, kind):
    info = document['info']
    title = info.get('name_de', info.get('name', info['id']))
    subtitle = info.get('summary', info.get('description', info.get('nick', '')))
    bounds = document.get('bounds_m')
    if not bounds:
        vertices = [v for p in document.get('parts', []) for v in p.get('mesh', {}).get('vertices', [])]
        if vertices:
            bounds = [[min(v[i] for v in vertices) for i in range(3)],
                      [max(v[i] for v in vertices) for i in range(3)]]
    facts = [('Bauteile', str(len(document.get('parts', []))))]
    if bounds:
        sizes = [1000 * (bounds[1][i]-bounds[0][i]) for i in range(3)]
        facts = [('Länge', f'{sizes[1]:.1f} mm'), ('Höhe', f'{sizes[2]:.1f} mm'), ('Breite', f'{sizes[0]:.1f} mm')] + facts
    provenance = info.get('provenance', {})
    if isinstance(provenance, dict) and provenance.get('kind'):
        facts.append(('Entwurfsmaße', provenance['kind']))
    facts += [tuple(fact) for fact in info.get('facts', [])]
    return (f'<div class="topline"><span class="eyebrow">Formgen · Design Collection</span><span class="eyebrow">{esc(kind)}</span></div>'
            f'<header class="masthead"><div><h1>{esc(title)}</h1><p class="subtitle">{esc(subtitle)}</p></div>'
            f'<div class="model-id">{esc(info["id"])}</div></header><dl class="facts">'
            + ''.join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in facts) + '</dl>')


def section(title, content, note='', class_name=''):
    return (f'<section class="section {esc(class_name)}"><div class="section-head"><h2>{esc(title)}</h2>'
            f'<p>{esc(note)}</p></div>{content}</section>')


def materials_html(document):
    # Static catalogue is shared with the renderer; no color constants in models.
    with (Path(__file__).resolve().parents[1] / 'skins.toml').open('rb') as stream:
        catalogue = tomllib.load(stream)
    roles = catalogue['roles']
    skin = catalogue['skins'].get(document.get('info', {}).get('skin'), {})    # nur Roboter tragen info.skin
    used = {}
    for part in document.get('parts', []):
        role = part.get('role', 'shell')
        color = part.get('color', skin.get('roles', {}).get(role, roles.get(role, {}).get('color', '')))
        if isinstance(color, (list, tuple)) and len(color) >= 3:
            rgb = [_number(c) for c in color[:3]]
            factor = 255 if max(rgb) <= 1 else 1
            color = '#' + ''.join(f'{max(0,min(255,round(c*factor))):02x}' for c in rgb)
        used.setdefault((role, str(color)), roles.get(role, {}))
    tiles = []
    for (role, color), value in used.items():
        valid_color = color if re.fullmatch(r'#[0-9a-fA-F]{6}', color) else 'transparent'
        detail = ' · '.join(text for text in (
            f'Rauheit {value["rough"]:g}' if 'rough' in value else '',
            f'Metall {value["metal"]:g}' if 'metal' in value else '') if text)
        tiles.append(f'<article class="material"><div class="swatch" style="background:{valid_color}"></div>'
                     f'<h3>{esc(value.get("de", role))}</h3><p>{esc(detail or "Material aus Modellquelle")}</p></article>')
    return '<div class="materials">' + ''.join(tiles) + '</div>'


def prompts_html(document):
    from .prompts import build as build_prompts
    prompts = build_prompts(document)
    return '<div class="prompts">' + ''.join(
        f'<article class="prompt" lang="{lang}"><h3>Prompt · {name}</h3><p>{esc(prompts[lang])}</p></article>'
        for lang, name in (('de', 'Deutsch'), ('en', 'English'))) + '</div>'


def page(document, body):
    info = document['info']
    title = info.get('name_de', info.get('name', info['id']))
    return (f'<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(info["id"])} · {esc(title)} · Konzeptblatt</title><style>{CSS}</style></head><body><main>{body}'
            '<footer><span>Formgen · Entwurfsstudie</span><span>Maße aus Modellgeometrie · keine Fertigungszeichnung</span></footer>'
            '</main></body></html>')


def build(document, views):
    """Return a weapon/sight sheet; never render, write files, or embed pixels.

    ``views`` maps names to stable relative image paths. Optional ``_meta``
    contains per-image width/height, labels, scale_px_m and reference_lines.
    Missing images remain explicit. ``figure`` documents dispatch separately.
    """
    if document['info'].get('kind') == 'figure':
        from .sheet_figure import build as build_figure
        return build_figure(document, views)
    sight = document['info'].get('kind') == 'sight'
    hero_key = 'iso' if sight else 'hero'
    warnings = list(document.get('warnings', []))
    required = [hero_key] + [key for key, _ in ORTHOS] + ['skin_' + skin for skin in SKINS]
    has_sight = any(p.get('sight') or p.get('assembly') == 'sight' for p in document.get('parts', []))
    if not sight:
        required += ['detail_trigger']
        if has_sight:
            required += ['sight_iso', 'sight_side']
    missing = [key for key in required if not views.get(key)]
    if missing:
        warnings.append('Ansichten ausstehend: ' + ', '.join(missing))
    scales = [metadata(views, key).get('scale_px_m') for key, _ in ORTHOS]
    widths = [metadata(views, key).get('width') for key, _ in ORTHOS]
    verified_scale = (all(isinstance(s, (float, int)) and math.isfinite(s) and s > 0 for s in scales)
                      and max(scales)-min(scales) < 1e-6
                      and all(isinstance(w, (float, int)) and w > 0 for w in widths)
                      and max(widths)-min(widths) < 1e-6)
    if not verified_scale:
        warnings.append('Gemeinsamer Maßstab der sechs Orthogonalansichten noch nicht belegt.')
    labels = selected_labels(views, hero_key)
    legend = '<ol class="legend">' + ''.join(
        f'<li><span class="number">{i:02}</span>{esc(entry["label"])}</li>' for i, entry in enumerate(labels, 1)) + '</ol>'
    if not labels:
        legend = '<p class="legend-note">Bauteilbeschriftungen ausstehend.</p>'
    named = {entry['label'] for entry in labels}
    remaining = sorted({p.get('label') for p in document.get('parts', [])
                        if p.get('label') and p.get('label') not in named and not p.get('sight') and p.get('assembly') != 'sight'})
    if remaining:
        legend += '<p class="legend-note">Weitere Bauteile: ' + esc(', '.join(remaining)) + '</p>'
    hero = '<div class="hero-panel">' + panel(views, hero_key, 'Isometrie' if sight else 'Isometrie · ohne Wechselvisier', size=(1440, 960), callouts=True) + legend + '</div>'
    orthos = '<div class="orthos">' + ''.join(panel(views, key, title, references=True) for key, title in ORTHOS) + '</div>'
    body = header(document, 'Visier · Konzeptblatt' if sight else 'Waffe · Konzeptblatt XL') + warnings_html(warnings)
    body += section('Form & Aufbau', '<div class="hero-layout">' + hero + orthos + '</div>',
                    'Sechs Orthogonalansichten · gleicher Maßstab' if verified_scale else 'Sechs Orthogonalansichten · Maßstab offen')
    if not sight:
        optics = ('<div class="sight-grid">' + panel(views, 'sight_iso', 'Visier · Schrägansicht') + panel(views, 'sight_side', 'Visier · Seite') + '</div>'
                  if has_sight or views.get('sight_iso') else '<p class="empty">Kein Wechselvisier im Modell enthalten.</p>')
        body += section('Details & Optik', '<div class="detail-grid"><div>' + panel(views, 'detail_trigger', 'Detail · Abzugsbereich') + '</div><div>' + optics + '</div></div>')
    body += section('Materialfelder', materials_html(document), 'Farben und Oberflächen der Modellquelle')
    body += section('Vier Skins', '<div class="skin-grid">' + ''.join(panel(views, 'skin_' + skin, title, size=(960, 640))
                    for skin, title in zip(SKINS, ('Standard', 'Nachtschicht', 'Polar', 'Kobalt'))) + '</div>')
    body += section('Bildbeschreibung', prompts_html(document), 'Aus Bauteilen, Materialrollen und Modellmaßen')
    return page(document, body)
