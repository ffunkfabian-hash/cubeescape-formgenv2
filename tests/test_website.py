"""Website unter out/: Seiten, Artefakte, 3D-Daten, Three.js-Vendoring und Release."""
import base64
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock
import zipfile

from formgen import build, pipeline, release_assets, viewer, wspec
from formgen.web import site
from formgen.web.vendor import pack_three

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT/'formgen/web'
GLB = b'glTF-Attrappe'


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))


def weapon(sid, letter, name):
    return {'format': wspec.FORMAT, 'format_version': wspec.FORMAT_VERSION, 'id': sid, 'name_de': f'Gewehr · {name}',
            'type': {'num': sid[2:], 'type_de': 'Automatikgewehr', 'type_en': 'Auto Rifle'}, 'variant': {'letter': letter, 'name': name},
            'dimensions_mm': {'length': 915.0}, 'parts': [{'id': 'upper', 'name_de': 'Oberes Gehäuse'}],
            'assemblies': [{'id': 'receiver', 'de': 'Hauptgehäuse'}]}


def robot(**change):
    return {'format': site.ROBOT_FORMAT, 'version': 1, 'id': 'RA01', 'name_de': 'RoboterBasic-01', 'kind': 'robot', 'line': 'basic',
            'skin': 'Weiß-Graphit', 'dimensions_mm': {'height': 1820.0, 'width': 760.0, 'depth': 520.0}, 'parts': 424,
            'assemblies': [{'id': 'head', 'de': 'Kopf'}, {'id': 'torso', 'de': 'Brustkorb'}], **change}


def sheet(out, sid, spec, glb=True):
    write(out/f'sheets/{sid}.dc.html', '<h1>Blatt</h1>')
    write(out/f'previews/{sid}.webp', b'webp')
    write(out/f'specs/{sid}.spec.json', json.dumps(spec))
    write(out/f'prompts/{sid}.prompts.json', json.dumps({'format': 'cubeescape-formgen/prompts'}))
    if glb:
        write(out/f'assets/{sid}.glb', GLB + sid.encode())


class Fixture(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='formgen-web-')
        self.addCleanup(directory.cleanup)
        patcher = mock.patch.object(wspec, 'migrate', lambda doc: doc)   # Schema prüft tests/test_pipeline.py
        patcher.start()
        self.addCleanup(patcher.stop)
        self.path = Path(directory.name)
        self.out, self.cache = self.path/'out', self.path/'cache'
        sheet(self.out, 'BA01', weapon('BA01', 'A', 'Baseline'))
        sheet(self.out, 'BB01', weapon('BB01', 'B', 'Long Reach'), glb=False)
        sheet(self.out, 'RA01', robot())
        for legacy, spec in (('R01', {'format': 'cubeescape-formgen/figure-spec'}), ('KG02', {'format': 'cubeescape-design/weapon-spec'})):
            sheet(self.out, legacy, spec)
        write(self.out/'sheets/W01.dc.html', 'ohne Spec')
        write(self.out/'previews/W01.webp', b'webp')

    def page(self, name):
        return (self.out/name).read_text(encoding='utf-8')


class PagesTests(Fixture):
    def test_navigation_and_separate_pages(self):
        viewer.build(self.out, self.cache)
        for name in ('index.html', 'waffen.html', 'roboter.html', '3d.html'):
            text = self.page(name)
            self.assertIn('aria-label="Hauptnavigation"', text)
            for href in ('index.html', 'waffen.html', 'roboter.html'):
                self.assertIn(f'href="{href}"', text)
        self.assertIn('aria-current=page>Waffen', self.page('waffen.html'))
        self.assertIn('BA01', self.page('waffen.html'))
        self.assertNotIn('RA01', self.page('waffen.html'))
        self.assertIn('RA01', self.page('roboter.html'))
        self.assertNotIn('BA01', self.page('roboter.html'))

    def test_cards_link_sheet_and_3d_only_when_the_model_exists(self):
        viewer.build(self.out, self.cache)
        text = self.page('waffen.html')
        self.assertIn('href="sheets/BA01.dc.html"', text)
        self.assertIn('href="3d.html?id=BA01"', text)
        self.assertIn('href="sheets/BB01.dc.html"', text)
        self.assertNotIn('3d.html?id=BB01', text)
        self.assertIn('3D fehlt', text)

    def test_robot_page_lists_line_and_assemblies(self):
        viewer.build(self.out, self.cache)
        text = self.page('roboter.html')
        self.assertIn('Linie Basic', text)
        self.assertIn('1820 mm', text)
        self.assertIn('Kopf', text)
        self.assertIn('3d.html?id=RA01&amp;baugruppe=torso', text)

    def test_sheets_without_known_format_stay_out(self):
        self.assertEqual([i['id'] for i in viewer.items(self.out)], ['BA01', 'BB01', 'RA01'])
        viewer.build(self.out, self.cache)
        for name in ('index.html', 'waffen.html', 'roboter.html', 'web/catalog.js'):
            for legacy in ('R01', 'R02', 'W01', 'KG02', 'VS02'):
                self.assertNotIn(legacy, self.page(name))

    def test_robot_spec_with_unknown_version_or_gaps_fails(self):
        for spec in (robot(version=2), robot(kind='weapon'), {k: v for k, v in robot().items() if k != 'assemblies'}):
            write(self.out/'specs/RA01.spec.json', json.dumps(spec))
            with self.assertRaises(ValueError):
                viewer.items(self.out)

    def test_no_robot_yet_is_a_clean_state(self):
        (self.out/'specs/RA01.spec.json').unlink()
        viewer.build(self.out, self.cache)
        self.assertIn('Noch kein Roboter gebaut', self.page('roboter.html'))
        self.assertIn('Noch kein Roboter gebaut', self.page('index.html'))

    def test_page_scripts_exist_in_load_order(self):
        viewer.build(self.out, self.cache)
        scripts = re.findall(r'<script defer src="([^"]+)"', self.page('3d.html'))
        self.assertEqual(scripts, [f"web/{site.THREE['file']}", 'web/change-request.js', 'web/catalog.js', 'web/markierung.js', 'web/viewer3d.js'])
        self.assertNotIn('type="module"', self.page('3d.html'))
        for script in scripts:
            self.assertTrue((self.out/script).is_file(), script)


