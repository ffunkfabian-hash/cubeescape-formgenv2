"""Orthographic mesh rasterizer adapted from Formgen v1 (see docs/raster.md).

No model construction, Blender or eng dependency. Coordinates are metres, +Z up,
-Y forward. Projection scale is always output pixels per metre, before SS=2.
"""
from __future__ import annotations

import math
from pathlib import Path
import tomllib

import numpy as np
from PIL import Image
from scipy import ndimage

from .versions import RASTER as VERSION
from . import legacy_surface

SS = 2
SOURCE_SHA256 = '7ab4863e8eb4e4fe21fdfdf5fb3cf84dc0b0075b29cd010d3b0b47daea240057'
SKINS_PATH = Path(__file__).resolve().parents[1] / 'skins.toml'
ORTHOS = ('side_left', 'side_right', 'front', 'back', 'top', 'bottom')
VIEWS = ORTHOS + ('iso',)
_DIRECTIONS = {
    'side_left': (1, 0, 0), 'side_right': (-1, 0, 0),
    'front': (0, -1, 0), 'back': (0, 1, 0),
    'top': (0, 0, 1), 'bottom': (0, 0, -1), 'iso': (1, -1.5, .85),
}
_ALIASES = {'left': 'side_left', 'right': 'side_right', 'side': 'side_left',
            'rear': 'back', 'oblique': 'iso', 'threequarter': 'iso'}
# Studio ambient keeps dark kit roles readable without altering their palette.
TOON = np.array([.72, .82, .92, 1.0])


def camera(view='side_left'):
    """Rows: screen right, screen up, towards camera; orthonormal world basis."""
    view = _ALIASES.get(view, view)
    if view not in _DIRECTIONS:
        raise ValueError(f'Unbekannte Ansicht: {view}')
    toward = np.array(_DIRECTIONS[view], dtype=float)
    toward /= np.linalg.norm(toward)
    # Keep weapon forward (-Y) horizontal and left in both plan views.
    up = np.array({'top': [-1., 0., 0.], 'bottom': [1., 0., 0.]}.get(view, [0., 0., 1.]))
    right = np.cross(up, toward)
    right /= np.linalg.norm(right)
    return np.array([right, np.cross(toward, right), toward])


def _size(width, height):
    if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in (width, height)):
        raise ValueError('Breite und Höhe müssen positive ganze Zahlen sein')


def _center(center):
    center = np.asarray(center, dtype=float)
    if center.shape != (3,) or not np.isfinite(center).all():
        raise ValueError('center muss drei endliche Weltkoordinaten in Metern enthalten')
    return center


def project(points, view='side_left', width=960, height=640, scale=1000., center=(0, 0, 0)):
    """Return Nx3 screen x/y in pixels and depth in metres (larger = nearer).

    Accepts a single xyz point as well, returning a length-three array. Use the
    exact framing returned by render.info['framing'] for annotation alignment.
    """
    _size(width, height)
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError('scale muss positiv und endlich sein (px/m)')
    p = np.asarray(points, dtype=float)
    if p.ndim not in (1, 2) or p.shape[-1] != 3 or not np.isfinite(p).all():
        raise ValueError('points müssen endliche xyz-Weltkoordinaten sein')
    q = (p - _center(center)) @ camera(view).T
    q[..., 0] = q[..., 0] * scale + width / 2
    q[..., 1] = height / 2 - q[..., 1] * scale
    return q


def _vertices(document):
    arrays = []
    for part in document.get('parts', []):
        mesh = part.get('mesh')
        if mesh is None:
            raise ValueError(f"Teil {part.get('id')}: ausgewertetes mesh fehlt")
        v = np.asarray(mesh['vertices'], dtype=float)
        if v.size:
            if v.ndim != 2 or v.shape[1] != 3 or not np.isfinite(v).all():
                raise ValueError('Ungültige Netzkoordinaten')
            arrays.append(v)
    if not arrays:
        raise ValueError('Dokument enthält keine Netzpunkte')
    return np.concatenate(arrays)


