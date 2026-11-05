"""RoboterBasic-01: Modell, Register, GLB, Spec und Silhouettenmessung, ohne Referenzdatei aus der Sicherung."""
import json
import re
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import jsonschema
import numpy as np

from formgen import change_request, geom, model, sheet, variants
from formgen.models.robot import roboterbasic_01 as basic
from formgen.robot import glb, lines, pipeline, silhouette, spec
from formgen.web import site

ROOT = Path(__file__).resolve().parents[1]


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = model.normalize(basic.document())
        cls.doc = geom.evaluate(cls.raw)


class ModelTest(Base):
    def test_parts_and_assemblies(self):
        self.assertEqual(len(self.raw['parts']), 424)
        self.assertEqual([a['id'] for a in self.raw['assemblies']], ['head', 'arms', 'upper_body', 'lower_body', 'legs'])
        self.assertEqual(self.raw['info']['id'], 'RA01')
        self.assertEqual(self.raw['info']['kind'], 'figure')

    def test_only_helmet_is_surface_data(self):
        measured = [p for p in self.raw['parts'] if p.get('provenance', {}).get('kind') == 'gemessen']
        self.assertEqual(len(measured), 58)
        self.assertTrue(all(p['id'].startswith('helmet_') for p in measured))
        rest = [p for p in self.raw['parts'] if p not in measured]
        self.assertEqual({p['form'] for p in rest}, {'wrap', 'cyl', 'box', 'loft', 'tube', 'plate', 'hull'})

    def test_size_matches_reference_measure(self):
        low, high = np.array(self.doc['bounds_m'])
        np.testing.assert_allclose(high - low, (.8663, .5257, 1.6560), atol=.002)   # Referenz 0,8659 × 0,5250 × 1,6559 m

    def test_every_anchor_on_known_part(self):
        ids = {p['id'] for p in self.raw['parts']}
        self.assertIn('Socket_Hand', self.raw['anchors'])
        self.assertTrue(all(a['part'] in ids for a in self.raw['anchors'].values()))

    def test_sides_mirror_in_part_count(self):
        ids = {p['id'] for p in self.raw['parts']}
        left = {i for i in ids if re.search(r'(^|_)L_', i)}
        for i in left:
            self.assertIn(re.sub(r'(^|_)L_', r'\1R_', i, count=1), ids)

    def test_no_critic_link_in_source(self):
        files = [*(ROOT / 'formgen/robot').glob('*.py'), *(ROOT / 'formgen/models/robot').glob('*.py'), ROOT / 'data/robots.toml', ROOT / 'tools/robot_helmet_transfer.py']
        for path in files:
            text = path.read_text().lower()
            self.assertNotIn('cubeescape-critic', text, path)
            self.assertNotIn('critic_', text, path)
            self.assertNotIn('/users/', text, path)


    def test_left_parts_keep_outward_normals(self):
        def volume(p):
            v = np.array(p['mesh']['vertices'])
            return float(np.einsum('ij,ij->i', v[np.array(p['mesh']['faces'])[:, 0]], np.cross(v[np.array(p['mesh']['faces'])[:, 1]], v[np.array(p['mesh']['faces'])[:, 2]])).sum() / 6)
        parts = {p['id']: p for p in self.doc['parts']}
        pairs = [(i, re.sub(r'(^|_)L_', r'\1R_', i, count=1)) for i, p in parts.items() if p['side'] == 'L' and p['form'] in ('loft', 'tube', 'wrap')]
        self.assertGreater(len(pairs), 30)
        for left, right in pairs:
            self.assertGreater(volume(parts[left]), 0, left)
            self.assertAlmostEqual(volume(parts[left]) / volume(parts[right]), 1, delta=.05, msg=left)

    def test_anchor_positions_survive_the_gltf_to_fux_formula(self):
        for name, a in self.doc['anchors'].items():
            x, y, z = a['position_m']
            np.testing.assert_allclose(change_request.fux_from_gltf((x, z, -y)), a['at'], atol=1e-6, err_msg=name)
        self.assertIn('[1000*pos.z,1000*pos.y,1000*pos.x]', (ROOT / 'formgen/web/markierung.js').read_text())


