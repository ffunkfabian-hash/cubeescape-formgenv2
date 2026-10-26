"""Figure overview and printable assembly sheets, consuming cached views.

Shares the v1-derived concept-sheet vocabulary in sheet.py. Figure assemblies,
anchors, explosion and poses are v2 additions; no figure is invented here.
"""
from __future__ import annotations

from .versions import SHEET as VERSION
from . import sheet


def _parts_table(parts):
    rows = ''.join('<tr>' + ''.join(f'<td>{sheet.esc(value)}</td>' for value in (
        part.get('id', ''), part.get('label') or part.get('de') or part.get('id'),
        part.get('role', ''), part.get('func', part.get('attach', '—')))) + '</tr>' for part in parts)
    return ('<div class="table-wrap"><table><thead><tr><th>Teil</th><th>Bezeichnung</th><th>Materialrolle</th><th>Funktion / Verbindung</th>'
            '</tr></thead><tbody>' + rows + '</tbody></table></div>')


def _anchors(document, parts=None):
    ids = None if parts is None else {part['id'] for part in parts}
    items = []
    for name, anchor in document.get('anchors', {}).items():
        if ids is not None and anchor.get('part') not in ids:
            continue
        at = anchor.get('at')
        if at is not None:
            location = 'f/u/x: ' + ' / '.join(f'{float(v):g}' for v in at) + ' mm'
        elif anchor.get('position_m') is not None:
            location = 'x/y/z: ' + ' / '.join(f'{1000*float(v):g}' for v in anchor['position_m']) + ' mm'
        else:
            location = 'Position ausstehend'
        items.append(f'<li><strong>{sheet.esc(name)}</strong><small>{sheet.esc(anchor.get("part", ""))} · {sheet.esc(location)}</small>'
                     f'<small>{sheet.esc(anchor.get("source", anchor.get("note", "")))}</small></li>')
    return '<ul class="anchor-list">' + ''.join(items) + '</ul>' if items else '<p class="note">Keine Anker zugeordnet.</p>'


def build(document, views):
    """Return figure overview plus one print section per declared assembly.

    View keys: front, side_left, back, iso, exploded, idle, ready and
    assembly_<id>. A ready image represents the supplied pose only; this
    composer never silently creates a held weapon or claims pose validation.
    """
    required = ['front', 'side_left', 'side_right', 'back', 'iso', 'exploded', 'idle', 'ready']
    assemblies = list(document.get('assemblies', []))
    known = {assembly['id'] for assembly in assemblies}
    # Undeclared groups remain visible; dropping their parts would hide gaps.
    for part in document.get('parts', []):
        group = part.get('assembly', 'unassigned')
        if group not in known:
            assemblies.append({'id': group, 'de': group, '_undeclared': True})
            known.add(group)
    required += ['assembly_' + assembly['id'] for assembly in assemblies]
    warnings = list(document.get('warnings', []))
    missing = [key for key in required if not views.get(key)]
    if missing:
        warnings.append('Ansichten ausstehend: ' + ', '.join(missing))
    if any(group.get('_undeclared') for group in assemblies):
        warnings.append('Nicht deklarierte Baugruppen wurden aus den Teilezuordnungen ergänzt.')
    if 'Socket_Hand' not in document.get('anchors', {}):
        warnings.append('Socket_Hand fehlt; die Anbindung einer Waffe ist noch offen.')
    poses = document.get('poses', {})
    for pose in ('idle', 'ready'):
        if pose not in poses:
            warnings.append(f'Pose {pose} ist im Modell noch nicht definiert.')
    body = sheet.header(document, 'Figur · Konzeptblatt') + sheet.warnings_html(warnings)
    body += sheet.section('Silhouette & Proportion', '<div class="figure-grid">' + ''.join(
        sheet.panel(views, key, title, size=(960, 960), references=key != 'iso')
        for key, title in (('front', 'Vorn'), ('side_left', 'Seite links'), ('side_right', 'Seite rechts'), ('back', 'Rücken'), ('iso', 'Schrägansicht'))) + '</div>')
    body += sheet.section('Baugruppen & Anker', '<div class="assembly-layout">' +
                          sheet.panel(views, 'exploded', 'Explosionsansicht · entlang der Anker', size=(960, 960)) +
                          '<div>' + _anchors(document) + '</div></div>')
    body += sheet.section('Posen', '<div class="pose-grid">' +
                          sheet.panel(views, 'idle', 'Idle · Ruhepose', size=(960, 960)) +
                          sheet.panel(views, 'ready', 'Ready · Bereitschaft', size=(960, 960)) + '</div>')
    body += sheet.section('Materialfelder', sheet.materials_html(document))
    for assembly in assemblies:
        parts = [part for part in document.get('parts', []) if part.get('assembly', 'unassigned') == assembly['id']]
        body += (f'<section class="assembly" data-assembly="{sheet.esc(assembly["id"])}"><div class="section-head">'
                 f'<h2>{sheet.esc(assembly.get("de", assembly["id"]))}</h2><p>{len(parts)} Bauteile</p></div>'
                 '<div class="assembly-layout">' + sheet.panel(views, 'assembly_' + assembly['id'],
                 assembly.get('de', assembly['id']), size=(960, 960)) + '<div>' + _parts_table(parts) + _anchors(document, parts) + '</div></div></section>')
    body += sheet.section('Bildbeschreibung', sheet.prompts_html(document))
    return sheet.page(document, body)
