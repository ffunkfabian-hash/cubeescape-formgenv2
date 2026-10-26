"""Data-only producer/consumer and archive corruption tests; no render fixtures."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import jsonschema
from formgen import geo, geom, model, release_assets, spec
from formgen.cache import canonical

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT/'tests/fixtures'


def write(path, raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(raw)


def mini():
    return geom.evaluate(model.load(ROOT/'formgen/models/mini.py'))


class GeoExportTests(unittest.TestCase):
    def test_import_preserves_mesh_and_semantics_and_rebinds_actual_spec_bytes(self):
        document = geo.load(FIX/'KG02.geo.json')
        before = copy.deepcopy(document)
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            # Deliberately different whitespace: SHA must describe delivered bytes.
            for sid in ('KG02','VS02'):
                value = json.loads((FIX/f'{sid}.spec.json').read_bytes())
                write(folder/f'{sid}.spec.json',canonical(value)+b'\n')
            result = geo.export(document,folder/'KG02.spec.json')
            jsonschema.Draft202012Validator(json.loads((ROOT/'docs/schemas/v1-geo.schema.json').read_text())).validate(result)
            for key in ('parts','decals','anchors','grip','support','checks','counts','surface','string','melee'):
                self.assertEqual(result[key],document['source_geo'][key],key)
            self.assertEqual(document,before)
            for ref in geo._references(result):
                self.assertEqual(ref['sha256'],hashlib.sha256((folder/ref['file']).read_bytes()).hexdigest())

    def test_sight_stays_legacy_and_supports_mount_origin(self):
        document = geo.load(FIX/'VS02.geo.json')
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'VS02.spec.json'
            write(path,(FIX/path.name).read_bytes())
            result = geo.export(document,path)
        self.assertEqual(result['format'],geo.LEGACY)
        self.assertEqual(result['origin'],'Socket_Mount')
        self.assertEqual(result['parts'],document['source_geo']['parts'])

    def test_additional_import_spec_is_required_and_checked(self):
        document = geo.load(FIX/'KG02.geo.json')
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            write(folder/'KG02.spec.json',(FIX/'KG02.spec.json').read_bytes())
            with self.assertRaisesRegex(ValueError,'VS02.spec.json'):
                geo.export(document,folder/'KG02.spec.json')
            write(folder/'VS02.spec.json',b'{}')
            with self.assertRaisesRegex(ValueError,'passt nicht'):
                geo.export(document,folder/'KG02.spec.json')
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            for name in ('KG02.geo.json','KG02.spec.json'):
                write(folder/name,(FIX/name).read_bytes())
            with self.assertRaisesRegex(ValueError,'VS02.spec.json'):
                geo.load(folder/'KG02.geo.json')
            write(folder/'VS02.spec.json',b'{}')
            with self.assertRaisesRegex(ValueError,'Herkunfts-SHA'):
                geo.load(folder/'KG02.geo.json')

    def test_native_mapping_and_nonzero_hand_origin(self):
        document = mini()
        before = copy.deepcopy(document)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'MINI.spec.json'
            specification = spec.build(document)
            write(path,canonical(specification)+b'\n')
            result = geo.export(document,path)
        self.assertEqual(document,before)
        self.assertEqual(result['format'],geo.NATIVE)
        self.assertEqual(result['sheet']['id'],'MINI')
        self.assertFalse(result['compatibility']['legacy_v1'])
        self.assertEqual(result['anchors']['Socket_Hand']['position_m'],[0,0,0])
        offset = [0,-.02,-.03]
        for original, part, semantic in zip(document['parts'],result['parts'],specification['parts']):
            self.assertEqual(part['id'],specification['part_id_map'][original['id']])
            self.assertEqual(part['bounds_m'],semantic['bounds_m'])
            self.assertEqual(part['channel'],semantic['channel'])
            self.assertEqual(part['mesh']['faces'],original['mesh']['faces'])
            for source, vertex in zip(original['mesh']['vertices'],part['mesh']['vertices']):
                for i in range(3): self.assertAlmostEqual(vertex[i],source[i]-offset[i])
        legacy_schema = json.loads((ROOT/'docs/schemas/v1-geo.schema.json').read_text())
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(legacy_schema).validate(result)

    def test_figure_contract_keeps_author_origin_assemblies_and_poses(self):
        document = mini();document['info']['kind'] = 'figure'
        document['poses'] = {'idle':{'source':'fixture, keine Bewegung'}}
        document['parts'][1]['parent_part'] = document['parts'][0]['id']
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'MINI.spec.json'
            write(path,canonical(spec.build(document))+b'\n')
            result = geo.export(document,path)
        self.assertEqual(result['format'],geo.FIGURE)
        self.assertEqual(result['format_version'],1)
        self.assertEqual(result['parts'],document['parts'])
        self.assertEqual(result['anchors'],document['anchors'])
        self.assertEqual(result['poses'],document['poses'])
        self.assertEqual(result['assemblies'],document['assemblies'])
        broken = copy.deepcopy(result);broken['counts']['faces'] += 1
        with self.assertRaisesRegex(ValueError,'counts.faces'): geo.validate(broken)

    def test_bad_input_counts_and_spec_rejected(self):
        document = mini()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'MINI.spec.json'
            write(path,canonical(spec.build(document))+b'\n')
            document['counts']['triangles'] = 1
            with self.assertRaisesRegex(ValueError,'counts.triangles'): geo.export(document,path)
            document = mini()
            specification = spec.build(document);specification['parts'][0]['label'] = 'falsches Modell'
            write(path,canonical(specification)+b'\n')
            with self.assertRaisesRegex(ValueError,'passt nicht'): geo.export(document,path)

    def test_native_zero_area_faces_are_counted_and_removed_without_vertex_changes(self):
        document = mini()
        part = document['parts'][0];mesh = part['mesh']
        initial_faces = copy.deepcopy(mesh['faces'])
        mesh['vertices'].append(list(mesh['vertices'][1]))
        mesh['faces'].append([0,1,len(mesh['vertices'])-1]);mesh['hard'].append(1)
        for key in ('vertices','faces','triangles'): document['counts'][key] += 1
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'MINI.spec.json'
            write(path,canonical(spec.build(document))+b'\n')
            result = geo.export(document,path)
        self.assertEqual(result['counts']['dropped_faces'],1)
        self.assertEqual(result['parts'][0]['mesh']['faces'],initial_faces)
        self.assertEqual(len(result['parts'][0]['mesh']['vertices']),len(mesh['vertices']))
        self.assertEqual(len(result['parts'][0]['mesh']['hard']),len(initial_faces))
        self.assertIn('1 degenerierte',result['warnings'][-1])

    def test_bounds_decals_and_unsafe_paths_rejected(self):
        original = json.loads((FIX/'KG02.geo.json').read_bytes())
        edits = [lambda d:d['parts'][0]['bounds_m'][0].__setitem__(0,99),
                 lambda d:d['counts'].__setitem__('decals',0),
                 lambda d:d['source']['sight_spec'].__setitem__('file','../VS02.spec.json'),
                 lambda d:d['anchors']['Socket_Hand'].__setitem__('position_m',[False,0,0])]
        for edit in edits:
            document = copy.deepcopy(original);edit(document)
            with self.assertRaises((ValueError,jsonschema.ValidationError)): geo.validate(document)

    def test_coplanar_reports_real_overlap_not_contacts_or_far_faces(self):
        def triangle(pid,z=0,reverse=False):
            return dict(id=pid,channel='MT_Primary',material='painted',emissive=False,glass=False,
                        mesh=dict(vertices=[[0,0,z],[.1,0,z],[0,.1,z]],faces=[[2,1,0] if reverse else [0,1,2]],hard=[1]))
        a = triangle('p00')
        findings = geo._coplanar([a,triangle('p01',.0003)])
        self.assertEqual(len(findings),1)
        self.assertAlmostEqual(findings[0]['distance_m'],.0003)
        self.assertAlmostEqual(findings[0]['overlap_m2'],.005)
        self.assertEqual(findings[0]['faces'],1)
        self.assertTrue(findings[0]['same_look'])
        self.assertEqual(geo._coplanar([a,triangle('p01',.0007)]),[])
        self.assertEqual(geo._coplanar([a,triangle('p01',0,True)]),[])


class ReleaseTests(unittest.TestCase):
    def fixture(self,folder):
        """Small static byte fixtures; raster validity is covered by render tests."""
        for sid in ('KG02','VS02'):
            for kind,suffix in (('specs','spec.json'),('geo','geo.json')):
                write(folder/kind/f'{sid}.{suffix}',(FIX/f'{sid}.{suffix}').read_bytes())
            write(folder/'prompts'/f'{sid}.prompts.json',canonical({'format':'cubeescape-formgen/prompts','de':'Probe','en':'test'}))
            write(folder/'previews'/f'{sid}.webp',b'preview fixture')
            write(folder/'views'/sid/'side.png',b'view fixture')
            write(folder/'sheets'/f'{sid}.dc.html',f'<style>@font-face{{src:url(../fonts/Test.ttf)}}</style><img src="../views/{sid}/side.png">'.encode())
        write(folder/'fonts/Test.ttf',b'font fixture')
        write(folder/'index.html',''.join(f'<a href="sheets/{sid}.dc.html"><img src="previews/{sid}.webp"></a>' for sid in ('KG02','VS02')).encode())

    def test_deterministic_zip_actual_references_and_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td);out = folder/'out';self.fixture(out)
            result = release_assets.package(out,folder/'a',['VS02','KG02'])
            other = release_assets.package(out,folder/'b',['KG02','VS02'])
            self.assertEqual(result['sha256'],other['sha256'])
            with zipfile.ZipFile(result['path']) as archive:
                names = archive.namelist()
                self.assertIn('prompts/KG02.prompts.json',names)
                self.assertNotIn('prompts/KG02.json',names)
                self.assertIn('fonts/Test.ttf',names)
                self.assertEqual(len(names),len(set(names)))
                manifest = json.loads(archive.read('release-manifest.json'))
                for name,sha in manifest['sha256'].items():
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(),sha)
                self.assertEqual(set(names),set(manifest['sha256'])|{'release-manifest.json'})

    def test_missing_view_and_font_fail_before_packaging(self):
        for missing in ('views/KG02/side.png','fonts/Test.ttf'):
            with tempfile.TemporaryDirectory() as td:
                folder = Path(td);out = folder/'out';self.fixture(out)
                (out/missing).unlink()
                with self.assertRaisesRegex(ValueError,'unvollständig'):
                    release_assets.package(out,folder/'release')
                self.assertFalse((folder/'release').exists())

    def test_wrong_geo_and_nested_sight_spec_hash_fail(self):
        for owner,field in [('geo/KG02.geo.json',('source','weapon_spec')),('specs/KG02.spec.json',('sight','sight_spec'))]:
            with tempfile.TemporaryDirectory() as td:
                folder = Path(td);out = folder/'out';self.fixture(out)
                path = out/owner;document = json.loads(path.read_bytes())
                document[field[0]][field[1]]['sha256'] = '0'*64
                write(path,canonical(document))
                with self.assertRaisesRegex(ValueError,'SHA'):
                    release_assets.package(out,folder/'release')

    def test_missing_additional_sight_spec_fails(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td);out = folder/'out';self.fixture(out)
            (out/'specs/VS02.spec.json').unlink()
            with self.assertRaisesRegex(ValueError,'VS02.spec.json'):
                release_assets.package(out,folder/'release',['KG02'])

    def test_bad_viewer_paths_external_links_and_selection_fail(self):
        bad_html = ['<img src="../../outside.png">','<img src="https://example.test/a.png">',
                    '<img src="/tmp/asset.png">','<a href="sheets/VS02.dc.html">only VS02</a>']
        for html in bad_html:
            with tempfile.TemporaryDirectory() as td:
                folder = Path(td);out = folder/'out';self.fixture(out)
                write(out/'index.html',html.encode())
                with self.assertRaises(ValueError): release_assets.package(out,folder/'release')

    def test_absolute_json_source_path_fails(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td);out = folder/'out';self.fixture(out)
            path = out/'specs/KG02.spec.json';document = json.loads(path.read_bytes())
            document['source'] = {'path':'/Users/private/secret.py'}
            write(path,canonical(document))
            with self.assertRaisesRegex(ValueError,'Absoluter'): release_assets.package(out,folder/'release')


if __name__ == '__main__': unittest.main()
