"""Pure analytical font contracts; no Blender, raster or repository writes."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from collections import Counter
import numpy as np
from formgen import geom


from formgen import text
DATA=text.font_data()


def shape(string,**extra):
 return dict(text=string,size=5,f=20,u=30,x=40,depth=.12,**extra)


def topology(v,f):
 edges=Counter(tuple(sorted((a,b))) for face in f for a,b in zip(face,face[1:]+face[:1]))
 return edges,len(v)-len(edges)+len(f)


def outline_bounds(glyph):
    """Exact polynomial extrema for analytical comparison to FT_Outline_Get_BBox."""
    extrema=[];current=None
    for commands in glyph['contours']:
        for command in commands:
            k=command[0];operands=np.asarray(command[1:],float)
            if k in ('M','L'):
                current=operands[0];extrema.append(current);continue
            controls=np.vstack([current,operands]);n=len(controls)-1
            candidates={0.,1.}
            for axis in range(2):
                p=controls[:,axis]
                coefficients=[p[0]-2*p[1]+p[2],p[1]-p[0]] if n==2 else [-p[0]+3*p[1]-3*p[2]+p[3],2*(p[0]-2*p[1]+p[2]),p[1]-p[0]]
                for root in np.roots(np.trim_zeros(coefficients,'f')):
                    if np.isreal(root) and 0<float(np.real(root))<1:candidates.add(float(np.real(root)))
            for t in candidates:
                if n==2:extrema.append((1-t)**2*controls[0]+2*(1-t)*t*controls[1]+t*t*controls[2])
                else:extrema.append((1-t)**3*controls[0]+3*(1-t)**2*t*controls[1]+3*(1-t)*t*t*controls[2]+t**3*controls[3])
            current=operands[-1]
    if not extrema:return np.zeros(4)
    points=np.array(extrema)
    return np.r_[points.min(axis=0),points.max(axis=0)]


class TextMeshTests(unittest.TestCase):
 def assertSolid(self,v,f):
  mesh=np.asarray(v)
  edges,_=topology(v,f)
  self.assertTrue(all(c==2 for c in edges.values()))
  direction=Counter((a,b) for face in f for a,b in zip(face,face[1:]+face[:1]))
  self.assertTrue(all(direction[a,b]==direction[b,a] for a,b in direction))
  self.assertGreater(geom._volume(v,f),0)
  tri=mesh[np.asarray(f)]
  area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)
  self.assertTrue(np.all(area>1e-16),area.min())
  self.assertEqual(str(geom._as_manifold(v,f).status()),'Error.NoError')

 def test_resource_provenance_and_supported_charset(self):
  self.assertEqual(DATA['source']['sha256'],'a33954fdab9fb09b9d308cb7f970518293128922ffc523c0a22b3b314a9a56c6')
  self.assertEqual(DATA['format'],'cubeescape-formgen/font-outline')
  self.assertEqual(DATA['format_version'],1)
  self.assertEqual(set(map(int,DATA['glyphs'])),set(range(32,127))|set(range(160,256)))
  self.assertEqual(DATA['metadata']['scale'],.001)
  self.assertEqual(DATA['metadata']['postscript_info']['notice'],None)

 def test_exact_bezier_extrema_match_freetype_bounds_all_glyphs(self):
  for code,glyph in DATA['glyphs'].items():
   with self.subTest(code=code):
    analytic=outline_bounds(glyph)
    self.assertTrue(np.all(np.abs(analytic-np.array(glyph['bounds_high_precision']))<.002),(chr(int(code)),analytic,glyph['bounds_high_precision']))

 def test_known_counter_holes_B_A_R_0_and_no_hole_S(self):
  for string,holes in (('B',2),('A',1),('R',1),('0',1),('S',0)):
   with self.subTest(string=string):
    v,f=text.text_mesh(shape(string));self.assertSolid(v,f)
    components=list(geom._mesh_components(v,f));self.assertEqual(len(components),1)
    self.assertEqual(topology(v,f)[1],2-2*holes)

 def test_every_visible_latin1_ascii_glyph_is_closed_valid_and_nonzero(self):
  for code,glyph in DATA['glyphs'].items():
   if not glyph['contours']:continue
   with self.subTest(code=code,char=chr(int(code))):self.assertSolid(*text.text_mesh(shape(chr(int(code)))))

 def test_real_pilot_text_and_symmetric_depth_independent_of_size(self):
  p=shape('BASIC  AR-01')
  v,f=text.text_mesh(p);self.assertSolid(v,f);a=np.asarray(v)
  np.testing.assert_allclose([a[:,0].min(),a[:,0].max()],[.04-.00012,.04+.00012],atol=1e-12)
  enlarged=dict(p,size=10);b,bf=text.text_mesh(enlarged)
  self.assertAlmostEqual(geom._volume(b,bf)/geom._volume(v,f),4,places=8)
  np.testing.assert_allclose(np.ptp(b,axis=0)[0],.00024,atol=1e-12)

 def test_advances_spaces_and_center_right_use_total_advance(self):
  p=shape(' A  R ');before=copy.deepcopy(DATA)
  contours,width,scale=text.layout(p)
  expected=sum(DATA['glyphs'][str(ord(c))]['advance'] for c in p['text'])
  self.assertEqual(width,expected)
  v,f=text.text_mesh(p)
  for align,factor in (('CENTER',-.5),('RIGHT',-1)):
   other,of=text.text_mesh(dict(p,align=align))
   np.testing.assert_allclose(np.asarray(other)-np.asarray(v),np.broadcast_to([0,width*scale*factor,0],np.shape(v)),atol=1e-12)
  self.assertEqual(DATA,before)
  self.assertEqual(DATA['glyphs']['32']['advance'],278)
  self.assertEqual(DATA['glyphs']['32']['contours'],[])

 def test_baseline_descenders_and_side_transform_matrices(self):
  p=shape('g')
  meshes=[]
  for side in (1,-1,0):
   v,f=text.text_mesh(dict(p,side=side));self.assertSolid(v,f);meshes.append(np.asarray(v))
  origin=np.asarray(geom.to_xyz((p['f'],p['u'],p['x'])))
  positive=meshes[0]-origin
  np.testing.assert_allclose(meshes[1]-origin,positive*[-1,-1,1],atol=1e-12)
  # +side coordinates (depth, advance, ascent) -> top (ascent,-advance,depth).
  np.testing.assert_allclose(meshes[2]-origin,positive[:,[2,1,0]]*[1,-1,1],atol=1e-12)
  self.assertLess(meshes[0][:,2].min(),origin[2])

 def test_planar_depth_zero_keeps_holes_and_baseline(self):
  v,f=text.text_mesh(dict(shape('B'),depth=0))
  self.assertTrue(np.allclose(np.asarray(v)[:,0],.04))
  # Connected planar B with two holes has Euler characteristic 1-2.
  self.assertEqual(topology(v,f)[1],-1)
  self.assertGreater(len(f),10)

 def test_unsupported_layout_or_chars_and_absent_manifold_fail_explicitly(self):
  for extra in (dict(text='☃'),dict(text='line\nbreak'),dict(text='  '),dict(align='JUSTIFY'),dict(side=2),dict(depth=-1),dict(size=0),dict(resolution=0)):
   with self.subTest(extra=extra):
    with self.assertRaises(geom.GeometryError):text.text_mesh(dict(shape('A'),**extra))
  existing=geom._manifold
  try:
   geom._manifold=None
   with self.assertRaisesRegex(geom.GeometryError,'manifold3d'):text.text_mesh(shape('A'))
  finally:geom._manifold=existing


if __name__=='__main__':unittest.main()
