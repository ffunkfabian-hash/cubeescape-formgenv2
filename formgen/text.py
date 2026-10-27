"""Bfont contours and kit text geometry; static JSON only at runtime.

Supported layout: one baseline, default spacing, ASCII+Latin1, LEFT/CENTER/RIGHT.
Source equations are independently implemented; no Blender runtime/imports.
"""
from functools import lru_cache
import json
from pathlib import Path
import numpy as np
from formgen import geom

FONT_PATH = Path(__file__).resolve().parents[1]/'docs/fonts/bfont-contours.json'


@lru_cache(maxsize=1)
def _decode_font(raw):
    data=json.loads(raw)
    if data.get('format') != 'cubeescape-formgen/font-outline' or data.get('format_version') != 1:
        raise geom.GeometryError('Ungültige statische Schriftkonturen')
    return data


def font_data(path=None):
    # Key by actual bytes: long-lived processes cannot reuse an old resource.
    return _decode_font(Path(FONT_PATH if path is None else path).read_bytes())


def flatten(glyph, resolution=12):
    if not isinstance(resolution,int) or isinstance(resolution,bool) or resolution < 1:
        raise geom.GeometryError('Textauflösung muss eine positive ganze Zahl sein')
    contours=[]
    for commands in glyph['contours']:
        points=[]; current=None
        for command in commands:
            kind=command[0]; operands=np.asarray(command[1:],float)
            if kind=='M':
                if points: raise geom.GeometryError('Mehrere Startpunkte in einer Schriftkontur')
                current=operands[0];points.append(current)
            elif kind=='L':
                current=operands[0];points.append(current)
            elif kind in ('Q','C'):
                t=np.arange(1,resolution+1,dtype=float)[:,None]/resolution
                if kind=='Q':
                    sample=(1-t)**2*current+2*(1-t)*t*operands[0]+t*t*operands[1]
                else:
                    sample=(1-t)**3*current+3*(1-t)**2*t*operands[0]+3*(1-t)*t*t*operands[1]+t**3*operands[2]
                points.extend(sample);current=operands[-1]
            else:raise geom.GeometryError('Unbekannter Schriftkonturbefehl '+kind)
        points=np.asarray(points)
        keep=np.r_[True,np.linalg.norm(np.diff(points,axis=0),axis=1)>1e-10]
        points=points[keep]
        if len(points)>1 and np.linalg.norm(points[-1]-points[0])<1e-10:points=points[:-1]
        if len(points)>=3 and abs(geom._area(points))>1e-10:contours.append(points)
    return contours


def layout(part, data=None):
    """Return font-unit contours, total advance and metre scale; origin baseline."""
    data=font_data() if data is None else data
    text=part['text'];align=part.get('align','LEFT')
    if align not in ('LEFT','CENTER','RIGHT'):
        raise geom.GeometryError('Textausrichtung muss LEFT, CENTER oder RIGHT sein')
    glyphs=[]
    for char in text:
        glyph=data['glyphs'].get(str(ord(char)))
        if glyph is None:
            raise geom.GeometryError(f'Zeichen U+{ord(char):04X} nicht in statischer Bfont-Ressource')
        glyphs.append(glyph)
    width=sum(glyph['advance'] for glyph in glyphs)
    cursor=width*{'LEFT':0.,'CENTER':-.5,'RIGHT':-1.}[align]
    contours=[]
    for glyph in glyphs:
        contours.extend(points+[cursor,0] for points in flatten(glyph,part.get('resolution',12)))
        cursor+=glyph['advance']
    scale=float(part['size'])/1000*data['metadata']['scale']
    if not np.isfinite(scale) or scale<=0:
        raise geom.GeometryError('Textgröße muss positiv und endlich sein')
    return contours,width,scale


def text_mesh(part, data=None):
    """Same kit axes and symmetric ±depth extrusion as the source Curve FONT."""
    if geom._manifold is None:
        raise geom.GeometryError('Echte Schriftkonturen benötigen vorhandenes manifold3d')
    contours,_,scale=layout(part,data)
    if not contours:
        raise geom.GeometryError('Text enthält keine sichtbaren Schriftkonturen')
    side=part.get('side',1)
    if side not in (-1,0,1):raise geom.GeometryError('Textseite muss -1, 0 oder 1 sein')
    depth=float(part.get('depth',.15))/1000
    if not np.isfinite(depth) or depth<0:
        raise geom.GeometryError('Textextrusion muss endlich und nichtnegativ sein')
    section=geom._manifold.CrossSection(contours,geom._manifold.FillRule.NonZero)
    if section.is_empty():raise geom.GeometryError('Schriftkonturen ergeben keine Fläche')
    if depth:
        solid=section.extrude(2*depth/scale).translate((0,0,-depth/scale))
        vertices,faces=geom._from_manifold(solid)
        vertices=np.asarray(vertices)*scale
    else:
        polygons=section.to_polygons()
        faces=np.asarray(geom._manifold.triangulate(polygons),int).tolist()
        xy=np.concatenate(polygons)*scale
        vertices=np.column_stack([xy,np.zeros(len(xy))])
    basis=np.array([[0,0,side],[side,0,0],[0,1,0]],float) if side else np.array([[0,1,0],[-1,0,0],[0,0,1]],float)
    origin=np.asarray(geom.to_xyz((part['f'],part['u'],part.get('x',0))))
    return (vertices@basis.T+origin).tolist(),faces
