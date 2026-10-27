"""Resolved v1 surface recipes over imported meshes, without v1 model code.

Sources: claude/generator/skinraster.py (647e93011f1a1f0b904488245d803b7b45be51e53af2d808f7aea49213acf5f3)
and xl.py (7aae8cba96f11b0a3728f39ab3e6bf246a193283c22e7cfde7dc5f731790c4d0)
in cubeescape-formgen. Equations use the local, provenance-preserving catalog
snapshot. Imported specs already resolve part IDs, dimensions and slot colors;
no old authoring modules, model imports or skin generator are needed here.
World coordinates and all resolved recipe distances are metres.
"""
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

CATALOG = Path(__file__).resolve().parents[1] / 'docs/textures/catalog.json'


@lru_cache(maxsize=1)
def catalog():
    value = json.loads(CATALOG.read_text())
    if value.get('format') != 'cubeescape-design/texture-catalog' or value.get('format_version') != 1:
        raise ValueError('Legacy-Oberflächen benötigen texture-catalog v1')
    return value


def rgb(value):
    return np.array([int(value.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)], float)


def in_polygon(points, polygon):
    """Even/odd containment in the recipe's YZ plane, including concavities."""
    points = np.asarray(points)
    inside = np.zeros(points.shape[:-1], bool)
    for a, b in zip(polygon, polygon[-1:]+polygon[:-1]):
        if a[1] == b[1]:
            continue
        inside ^= ((a[1] > points[..., 1]) != (b[1] > points[..., 1])) & (
            points[..., 0] < (b[0]-a[0])*(points[..., 1]-a[1])/(b[1]-a[1])+a[0])
    return inside


def _hash(value):
    return np.sin(value*12.9898)*43758.5453 % 1.