class ArtifactTests(Fixture):
    def test_model_file_embeds_the_glb_and_names(self):
        viewer.build(self.out, self.cache)
        text = self.page('models3d/BA01.js')
        self.assertTrue(text.startswith('window.formgenModel={"id": "BA01",'))
        model = json.loads(text.removeprefix('window.formgenModel=').removesuffix(';\n'))
        raw = (self.out/'assets/BA01.glb').read_bytes()
        self.assertEqual(base64.b64decode(model['glb']), raw)
        self.assertEqual(model['asset_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(model['labels']['parts']['upper'], 'Oberes Gehäuse')
        self.assertFalse((self.out/'models3d/BB01.js').exists())

    def test_second_run_builds_nothing_and_restores_a_missing_file(self):
        first = viewer.build(self.out, self.cache)
        self.assertTrue(all(r.built for r in first))
        self.assertFalse(any(r.built for r in viewer.build(self.out, self.cache)))
        (self.out/'models3d/BA01.js').unlink()
        (self.out/'web/site.css').unlink()
        again = viewer.build(self.out, self.cache)
        self.assertFalse(any(r.built for r in again))
        self.assertEqual({r.output for r in again if r.reason == 'restored_missing_output'}, {'models3d/BA01.js', 'web/site.css'})

    def test_changed_glb_rebuilds_only_its_model(self):
        viewer.build(self.out, self.cache)
        write(self.out/'assets/BA01.glb', GLB + b'neu')
        self.assertEqual([r.output for r in viewer.build(self.out, self.cache) if r.built], ['models3d/BA01.js'])

    def test_force_rebuilds_everything_and_versions_carry_site(self):
        viewer.build(self.out, self.cache)
        self.assertTrue(all(r.built for r in viewer.build(self.out, self.cache, force=True)))
        for artifact in site.artifacts(self.out):
            self.assertEqual(artifact.versions, {'VIEWER': site.VIEWER, 'SITE': site.SITE})

    def test_sheets_stay_untouched(self):
        before = (self.out/'sheets/BA01.dc.html').read_bytes()
        viewer.build(self.out, self.cache)
        self.assertEqual((self.out/'sheets/BA01.dc.html').read_bytes(), before)
        self.assertFalse(any(a.output.startswith('sheets/') for a in site.artifacts(self.out)))

    def test_image_stages_do_not_depend_on_the_website(self):
        for stage, rel in pipeline.CODE.items():
            if stage != 'viewer':
                names = build.source_hashes(ROOT/rel)
                self.assertFalse([n for n in names if '/formgen/web/' in n or n.endswith(('viewer.py', 'change_request.py'))], stage)


class SourceTests(unittest.TestCase):
    def test_sources_have_no_machine_paths_or_external_references(self):
        for path in sorted(WEB.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix in ('.js', '.css', '.py'):
                text = path.read_text(encoding='utf-8')
                for needle in ('cubeescape-critic', 'formgenv2-robot', '/Users/', 'node_modules'):
                    self.assertNotIn(needle, text, path.name)
        own = [WEB/n for n in ('site.css', 'site.js', 'viewer3d.js', 'markierung.js', 'change-request.js', 'site.py')]
        for path in own:
            self.assertNotRegex(path.read_text(encoding='utf-8'), r'https?://', path.name)

    def test_three_is_pinned_with_hash_license_and_origin(self):
        record = json.loads((WEB/'vendor/three.json').read_text(encoding='utf-8'))
        self.assertEqual((record['version'], record['revision'], record['license']), ('0.186.1', '186', 'MIT'))
        self.assertEqual(record['source'], 'https://registry.npmjs.org/three/-/three-0.186.1.tgz')
        self.assertEqual(record['npm_integrity'],
                         'sha512-blFeqb49wRCSGUGj7gtpfnSGHy2lwDk94RhUmS1c/hTby70kvChbWpkJ4Pm1390LqzzvTmzgXKHPEafJwCb8jA==')
        raw = (WEB/'vendor'/record['file']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), record['sha256'])
        self.assertEqual(len(raw), record['bytes'])
        license_text = (WEB/'vendor'/record['license_file']).read_bytes()
        self.assertEqual(hashlib.sha256(license_text).hexdigest(), record['license_sha256'])
        self.assertIn(b'The MIT License', license_text)
        self.assertLess(len(raw), 1_500_000)

    def test_three_pack_is_a_classic_script(self):
        text = (WEB/'vendor'/site.THREE['file']).read_text(encoding='utf-8')
        self.assertNotRegex(text, r'(?m)^(import|export)\b')
        self.assertIn('window.FormgenThree={THREE:M.three,GLTFLoader:', text)
        self.assertIn('three.js r186 (0.186.1)', text.splitlines()[0])

    def test_packer_keeps_literals_and_drops_comments(self):
        source = ("// weg\nconst a = 'x // bleibt', b = `  /* bleibt */\n  ${ 'y' }  `;\n/* weg */\n"
                  "const r = /\\/\\/[/]x/g, c = a / 2 / 3;\nreturn /'/.test( a );\n")
        result = pack_three.strip(source)
        self.assertEqual(result, "const a = 'x // bleibt',b = `  /* bleibt */\n  ${ 'y' }  `;\n"
                                 "const r = /\\/\\/[/]x/g,c = a / 2 / 3;\nreturn /'/.test(a);\n")

    def test_packer_turns_modules_into_functions(self):
        wrapped = pack_three.wrap("import { A, B as C } from 'three';\nclass D extends A {}\nconst e = C;\nexport { D, e as E };\n", 'k')
        self.assertIn('const{A,B:C}=M["three"];', wrapped)
        self.assertIn('M["k"]={D,E:e};', wrapped)
        with self.assertRaisesRegex(ValueError, 'Modulsyntax'):
            pack_three.wrap('export default 1;\n', 'k')


class ReleaseTests(Fixture):
    def prepare(self):
        for legacy in ('R01', 'KG02'):   # alte Formate stehen weder im Viewer noch im Standard-Release
            (self.out/f'sheets/{legacy}.dc.html').unlink()
        write(self.out/'assets/BB01.glb', GLB)
        viewer.build(self.out, self.cache)

    def test_main_zip_follows_the_pages_without_3d_data(self):
        self.prepare()
        result = release_assets.package(self.out, self.path/'release')
        self.assertEqual(result['models'], ['BA01', 'BB01', 'RA01'])
        with zipfile.ZipFile(result['path']) as archive:
            names = set(archive.namelist())
        self.assertLessEqual({'index.html', 'waffen.html', 'roboter.html', '3d.html', 'web/site.css', 'web/catalog.js', 'sheets/RA01.dc.html',
                              f"web/{site.THREE['file']}", f"web/{site.THREE['license_file']}", 'specs/RA01.spec.json'}, names)
        self.assertFalse([n for n in names if n.startswith(('models3d/', 'assets/'))])

    def test_robot_needs_no_prompts(self):
        self.prepare()
        (self.out/'prompts/RA01.prompts.json').unlink()
        self.assertIn('RA01', release_assets.package(self.out, self.path/'release')['models'])

    def test_missing_page_link_fails(self):
        self.prepare()
        write(self.out/'waffen.html', self.page('waffen.html').replace('sheets/BA01.dc.html', 'sheets/BB01.dc.html'))
        with self.assertRaisesRegex(ValueError, 'Viewer'):
            release_assets.package(self.out, self.path/'release')

    def test_3d_zip_is_separate_deterministic_and_complete(self):
        self.prepare()
        one = release_assets.package_3d(self.out, self.path/'a')
        other = release_assets.package_3d(self.out, self.path/'b')
        self.assertEqual(one['sha256'], other['sha256'])
        self.assertTrue(one['path'].endswith('-3d-dry-run.zip'))
        with zipfile.ZipFile(one['path']) as archive:
            self.assertEqual(set(archive.namelist()), {'models3d/BA01.js', 'models3d/BB01.js', 'models3d/RA01.js', 'release-manifest-3d.json'})
            manifest = json.loads(archive.read('release-manifest-3d.json'))
            for name, digest in manifest['sha256'].items():
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)

    def test_3d_zip_rejects_missing_and_foreign_data(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'fehlen'):
            release_assets.package_3d(self.out, self.path/'a', ['BZ99'])
        write(self.out/'models3d/BA01.js', self.page('models3d/BB01.js'))
        with self.assertRaisesRegex(ValueError, 'widersprechen'):
            release_assets.package_3d(self.out, self.path/'a', ['BA01'])


if __name__ == '__main__':
    unittest.main()