class KeyTest(unittest.TestCase):
    def spec_key(self, sheets, skins='0' * 64):
        seen = []
        hashes = lambda path: skins if Path(path).name == 'skins.toml' else '0' * 64
        with tempfile.TemporaryDirectory() as t, mock.patch.object(pipeline, 'run_artifacts', side_effect=lambda a, *r, **k: seen.extend(a) or []), \
                mock.patch.object(pipeline, 'file_hash', hashes):
            pipeline.run(sheets, Path(t), Path(t) / 'c', stages=('specs',), log=lambda *_: None)
        return seen[0].key

    def test_spec_key_follows_register_and_skin(self):
        sheets = lines.sheets()
        base = self.spec_key(sheets)
        self.assertEqual(base, self.spec_key(sheets))
        self.assertNotEqual(base, self.spec_key({'RA01': dict(sheets['RA01'], skin='nacht')}))
        self.assertNotEqual(base, self.spec_key(sheets, skins='1' * 64))

    def test_image_and_sheet_keys_carry_the_code(self):
        a = pipeline.Artifact('RA01', 'sheets', 's', {}, {}, 'x', 'b', {})
        b = pipeline.Artifact('RA01', 'views', 's', {}, {}, 'x', 'b', {})
        sheet_a, view_b = pipeline._coded([a, b])
        self.assertIn('code', sheet_a.params)
        self.assertIn('env', view_b.params)
        self.assertNotEqual(a.key, sheet_a.key)

    def test_geometry_key_includes_the_evaluation_engine(self):
        entry = lines.sheets()['RA01']
        real = pipeline.build.source_hashes
        changed = lambda path, *a: {k: ('x' if k.endswith('geom.py') else v) for k, v in real(path, *a).items()}
        before = pipeline.source_hash(entry)
        with mock.patch.object(pipeline.build, 'source_hashes', changed):
            self.assertNotEqual(before, pipeline.source_hash(entry))


class LinesTest(unittest.TestCase):
    def test_register_has_exactly_ra01_today(self):
        self.assertEqual(list(lines.sheets()), ['RA01'])
        e = lines.sheets()['RA01']
        self.assertEqual((e['skin'], e['type']['name_de'], e['line']['name']), ('weiss_graphit', 'RoboterBasic-01', 'Basic'))

    def test_second_basic_type_gets_its_own_sheet_and_leaves_the_first_alone(self):
        reg = lines.load()
        before = lines.sheets(reg)['RA01']
        two = dict(types=reg['types'] + [dict(num=2, name_de='RoboterBasic-02', module='formgen.models.robot.roboterbasic_02', since='0.10')],
                   lines=[dict(reg['lines'][0], types=[1, 2])])
        sheets = lines.sheets(lines.validate(two['types'], two['lines']))
        self.assertEqual(list(sheets), ['RA01', 'RA02'])
        self.assertEqual(sheets['RA01'], before)
        self.assertEqual(pipeline.source_hash(sheets['RA01']), pipeline.source_hash(before))

    def test_rules(self):
        types = [dict(num=1, name_de='x', module='formgen.models.robot.x', since='0.9')]
        good = dict(letter='B', name='Heavy', since='0.9', idea='x', skin='weiss_graphit', types=[1])
        lines.validate(types, [good])
        for bad in (dict(good, letter='I'), dict(good, letter='O'), dict(good, name='a b c d'), dict(good, name='Averyveryverylongname'), dict(good, types=[7]), dict(good, types=[])):
            with self.assertRaises(ValueError):
                lines.validate(types, [bad])
        with self.assertRaises(ValueError):
            lines.validate(types, [good, dict(good, name='Other')])
        with self.assertRaisesRegex(ValueError, 'nicht unter'):
            lines.validate([dict(types[0], module='anderswo.x')], [good])

    def test_merge_rejects_unknown_parameter(self):
        with self.assertRaisesRegex(ValueError, 'nope'):
            lines.merge(basic.PARAMS, {'nope': 1})
        with self.assertRaisesRegex(ValueError, 'legs.nope'):
            lines.merge(basic.PARAMS, {'legs': {'nope': 1}})

    def test_parameter_line_changes_shape_and_keeps_ids(self):
        base = {p['id']: p for p in basic.parts()}
        other = {p['id']: p for p in basic.parts(lines.merge(basic.PARAMS, {'arm_bulk': 1.6}))}
        self.assertEqual(set(base), set(other))
        self.assertNotEqual(base['arm_R_fore_body']['points'], other['arm_R_fore_body']['points'])
        self.assertEqual(base['torso_core']['vertices'], other['torso_core']['vertices'])


