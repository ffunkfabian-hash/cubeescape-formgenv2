"""Markierung ohne Browser: Öffnen, Speichern, Wieder-Öffnen und Rückgängig über JavaScriptCore; Attrappen in fixtures/markierung_harness.js."""
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSC = Path('/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc')


def run(script=None):
    args = [str(JSC), str(ROOT / 'tests/fixtures/markierung_harness.js'), '--', str(ROOT)] + ([str(script)] if script else [])
    out = subprocess.run(args, capture_output=True, text=True, check=True).stdout
    return json.loads(out.strip().splitlines()[-1])


@unittest.skipUnless(JSC.exists(), 'JavaScriptCore nur auf dem Mac')
class MarkierungTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = run()

    def test_foreign_file_with_new_marking_survives_a_second_round(self):
        self.assertEqual(self.r['mixed'], dict(sha=self.r['old'], markings=2, same=True))
        self.assertIn('Datei geöffnet', self.r['reopen'])

    def test_undo_restores_the_origin_of_a_foreign_file(self):
        self.assertEqual(self.r['undoForeign']['sha'], self.r['old'])
        self.assertIn('Datei geöffnet', self.r['undoForeign']['reopen'])

    def test_undo_drops_the_origin_of_a_file_taken_back(self):
        self.assertEqual(self.r['undoOwn'], dict(sha=self.r['cur'], migrated=None))

    def test_saving_keeps_asset_and_migration_of_the_source(self):
        self.assertEqual(self.r['kept'], dict(sha=self.r['old'], asset='old.glb', migrated=dict(format='formgen/robot-change-request', version=1)))

    def test_new_file_names_the_current_asset_and_author_frame(self):
        self.assertEqual(self.r['fresh']['sha'], self.r['cur'])
        self.assertEqual([round(v, 3) for v in self.r['fresh']['fux']], [0, 333.333, 333.333])

    def test_group_filter_marks_on_the_single_part(self):
        self.assertEqual(self.r['family'], 'hands')       # Ansicht Baugruppe Arme: die Probe nennt das Einzelteil
        self.assertEqual(self.r['single'], 'hands')
        self.assertEqual(self.r['otherFamily'], '0 Markierungen')         # Ansicht Beine: Teil der Arme ist nicht wählbar


if __name__ == '__main__':
    unittest.main()
