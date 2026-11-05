"""Änderungsdateien: Migration der Altdateien, Rückweg, Schema und Gleichlauf von Python und Editor."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from formgen import change_request as cr

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT/'tests/fixtures'
JS = ROOT/'formgen/web/change-request.js'
JXA = """
function run(argv){
 const read=p=>$.NSString.stringWithContentsOfFileEncodingError(p,$.NSUTF8StringEncoding,null).js;
 const box={};new Function('window',read(argv[0]))(box);
 return JSON.stringify(box.FormgenChangeRequest.migrate(JSON.parse(read(argv[1]))));
}
"""


def fixture(name):
    return json.loads((FIX/name).read_text(encoding='utf-8'))


class MigrationTests(unittest.TestCase):
    def test_legacy_files_migrate_to_golden_and_back_without_loss(self):
        for version in (1, 2):
            with self.subTest(version=version):
                legacy = fixture(f'change-request-legacy-v{version}.json')
                migrated = cr.migrate(legacy)
                self.assertEqual(migrated, fixture(f'change-request-migrated-v{version}.json'))
                self.assertEqual(cr.downgrade(migrated), legacy)
                self.assertEqual(cr.migrate(cr.downgrade(migrated)), migrated)

    def test_real_v1_file_keeps_part_assembly_and_location(self):
        legacy = fixture('change-request-legacy-v1.json')
        doc = cr.migrate(legacy)
        self.assertEqual((doc['model']['id'], doc['model']['kind'], doc['model']['name']), ('RA01', 'robot', 'RoboterBasic-01'))
        sample = doc['markings'][0]['samples'][0]
        self.assertEqual((sample['part'], sample['assembly']), ('pauldron_l_338', 'SHOULDER_L'))
        self.assertEqual(sample['location']['gltf_triangle'], 1933)
        self.assertEqual(sample['source']['source_member'], 'SHOULDER_L.json')
        self.assertIsNone(doc['markings'][0]['diameter_mm'])

    def test_unknown_legacy_field_survives_the_round_trip(self):
        legacy = fixture('change-request-legacy-v1.json')
        legacy['target']['future_field'] = {'a': 1}
        self.assertEqual(cr.downgrade(cr.migrate(legacy)), legacy)

    def test_current_file_passes_and_weapon_has_no_way_back(self):
        doc = fixture('change-request-weapon.json')
        self.assertEqual(cr.migrate(doc), doc)
        self.assertEqual(doc['model']['kind'], 'weapon')
        with self.assertRaisesRegex(cr.ChangeRequestError, 'migrierte'):
            cr.downgrade(doc)

    def test_load_reads_files_of_every_version(self):
        for name in ('legacy-v1', 'legacy-v2', 'weapon'):
            self.assertEqual(cr.load(FIX/f'change-request-{name}.json')['format'], cr.FORMAT)

    def test_unknown_or_broken_files_fail(self):
        legacy = fixture('change-request-legacy-v1.json')
        current = fixture('change-request-weapon.json')
        broken = [{'format': 'x'}, dict(current, version=2), dict(legacy, version=3), dict(legacy, model='Unbekannt'),
                  {k: v for k, v in legacy.items() if k != 'target'}, dict(current, markings=[]),
                  dict(current, model=dict(current['model'], kind='vehicle'))]
        for doc in broken:
            with self.subTest(doc=str(doc)[:80]), self.assertRaises(cr.ChangeRequestError):
                cr.migrate(doc)

    def test_saved_text_is_strict_json(self):
        doc = fixture('change-request-weapon.json')
        self.assertEqual(json.loads(cr.dumps(doc)), doc)
        self.assertTrue(cr.dumps(doc).endswith('}\n'))


class EditorParityTests(unittest.TestCase):
    def test_constants_match_python(self):
        text = JS.read_text(encoding='utf-8')
        keys = re.search(r'LOCATION_KEYS=\[(.*?)\]', text, re.S)[1]
        self.assertEqual(tuple(re.findall(r"'([^']+)'", keys)), cr.LOCATION_KEYS)
        self.assertIn(f"FORMAT='{cr.FORMAT}',VERSION={cr.VERSION},LEGACY_FORMAT='{cr.LEGACY_FORMAT}'", text)
        self.assertIn(f"LEGACY_TARGET_ID='{cr.LEGACY_TARGET_ID}'", text)
        self.assertEqual(cr.LEGACY_MODELS, {'RoboterBasic-01': ('RA01', 'robot')})
        self.assertIn("LEGACY_MODELS={'RoboterBasic-01':['RA01','robot']}", text)

    @unittest.skipUnless(shutil.which('osascript'), 'JavaScript-Lauf nur auf dem Mac (JavaScriptCore)')
    def test_javascript_migration_equals_python(self):
        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder)/'migrate.js'
            script.write_text(JXA, encoding='utf-8')
            for name in ('legacy-v1', 'legacy-v2', 'weapon'):
                with self.subTest(name=name):
                    path = FIX/f'change-request-{name}.json'
                    run = subprocess.run(['osascript', '-l', 'JavaScript', str(script), str(JS), str(path)],
                                         capture_output=True, text=True, check=True)
                    self.assertEqual(json.loads(run.stdout), cr.load(path))

    def test_downgrade_to_v1_refuses_more_than_one_point(self):
        doc = cr.load(FIX/'change-request-legacy-v1.json')
        doc['markings'].append(dict(doc['markings'][0], id='zwei'))
        with self.assertRaisesRegex(cr.ChangeRequestError, 'genau einen Punkt'):
            cr.downgrade(doc)


if __name__ == '__main__':
    unittest.main()