class AssetTest(Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.glb = glb.build(cls.doc, 'weiss_graphit')
        size, = struct.unpack_from('<I', cls.glb, 12)
        cls.gltf = json.loads(cls.glb[20:20 + size])

    def test_header_and_length(self):
        self.assertEqual(self.glb[:4], b'glTF')
        self.assertEqual(struct.unpack_from('<I', self.glb, 8)[0], len(self.glb))

    def test_every_part_is_a_named_node(self):
        nodes = [n for n in self.gltf['nodes'] if 'mesh' in n]
        self.assertEqual({n['extras']['basic_part'] for n in nodes}, {p['id'] for p in self.doc['parts']})
        self.assertTrue(all(n['extras']['basic_assembly'] for n in nodes))

    def test_triangles_survive(self):
        with tempfile.TemporaryDirectory() as t:
            path = Path(t) / 'a.glb'
            path.write_bytes(self.glb)
            self.assertEqual(len(silhouette.triangles(path)), self.doc['counts']['triangles'])

    def test_normals_are_split_at_sharp_edges(self):
        cube = [[a, b, c] for a in (0, 1) for b in (0, 1) for c in (0, 1)]
        faces = geom._triangulate(*geom._shape(dict(shape='hull', points=[[1000 * v for v in p] for p in cube]), []))
        v, n, t = glb.split_normals(geom._shape(dict(shape='hull', points=[[1000 * v for v in p] for p in cube]), [])[0], faces)
        self.assertEqual(len(v), 24)
        np.testing.assert_allclose(np.linalg.norm(n, axis=1), 1)

    def test_skin_colors_come_from_skins_toml(self):
        m = {x['name']: x for x in glb.materials('weiss_graphit', ['shell', 'graphite'])}
        self.assertGreater(m['shell']['pbrMetallicRoughness']['baseColorFactor'][0], .6)
        self.assertLess(m['graphite']['pbrMetallicRoughness']['baseColorFactor'][0], .06)


class ContractTest(Base):
    def test_basic_type_contract_holds_and_rejects_gaps(self):
        lines.check_document(self.doc)
        with self.assertRaisesRegex(ValueError, 'Baugruppen'):
            lines.check_document(dict(self.doc, assemblies=self.doc['assemblies'][:4]))
        with self.assertRaisesRegex(ValueError, 'Socket_Hand'):
            lines.check_document(dict(self.doc, anchors={k: v for k, v in self.doc['anchors'].items() if k != 'Socket_Hand'}))
        with self.assertRaisesRegex(ValueError, 'Rollen'):
            lines.check_document(dict(self.doc, parts=[dict(self.doc['parts'][0], role='gibt_es_nicht')]))

    def test_module_interface(self):
        for name in ('PARAMS', 'DATA_FILES', 'document', 'INFO', 'PARTS', 'ASSEMBLIES', 'ANCHORS', 'POSES'):
            self.assertTrue(hasattr(basic, name), name)
        doc = pipeline.document_for('RA01', lines.sheets()['RA01'])
        self.assertEqual((doc['info']['id'], doc['info']['name_de'], doc['info']['line']), ('RA01', 'RoboterBasic-01', 'basic'))

    def test_website_shows_two_types_side_by_side(self):
        item = dict(kind='robot', has_3d=True, name='x', line='basic', skin='weiss_graphit', parts=1, labels={}, assemblies=[dict(id='head', de='Kopf')],
                    dimensions_mm=dict(height=1, width=1, depth=1))
        html = site.robots_page([dict(item, id='RA01'), dict(item, id='RA02')])
        self.assertIn('2 Roboter', html)
        self.assertIn('3d.html?id=RA02', html)


class SheetTest(Base):
    def test_material_tiles_show_the_robot_skin(self):
        doc = dict(self.doc, info=dict(self.doc['info'], skin='weiss_graphit'))
        html = sheet.materials_html(doc).upper()
        self.assertIn('#D6D7D5', html)
        self.assertNotIn('#D8CCB4', html)
        self.assertIn('#D8CCB4', sheet.materials_html(self.doc).upper())      # ohne info.skin wie bisher

    def test_weapon_lines_cannot_use_a_robot_skin(self):
        self.assertNotIn('weiss_graphit', variants._skins())


class SpecTest(Base):
    def test_spec(self):
        s = spec.build(self.doc, lines.sheets()['RA01'])
        self.assertEqual((s['format'], s['version'], s['id'], s['kind'], s['skin'], s['line']), ('formgenv2/robot-sheet-spec', 1, 'RA01', 'robot', 'weiss_graphit', 'basic'))
        self.assertEqual(s['type'], dict(num=1, name_de='RoboterBasic-01'))
        self.assertEqual(len(s['measured_parts']), 58)
        self.assertEqual(sum(a['parts'] for a in s['assemblies']), 424)
        self.assertEqual(len(s['parts']), 424)
        self.assertEqual({'id', 'name_de', 'assembly', 'role'}, set(s['parts'][0]))
        jsonschema.validate(json.loads(json.dumps(s)), json.loads((ROOT / 'docs/schemas/robot-sheet-spec.schema.json').read_text()))
        spec.migrate(s)
        with self.assertRaises(ValueError):
            spec.migrate(dict(s, version=2))
        with self.assertRaises(ValueError):
            spec.migrate(dict(s, format='anders'))


def _box(w, h, d):
    v = np.array([[x, y, z] for x in (-w / 2, w / 2) for y in (0, h) for z in (-d / 2, d / 2)])
    t = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
    return v[np.array(t)]


def _tiny_glb(path, names):
    """Je Name ein Dreieck unter einem Node SEG_head, wie im Referenz-GLB."""
    blob = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], '<f4').tobytes()
    meshes = [dict(primitives=[dict(attributes=dict(POSITION=0))]) for _ in names]
    nodes = [dict(name=n, mesh=i) for i, n in enumerate(names)] + [dict(name='SEG_head', children=list(range(len(names))))]
    doc = dict(scene=0, scenes=[dict(nodes=[len(names)])], nodes=nodes, meshes=meshes, buffers=[dict(byteLength=len(blob))],
               bufferViews=[dict(buffer=0, byteOffset=0, byteLength=len(blob))], accessors=[dict(bufferView=0, componentType=5126, count=3, type='VEC3')])
    head = json.dumps(doc).encode()
    head += b' ' * (-len(head) % 4)
    Path(path).write_bytes(struct.pack('<4sII', b'glTF', 2, 28 + len(head) + len(blob)) + struct.pack('<I4s', len(head), b'JSON') + head + struct.pack('<I4s', len(blob), b'BIN\0') + blob)