def framing(document, views=ORTHOS, width=960, height=640, padding=.08, center=None):
    """Shared world center and scale (px/m) fitting every requested view.

    Passing this result to every render preserves physical size across views.
    Auto-fit of one render alone does not promise equal scale across views.
    """
    _size(width, height)
    if not 0 <= padding < .5 or not views:
        raise ValueError('padding muss in [0,.5) liegen, views darf nicht leer sein')
    if isinstance(views, str):
        views = [views]
    v = _vertices(document)
    c = (v.min(axis=0) + v.max(axis=0)) / 2 if center is None else _center(center)
    scales = []
    for view in views:
        q = (v-c) @ camera(view).T
        extent = 2*np.max(np.abs(q[:, :2]), axis=0)
        scales.extend([width*(1-2*padding)/max(extent[0], 1e-9),
                       height*(1-2*padding)/max(extent[1], 1e-9)])
    return {'scale': float(min(scales)), 'center': c.tolist()}


def palette():
    with SKINS_PATH.open('rb') as stream:
        return tomllib.load(stream)


def _rgb(value):
    if isinstance(value, str):
        value = value.removeprefix('#')
        if len(value) != 6:
            raise ValueError('Farbe muss sechs Hex-Ziffern enthalten')
        return np.array([int(value[i:i+2], 16) for i in (0, 2, 4)], dtype=float)
    value = np.asarray(value, dtype=float)
    if value.shape != (3,) or not np.isfinite(value).all():
        raise ValueError('Ungültige RGB-Farbe')
    return value * 255 if value.max() <= 1 else value


def material(part, skin='standard', data=None):
    """Resolve TOML roles/skin plus explicitly preserved imported Geo colors."""
    data = palette() if data is None else data
    if skin not in data['skins']:
        raise ValueError(f'Unbekannter Skin: {skin}')
    role = part.get('role', 'shell')
    if role not in data['roles'] and 'color' not in part:
        raise ValueError(f'Unbekannte Materialrolle: {role}')
    m = dict(data['roles'].get(role, data['roles']['shell']))
    style = data['skins'][skin]
    if 'color' in part:
        m['color'] = part['color']
    m['color'] = style.get('roles', {}).get(role, m['color'])
    if 'alpha' in part:
        m['alpha'] = part['alpha']
    if part.get('glass') and 'alpha' not in part:
        m['alpha'] = data['roles']['glass'].get('alpha', .12)
    m['unlit'] = bool(m.get('emit', 0) or m.get('emit_only') or part.get('emissive') or part.get('emit'))
    if style.get('metal_shell') and role == 'shell':
        m.update(metal=1., rough=.3)
    m['rgb'] = _rgb(m['color'])
    m['role'] = role
    m['style'] = style
    if not 0 <= float(m.get('alpha', 1.)) <= 1:
        raise ValueError('Material-alpha muss zwischen 0 und 1 liegen')
    return m


def _triangles(vertices, face):
    """Ear-clip planar simple polygon, preserving concave silhouettes."""
    if len(face) < 3 or any(i < 0 or i >= len(vertices) for i in face):
        raise ValueError('Ungültige Flächenindizes')
    if len(face) == 3:
        return [face]
    pts = vertices[face]
    normal = np.sum(np.cross(pts, np.roll(pts, -1, axis=0)), axis=0)
    uv = np.delete(pts, np.argmax(np.abs(normal)), axis=1)
    area = np.sum(uv[:, 0]*np.roll(uv[:, 1], -1)-uv[:, 1]*np.roll(uv[:, 0], -1))
    if abs(area) < 1e-20:
        return []
    sign = 1 if area > 0 else -1
    ids = list(range(len(face)))
    result = []
    def cross(a, b):
        return a[0]*b[1]-a[1]*b[0]
    while len(ids) > 3:
        for j, b in enumerate(ids):
            a, c = ids[j-1], ids[(j+1) % len(ids)]
            if sign*cross(uv[b]-uv[a], uv[c]-uv[b]) <= 1e-16:
                continue
            inside = False
            for k in ids:
                if k in (a, b, c):
                    continue
                if all(sign*cross(uv[t]-uv[s], uv[k]-uv[s]) >= -1e-16
                       for s, t in ((a, b), (b, c), (c, a))):
                    inside = True
                    break
            if not inside:
                result.append([face[a], face[b], face[c]])
                ids.pop(j)
                break
        else:
            raise ValueError('Nicht triangulierbare Fläche: nicht einfach/planar oder doppelte Punkte')
    result.append([face[k] for k in ids])
    return result