class Surface:
    def __init__(self, document, skin='standard'):
        self.document = document
        self.parts = {p['id']: p for p in document['parts']}
        spec = document.get('source_spec', {})
        block = spec.get('skin') or {}
        requested = skin.split(':', 1)[1] if skin.startswith('legacy:') else block.get('hero')
        items = block.get('items', [])
        self.recipe = next((item for item in items if item['id'] == requested), None)
        if skin.startswith('legacy:') and self.recipe is None:
            raise ValueError(f'Unbekannter aufgelöster Legacy-Skin: {requested}')
        self.layers = self.recipe.get('layers', []) if self.recipe else []
        variants = self.recipe.get('colors', {}) if self.recipe else {}
        # The original hero uses its source palette ("base"). v1's variant
        # named "standard" is a separate recoloring, not that source palette.
        self.colors = variants.get(skin, variants.get('base', {})) if skin != 'standard' else variants.get('base', {})
        self.material_skin = 'standard' if skin.startswith('legacy:') else skin
        self.surface = document.get('source_geo', {}).get('surface') or {}
        self.textures = spec.get('textures') or {}
        # View selections must not change the physical finish/streak scale.
        source_parts = document.get('source_geo', {}).get('parts', document['parts'])
        vertices = np.asarray([v for p in source_parts if not p.get('sight')
                               for v in p['mesh']['vertices']])
        self.height = float(np.ptp(vertices[:, 2])) if len(vertices) else 1.
        self._catalog = catalog()
        self._finishes = {f['id']: f for f in self._catalog['finishes']}

    def slot(self, slot):
        value = self.colors.get(slot)
        if value is None:
            raise ValueError(f'Legacy-Skin: aufgelöste Slotfarbe fehlt: {slot}')
        return rgb(value['color']), value.get('finish', 'paint')

    def tones(self, color, finish, level, positions, toon):
        """Finish ladder plus a fixed object-space highlight, with no bloom."""
        color = np.asarray(color)
        out = np.broadcast_to(color, np.shape(positions)).copy()
        if finish == 'paint':
            return out*np.asarray(toon)[level]
        description = self._finishes[finish]
        ladder = description['ladder']
        index = 3-int(level)
        step = ladder['steps'][index]
        if step.get('with'):
            out = out*(1-step['amount'])+rgb(step['with'])*step['amount']
        if description.get('streak'):
            streak = self._catalog['wear']['streak']
            # Original model axes length,height,width -> Toolgen -Y,Z,X.
            direction = np.asarray(streak['direction'])[[2, 0, 1]]*[1, -1, 1]
            hit = (np.asarray(positions)@direction/(streak['period_rel_height']*self.height)) % 1 < streak['width_fraction']
            high = ladder['highlight']
            highlight = rgb(high['fixed']) if 'fixed' in high else color*(1-high['amount'])+rgb(high['with'])*high['amount']
            out[hit] = highlight
        return out

    def _material_pattern(self, part, positions, normal):
        texture = part.get('texture') or part.get('toolgen_material')
        patterns = {p['id']: p for p in self._catalog['patterns']}
        x, y, z = np.moveaxis(np.asarray(positions)*1000, -1, 0)
        if texture == 'painted':
            waves = patterns['gloss_gradient']['params']['waves']
            return 1+sum(w['amplitude']*np.cos(2*np.pi*(z if w['axes'] == ['height'] else x-y)/w['wavelength_mm']) for w in waves)
        if texture == 'brushed':
            parameters = patterns['brushed']['params']
            vertices = np.asarray(part['mesh']['vertices'])
            extents = np.ptp(vertices, axis=0)
            axis = (1, 2, 0)[int(np.argmax(extents[[1, 2, 0]]))]
            # Original length,height,width = -worldY,worldZ,worldX.
            # World-Y therefore contributes with a minus sign even when it
            # is a transverse axis (long parts along world X or Z).
            across = [x, -y, z]
            q = sum(across[k] for k in range(3) if k != axis)
            return 1+parameters['amplitude']*sum(w['weight']*np.sin(2*np.pi*q/w['wavelength_mm']+w['phase']) for w in parameters['waves'])
        if texture == 'rubber':
            # Preserve v1's dominant-normal tie order as well as handedness.
            axis = int(np.argmax(np.abs(normal)[[1, 2, 0]]))
            u, v = ([z, x] if axis == 0 else [-y, x] if axis == 1 else [-y, z])
            pattern = patterns['knurl']
            cells = (np.floor((u+v)/pattern['size_mm']) % 2 == 0) & (np.floor((u-v)/pattern['size_mm']) % 2 == 0)
            return 1-pattern['params']['darkening']*cells
        if texture == 'painted_matte':
            pattern = patterns['grain']
            a, b, c = pattern['params']['hash_coefficients']
            size = pattern['size_mm']
            noise = _hash(np.floor(-y/size)*a+np.floor(z/size)*b+np.floor(x/size)*c)
            return 1+pattern['params']['amplitude']*(noise-.5)
        return np.ones(np.shape(positions)[:-1])

    def shade(self, part, base_color, normal, positions, level, toon):
        """Evaluate resolved layers at visible geometry samples, in order."""
        positions = np.asarray(positions)
        if '_legacy_finish' in part:
            if part.get('emissive') and part['_legacy_finish'] == 'paint':
                return np.broadcast_to(base_color, positions.shape).copy()
            return self.tones(base_color, part['_legacy_finish'], level, positions, toon)
        out = np.broadcast_to(base_color, positions.shape).copy()*np.asarray(toon)[level]
        if part.get('emissive'):
            return np.broadcast_to(base_color, positions.shape).copy()
        out *= self._material_pattern(part, positions, normal)[..., None]
        yz = positions[..., 1:]
        for layer in self.layers:
            kind = layer['type']
            if kind not in ('finish', 'side_block', 'bands', 'gradient', 'rings') or part['id'] not in layer.get('parts', []):
                continue
            selection = np.ones(positions.shape[:-1], bool)
            if kind == 'side_block':
                selection &= in_polygon(yz, layer['poly_yz_m'])
            if kind in ('finish', 'side_block'):
                color, finish = self.slot(layer['slot'])
                out[selection] = self.tones(color, finish, level, positions[selection], toon)
            elif kind in ('bands', 'rings'):
                if kind == 'bands':
                    t = positions@np.asarray(layer['dir'])-layer['t0_m']
                    period = layer['period_m'] or layer['width_m']
                    if layer.get('window_yz_m'):
                        selection &= in_polygon(yz, layer['window_yz_m'])
                else:
                    t = np.linalg.norm(yz-np.asarray(layer['center_yz_m']), axis=-1)-layer['r0_m']
                    period = layer['width_m']+layer['gap_m']
                band = np.floor(t/period)
                selection &= (t >= 0) & (t-band*period < layer['width_m']) & (band < layer['count'])
                for index, slot in enumerate(layer['slots']):
                    mask = selection & (band % len(layer['slots']) == index)
                    color, finish = self.slot(slot)
                    out[mask] = self.tones(color, finish, level, positions[mask], toon)
            elif kind == 'gradient':
                t = positions@np.asarray(layer['dir'])
                amount = np.clip((t-layer['t0_m'])/(layer['t1_m']-layer['t0_m']), 0, .9999)
                steps = layer['steps']
                a, _ = self.slot(layer['slots'][0]); b, _ = self.slot(layer['slots'][1])
                index = np.floor(amount*steps).astype(int)
                out = (a+(b-a)*index[..., None]/max(steps-1, 1))*np.asarray(toon)[level]
        return np.clip(out, 0, 255)

    def decorations(self):
        """Flat decals and resolved trim meshes; no mutation of source data."""
        result = []
        def decal(parent, points, normal, color, emissive, name, finish='paint'):
            result.append(dict(id=name, role='decal', color=color,
                emissive=emissive, _surface_parent=parent, _decal_normal=normal,
                _legacy_finish=finish, _annotation=False,
                mesh=dict(vertices=deepcopy(points), faces=[list(range(len(points)))], hard=True)))
        for i, value in enumerate(self.document.get('decals', [])):
            if value['part'] not in self.parts:
                continue
            decal(value['part'], value['polygon_m'], value['normal'], value['color'],
                  value.get('emissive', False), f"{value['part']}/legacy-decal/{i}")
        for li, layer in enumerate(self.layers):
            if layer['type'] == 'glyphs':
                if layer['part'] not in self.parts:
                    continue
                for i, value in enumerate(layer['decals']):
                    color = self.colors[value['slot']]
                    decal(layer['part'], value['points_m'], [1, 0, 0] if value['surface'] == 'left' else [-1, 0, 0],
                          color['color'], color['finish'] == 'neon',
                          f"{layer['part']}/legacy-glyph/{li}-{i}", color['finish'])
            elif layer['type'] == 'trim':
                if layer['attach'] not in self.parts:
                    continue
                value = self.colors[layer['slot']]
                for i, shape in enumerate(layer['parts']):
                    profile = shape['profile_yz_m']; n = len(profile)
                    vertices = [[x, y, z] for x in shape['x_m'] for y, z in profile]
                    faces = [list(reversed(range(n))), list(range(n, 2*n))]
                    faces += [[j, (j+1) % n, (j+1) % n+n, j+n] for j in range(n)]
                    result.append(dict(id=f"{layer['attach']}/legacy-trim/{li}-{i}",
                        label=None, role='metal', color=value['color'],
                        _legacy_finish=value['finish'], _annotation=False,
                        _surface_attach=layer['attach'],
                        mesh=dict(vertices=vertices, faces=faces, hard=True)))
        return result

    def render_parts(self):
        return list(self.document['parts'])+self.decorations()

    @staticmethod
    def parents(render_parts):
        """Map visible decal IDs to their owning geometry ID for Z-tests."""
        ids = {p['id']: i for i, p in enumerate(render_parts)}
        return np.array([ids[p['_surface_parent']] if p.get('_surface_parent') else i
                         for i, p in enumerate(render_parts)]+[-1], dtype=int)

    @staticmethod
    def parent_visible(part, visible_ids, parents, render_parts):
        """No projected decal may paint an unrelated foreground surface."""
        parent = part.get('_surface_parent')
        if parent is None:
            return np.ones(np.shape(visible_ids), bool)
        owner = next(i for i, p in enumerate(render_parts) if p['id'] == parent)
        lookup = np.where(visible_ids >= 0, visible_ids, len(render_parts))
        return parents[lookup] == owner

    def wear(self, colors, geometry_ids, part_ids, positions, levels, render_parts, scale, toon):
        """Wear only geometry boundaries, excluding flat decal boundaries."""
        layers = [l for l in self.layers if l['type'] == 'edge_wear']
        if not layers:
            value = self.surface.get('wear')
            if value:
                ids = [p['id'] for p in render_parts if p.get('texture') in ('painted', 'painted_matte')]
                layers = [dict(parts=ids, width_mm=value['width_m']*1000,
                               coverage=value['coverage'], color=value['bare_metal'])]
        if not layers:
            return colors
        ordinary = np.array([not p.get('_surface_parent') for p in render_parts]+[False])
        flat = np.array([bool(p.get('_surface_parent')) for p in render_parts]+[False])
        lookup = np.where(part_ids >= 0, part_ids, len(render_parts))
        valid = ordinary[lookup] & (part_ids >= 0)
        edges = np.zeros(valid.shape, bool)
        for axis in (0, 1):
            for shift in (-1, 1):
                neighbor = np.roll(geometry_ids, shift, axis)
                neighbor_flat = np.roll(flat[lookup], shift, axis)
                edges |= valid & ~neighbor_flat & (geometry_ids != neighbor)
        if not edges.any():
            return colors
        distance = ndimage.distance_transform_edt(~edges)
        out = colors.copy()
        x, y, z = np.moveaxis(positions, -1, 0)
        cell_widths = self._catalog['wear']['cell_widths']
        low, high = self._catalog['wear']['width_variation']
        for layer in layers:
            ids = [i for i, p in enumerate(render_parts) if p['id'] in layer['parts']]
            mask = valid & np.isin(part_ids, ids)
            width = layer['width_mm']/1000
            if width <= 0:
                continue
            cell = width*cell_widths
            # Same original-coordinate hash used by skinraster.py.
            noise = _hash(np.floor(-y/cell)*.37+np.floor(z/cell)*1.91+np.floor(x/cell)*3.7)
            mask &= (distance < width*scale*(low+(high-low)*noise)) & (noise > 1-layer['coverage'])
            out[mask] = rgb(layer['color'])*np.asarray(toon)[levels[mask], None]
        return np.clip(out, 0, 255)


def resolve(document, skin='standard'):
    """Native kit documents keep their existing raster path unchanged."""
    source = document.get('source_geo', {})
    if source.get('format') != 'cubeescape-design/geometry-spec':
        return None
    return Surface(document, skin)
