"""Bilingual, geometry-grounded presentation instructions; no form invention."""
from __future__ import annotations
import copy
from pathlib import Path
from .spec import dimensions
from .versions import PROMPTS as VERSION

ROLE_NAMES = {
    'shell': ('lackiertes Gehäuse', 'painted housing'), 'graphite': ('Griffpolymer', 'grip polymer'),
    'metal': ('Funktionsmetall', 'functional metal'), 'dark_metal': ('dunkles Metall', 'dark metal'),
    'rubber': ('Gummi', 'rubber'), 'accent': ('Akzent', 'accent'), 'energy': ('Leuchtfläche', 'emissive surface'),
    'trim': ('Metallzierkante', 'metal trim'), 'anodized': ('eloxiertes Metall', 'anodized metal'),
    'brass': ('Messing', 'brass'), 'string': ('Sehne', 'string'), 'decal': ('Markierung', 'marking'),
}


def _role(role, lang):
    if role.startswith('glass'):
        return 'Glas' if lang == 'de' else 'glass'
    if role.startswith('reticle_'):
        return 'Fadenkreuz' if lang == 'de' else 'reticle'
    return ROLE_NAMES.get(role, (role, role))[lang == 'en']


def _source(document):
    source=copy.deepcopy(document.get('source',{}))
    root=Path(__file__).resolve().parents[1]
    if source.get('path'):
        path=Path(source['path'])
        if path.is_absolute():
            source['path']=str(path.relative_to(root)) if path.is_relative_to(root) else path.name
    return source


def build(document):
    """Describe actual labels, roles and measured bounds; qualify design requests."""
    info = document['info']
    dims = dimensions(document['parts'])
    roles = sorted({p['role'] for p in document['parts']})
    texts = {}
    for lang in ('de', 'en'):
        english = lang == 'en'
        name = info.get('name_en', info.get('name_de', info['id'])) if english else info.get('name_de', info['id'])
        labels = [(p.get('en') or p.get('label') or p['id']) if english else (p.get('label') or p['id']) for p in document['parts']]
        measures = ' × '.join(f'{dims[k]:.6f}' for k in ('length', 'height', 'width'))
        if english:
            text = (f"{info['id']} — {name}. Reproduce the supplied evaluated mesh and its proportions. "
                    f"Measured length × height × width: {measures} m (mesh AABB). "
                    f"Components (source labels retained where no translation is supplied): {'; '.join(labels)}. "
                    f"Material roles: {', '.join(_role(r, lang) for r in roles)}. "
                    "Presentation vocabulary from the master prompt: industrial science fiction, legible hard-surface contours, "
                    "clear component separation. These are presentation instructions; preserve the supplied shapes and anchors. "
                    "Use neutral mid-gray background, no bloom or motion blur. Do not add geometry or infer mechanisms from labels. "
                    "Colors come from skins.toml or the verified imported specification. Do not conceal geometry limitations.")
        else:
            text = (f"{info['id']} — {name}. Das mitgelieferte ausgewertete Netz und seine Proportionen wiedergeben. "
                    f"Gemessene Länge × Höhe × Breite: {measures} m (Netz-AABB). "
                    f"Bauteile: {'; '.join(labels)}. Materialrollen: {', '.join(_role(r, lang) for r in roles)}. "
                    "Darstellungsvokabular aus dem Masterprompt: Industrial Science-Fiction, erkennbare Hard-Surface-Konturen, "
                    "klare Bauteiltrennung. Das sind Darstellungsvorgaben; vorhandene Formen und Anker beibehalten. "
                    "Neutraler mittelgrauer Hintergrund, kein Bloom oder Bewegungsunschärfe. Keine Geometrie ergänzen oder "
                    "Mechanik aus Bezeichnungen ableiten. Farben aus skins.toml oder der geprüften Importspezifikation. "
                    "Geometrieeinschränkungen nicht verdecken.")
        if document.get('warnings'):
            text += (' Source geometry warnings: ' if english else ' Warnungen der Quellgeometrie: ') + '; '.join(document['warnings'])
        texts[lang] = text
    return dict(format='cubeescape-formgen/prompts', format_version=1, generator_version=VERSION,
                id=info['id'], **texts, dimensions_m=dims,
                source=_source(document),
                vocabulary_source='cubeescape-formgen/docs/masterprompt.md §8–9',
                warnings=list(document.get('warnings', [])))