def _face_groups(mesh, angle_degrees=25.):
    """Join edge-adjacent faces below the feature angle, never across parts.

    Coordinate welding also handles triangle soups whose shared corner has a
    separate vertex index. One source polygon keeps one ID after triangulation.
    """
    vertices = np.asarray(mesh['vertices'], dtype=float)
    faces = mesh['faces']
    parent = list(range(len(faces)))
    normals = []
    edges = {}
    corner_ids = {}
    welded = []
    for vertex in vertices:
        key = tuple(np.round(vertex, 9))
        welded.append(corner_ids.setdefault(key, len(corner_ids)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def join(a, b):
        parent[root(b)] = root(a)
    for fi, face in enumerate(faces):
        points = vertices[face]
        normal = np.sum(np.cross(points, np.roll(points, -1, axis=0)), axis=0)
        length = np.linalg.norm(normal)
        normals.append(normal/length if length > 1e-16 else np.zeros(3))
        for a, b in zip(face, list(face[1:])+[face[0]]):
            edge = tuple(sorted((welded[a], welded[b])))
            if edge[0] != edge[1]:
                edges.setdefault(edge, []).append(fi)
    threshold = math.cos(math.radians(angle_degrees))
    for adjacent in edges.values():
        # Non-manifold edges are deliberately not smoothed across.
        if len(adjacent) == 2:
            a, b = adjacent
            if float(normals[a] @ normals[b]) > threshold:
                join(a, b)
    hard = mesh.get('hard', True)
    soft = [i for i in range(len(faces))
            if not (hard[i] if isinstance(hard, (list, tuple)) else hard)]
    for i in soft[1:]:
        join(soft[0], i)
    return [root(i) for i in range(len(faces))]


def _fragments(screen, world, width, height):
    a, b, c = screen
    den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
    if abs(den) < 1e-10:
        return None
    lo = np.maximum(np.floor(screen[:, :2].min(axis=0)).astype(int), 0)
    hi = np.minimum(np.ceil(screen[:, :2].max(axis=0)).astype(int), [width, height])
    x0, y0 = lo
    x1, y1 = hi
    if x1 <= x0 or y1 <= y0:
        return None
    yy, xx = np.mgrid[y0:y1, x0:x1]
    xx, yy = xx+.5, yy+.5
    u = ((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
    v = ((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
    weights = np.stack([u, v, 1-u-v], axis=-1)
    hit = (weights >= -1e-8).all(axis=-1)
    return (slice(y0, y1), slice(x0, x1)), hit, weights @ screen[:, 2], weights @ world


def _shade(mat, normal, world):
    rgb = np.broadcast_to(mat['rgb'], world.shape).copy()
    if mat['unlit']:
        return rgb
    light = np.array([-.4, -.6, 1.])
    light /= np.linalg.norm(light)
    diffuse = max(0., float(normal @ light))
    # Four lighting bands; metallic roles reach the brightest band sooner.
    level = min(3, int(np.clip(diffuse + mat.get('metal', 0)*.10, 0, .9999)*4))
    rgb *= TOON[level]
    style, role = mat['style'], mat['role']
    # World/object coordinates, never image coordinates: pattern stays attached.
    x, y, z = np.moveaxis(world, -1, 0)
    wave = np.sin(71*x+13*np.sin(43*y))+np.sin(57*z-29*y)
    if style.get('pattern') and role == 'shell':
        colors = np.array([_rgb(c) for c in style['pattern']])
        idx = np.clip(((wave+2)/4*len(colors)).astype(int), 0, len(colors)-1)
        rgb = colors[idx]*TOON[level]
    grain = np.sin(1703*x+1031*y+1279*z)*np.sin(911*x-1741*y+613*z)
    amplitude = .008 + .025*float(mat.get('rough', .5))
    if role in ('rubber', 'graphite'):
        amplitude *= 1.5
    rgb *= (1+grain*amplitude)[..., None]
    grime = float(style.get('grime', 0))
    wear = float(style.get('wear', 1))
    rgb *= (1-np.maximum(0., wave-1.2)*.055*grime)[..., None]
    rgb += (np.maximum(0., grain-.88)*7*wear)[..., None]
    return np.clip(rgb, 0, 255)


def _edges(ids, split=False):
    foreground = ids >= 0
    pad = np.pad(ids, 1, constant_values=-1)
    inner = np.zeros_like(foreground)
    silhouette = np.zeros_like(foreground)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        other = pad[1+dy:1+dy+ids.shape[0], 1+dx:1+dx+ids.shape[1]]
        inner |= foreground & (other >= 0) & (ids != other)
        silhouette |= foreground & (other < 0)
    # Stay inside geometry: no outside glow or opaque pixels from a contour.
    silhouette = ndimage.binary_dilation(silhouette, iterations=SS-1) & foreground
    inner &= ~silhouette
    return (inner, silhouette) if split else inner | silhouette


def render(document, view='side_left', width=960, height=640, skin='standard', bg='mid', scale=None, center=None):
    """Render an evaluated mesh document. Returned PIL image contains framing,
    visible label anchors and bounding boxes in .info (output-pixel units).

    image.coverage_mask is a same-sized PIL L image with geometric sample
    coverage (0..255), including visible glass regardless of its opacity. It
    comes from the final part buffer, not color, background or contour pixels.
    It is separate from JSON-serializable .info and can be saved as a PNG.
    """
    frame = framing(document, [view], width, height, center=center)
    if scale is not None:
        if not np.isfinite(scale) or scale <= 0:
            raise ValueError('scale muss positiv und endlich sein (px/m)')
        frame['scale'] = float(scale)
    data = palette()
    surface = legacy_surface.resolve(document, skin)
    render_parts = surface.render_parts() if surface else list(document['parts'])
    for part in document['parts']:
        for index, mesh in enumerate(part.get('decal_meshes', [])):
            render_parts.append({'id': f"{part['id']}/decal/{index}",
                                 'role': mesh.get('role', 'graphite'),
                                 'mesh': mesh, '_annotation': False})
    materials = [material(p, surface.material_skin if surface else skin, data) for p in render_parts]
    parents = surface.parents(render_parts) if surface else None
    w, h = width*SS, height*SS
    zbuf = np.full((h, w), -np.inf)
    ids = np.full((h, w), -1, dtype=np.int32)
    parts = np.full((h, w), -1, dtype=np.int32)
    rgba = np.zeros((h, w, 4), dtype=np.float32)
    if bg is not None and bg != 'transparent':
        rgba[..., :3] = _rgb(data['render']['background_mid'] if bg == 'mid' else bg)
        rgba[..., 3] = 255
    if surface:
        positions = np.zeros((h, w, 3), dtype=np.float32)
        normals = np.zeros((h, w, 3), dtype=np.float32)
        levels = np.zeros((h, w), dtype=np.uint8)
    transparent = []
    next_id = 0
    for pi, (part, mat) in enumerate(zip(render_parts, materials)):
        decal_normal = None
        if surface and part.get('_surface_parent'):
            decal_normal = np.asarray(part['_decal_normal'], dtype=float)
            decal_normal /= np.linalg.norm(decal_normal)
            if decal_normal @ camera(view)[2] <= 1e-4:
                continue
        mesh = part['mesh']
        vertices = np.asarray(mesh['vertices'], dtype=float)
        if not len(vertices):
            continue
        screen = project(vertices, view, w, h, frame['scale']*SS, frame['center'])
        alpha = float(mat.get('alpha', 1.))
        if alpha == 0:
            continue
        glass_z = np.full((h, w), -np.inf) if alpha < 1 else None
        glass_rgb = np.zeros((h, w, 3), dtype=np.float32) if alpha < 1 else None
        groups = _face_groups(mesh)
        face_ids = {group: next_id+i for i, group in enumerate(sorted(set(groups)))}
        next_id += len(face_ids)
        for fi, face in enumerate(mesh['faces']):
            tris = _triangles(vertices, face)
            for tri in tris:
                world = vertices[tri]
                normal = np.cross(world[1]-world[0], world[2]-world[0])
                length = np.linalg.norm(normal)
                if length < 1e-16:
                    continue
                normal /= length
                # Double-sided surfaces retain the same visible-side light response.
                if normal @ camera(view)[2] < 0:
                    normal = -normal
                fid = face_ids[groups[fi]]
                fragments = _fragments(screen[tri], world, w, h)
                if fragments is None:
                    continue
                sl, hit, depth, position = fragments
                target = glass_z if alpha < 1 else zbuf
                ok = hit & (depth >= target[sl]-1e-9)
                if decal_normal is not None:
                    ok &= surface.parent_visible(part, parts[sl], parents, render_parts)
                    # New v2 protection: a decal must face its visible parent
                    # within 60 degrees, as well as face the camera.
                    ok &= (normals[sl] @ decal_normal) > .5
                if not ok.any():
                    continue
                if decal_normal is None:
                    target[sl][ok] = depth[ok]
                if surface:
                    light = np.array([-.4, -.6, 1.])
                    light /= np.linalg.norm(light)
                    diffuse = max(0., float(normal @ light))
                    level = 3 if mat['unlit'] else min(3, int(np.clip(
                        diffuse + mat.get('metal', 0)*.10, 0, .9999)*4))
                    color = surface.shade(part, mat['rgb'], normal, position[ok], level, TOON)
                else:
                    color = _shade(mat, normal, position[ok])
                if alpha < 1:
                    glass_rgb[sl][ok] = color
                else:
                    rgba[sl][..., :3][ok] = color
                    rgba[sl][..., 3][ok] = 255
                    if decal_normal is None:
                        ids[sl][ok] = fid
                        if surface:
                            positions[sl][ok] = position[ok]
                            normals[sl][ok] = normal
                            levels[sl][ok] = level
                    parts[sl][ok] = pi
        if alpha < 1:
            transparent.append((glass_z, glass_rgb, alpha, pi))
    if surface:
        rgba[..., :3] = surface.wear(rgba[..., :3], ids, parts, positions,
                                    levels, render_parts, frame['scale']*SS, TOON)
    inner, silhouette = _edges(ids, split=True)
    line = inner | silhouette
    outline = _rgb(data['render']['outline'])
    # Dark-on-dark outlines disappear. Lift only interior edges, deriving the
    # edge tint from the visible material and the existing TOML outline color.
    dark_inner = inner & (np.max(rgba[..., :3], axis=-1) < 64)
    rgba[dark_inner, :3] = np.clip(rgba[dark_inner, :3]*1.8 + outline*.35, 0, 255)
    rgba[line & ~dark_inner, :3] = outline
    # Nearest surface per transparent part. Composite per-pixel back to front,
    # including crossing glass parts; opaque Z rejects hidden glass fragments.
    if transparent:
        depths = np.stack([g[0] for g in transparent])
        order = np.argsort(depths, axis=0)
        for rank in range(len(transparent)):
            selected = order[rank]
            for gi, (depth, color, alpha, pi) in enumerate(transparent):
                ok = (selected == gi) & np.isfinite(depth) & (depth >= zbuf-1e-9)
                if not ok.any():
                    continue
                a = rgba[ok, 3]/255
                out_a = alpha+a*(1-alpha)
                rgba[ok, :3] = (color[ok]*alpha+rgba[ok, :3]*(a*(1-alpha))[:, None])/out_a[:, None]
                rgba[ok, 3] = out_a*255
                parts[ok] = pi
    annotation_parts = parents[np.where(parts >= 0, parts, len(render_parts))] if surface else parts
    anchors, boxes = {}, {}
    for pi, part in enumerate(render_parts):
        if not part.get('_annotation', True):
            continue
        label = part.get('label') or part['id']
        visible = annotation_parts == pi
        if not visible.any():
            continue
        yy, xx = np.nonzero(visible)
        boxes[label] = [float(xx.min()/SS), float(yy.min()/SS), float((xx.max()+1)/SS), float((yy.max()+1)/SS)]
        eligible = visible & ~line
        if eligible.any():
            yy, xx = np.nonzero(eligible)
        nearest = np.argmin((xx-xx.mean())**2+(yy-yy.mean())**2)
        anchors[label] = [float((xx[nearest]+.5)/SS), float((yy[nearest]+.5)/SS)]
    image = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8)).resize((width, height), Image.Resampling.LANCZOS)
    # BOX averages the exact subpixel coverage without Lanczos ringing outside
    # the silhouette. Keep glass coverage separate from composited opacity.
    image.coverage_mask = Image.fromarray((parts >= 0).astype(np.uint8)*255).resize(
        (width, height), Image.Resampling.BOX)
    image.info.update(framing=frame, view=view, skin=skin, anchors=anchors, boxes=boxes,
                      raster_version=VERSION, supersampling=SS)
    return image
