"""RA02 über den echten Weg der Pipeline; tests/robot prüft sonst nur geom.evaluate."""
import contextlib
import io
import unittest

from formgen.robot import bevel, glb, lines, pipeline, silhouette, spec


class IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry = lines.sheets()['RA02']
        cls.document = lines.check_document(bevel.evaluate(pipeline.document_for('RA02', cls.entry)))

    def test_document_passes_the_contract_with_exact_counts(self):
        self.assertEqual(self.document['counts']['triangles'], 264549)
        self.assertEqual(len(self.document['parts']), 554)

    def test_measured_bevels_stay_untouched(self):
        self.assertEqual({p['bevel'] for p in self.document['parts']}, {0})

    def test_spec_and_glb_build(self):
        built = spec.build(self.document, self.entry)
        self.assertEqual([g['id'] for g in built['groups']], ['head', 'upper_body', 'arms', 'legs'])
        self.assertTrue(glb.build(self.document, self.entry['skin']).startswith(b'glTF'))

    def test_no_central_part_claims_a_side(self):
        for part in self.document['parts']:
            low, high = part['bounds_m'][0][0], part['bounds_m'][1][0]
            if '_L_' in part['id'] or '_R_' in part['id']:
                self.assertFalse(low < -.005 and high > .005, part['id'])


class SilhouetteKindTest(unittest.TestCase):
    def test_reference_pose_of_type_two(self):
        self.assertEqual(len(silhouette.reference_triangles(kind=2)), 260247)

    def test_wrong_use_is_refused(self):
        for args, message in ((['a.glb', '--referenzhaltung', '--typ', '7'], 'Register'),
                              (['a.glb', '--referenzhaltung', '--typ'], 'Nummer'),
                              (['a.glb', 'b.glb', '--typ', '2'], 'referenzhaltung'),
                              (['a.glb', '--referenzhaltung', '--typ', '2', '--ohne-helm'], 'Typ 1')):
            with self.subTest(args=args), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(SystemExit, message):
                    if '7' in args:
                        silhouette.reference_triangles(kind=7)
                    else:
                        silhouette.main(args)


if __name__ == '__main__':
    unittest.main()