class SilhouetteTest(unittest.TestCase):
    def test_without_helmet_keeps_the_neck_only(self):
        with tempfile.TemporaryDirectory() as t:
            path = Path(t) / 'r.glb'
            _tiny_glb(path, ['neck', 'neck_ring', 'Crown', 'Shell'])
            self.assertEqual(len(silhouette.triangles(path)), 4)
            self.assertEqual(len(silhouette.triangles(path, helmet=False)), 2)

    def test_identical_figures_pass(self):
        r = silhouette.compare(_box(.5, 1.6, .3), _box(.5, 1.6, .3), 200)
        for v in r.values():
            self.assertEqual(v['iou'], 1.0)
            self.assertTrue(v['iou_pass'] and v['bands_pass'])

    def test_counterproof_wider_figure_fails_for_the_right_reason(self):
        """Gegenprobe: 15 % breiter muss in IoU und Band rot werden, nicht nur irgendwie."""
        r = silhouette.compare(_box(.5, 1.6, .3), _box(.575, 1.6, .345), 200)
        for v in r.values():
            self.assertFalse(v['iou_pass'])
            self.assertFalse(v['bands_pass'])
            self.assertGreater(min(v['bands']), 1.08)

    def test_band_catches_local_error_iou_misses(self):
        low = _box(.5, 1.6, .3)
        extra = _box(.70, .16, .3) + np.array((0, 1.44, 0))
        r = silhouette.compare(low, np.concatenate((low, extra)), 200)
        self.assertTrue(r['front']['iou_pass'])
        self.assertFalse(r['front']['bands_pass'])
        self.assertGreater(r['front']['bands'][-1], 1.08)
        self.assertAlmostEqual(r['front']['bands'][0], 1.0, places=2)


if __name__ == '__main__':
    unittest.main()
