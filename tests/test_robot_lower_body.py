"""Beckenvertrag und echte geschlossene Schalen, ohne Renderlast."""
import json
import unittest
from collections import Counter

from formgen import geom
from formgen.models.figures.r01_parts import lower_body


class RobotLowerBodyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = geom.evaluate(dict(
            info=dict(id='LOWER', kind='figure', name_de='Becken',
                      provenance=lower_body.PROVENANCE),
            parts=lower_body.PARTS,
            assemblies=[dict(id='lower_body', de='Becken')],
            anchors=lower_body.ANCHORS))

    def test_shared_interface_and_materials(self):
        anchors = lower_body.ANCHORS
        self.assertEqual(anchors['Socket_Waist']['at'], [45, 1190, 0])
        for side, x in [('R', -142), ('L', 142)]:
            self.assertEqual(anchors['Socket_HipMount_' + side]['at'],
                             [45, 1080, x])
        for part in lower_body.PARTS:
            self.assertEqual(part['assembly'], 'lower_body')
            self.assertTrue(part['id'].startswith('lower_'))
            self.assertNotIn(part['role'], ('energy', 'cyan'))
        self.assertEqual(self.document['warnings'], [])
        json.dumps(self.document, allow_nan=False)

    def test_shells_have_closed_consistent_edges_and_positive_volume(self):
        for part in self.document['parts']:
            with self.subTest(part=part['id']):
                mesh = part['mesh']
                edges = Counter()
                directed = Counter()
                for face in mesh['faces']:
                    for a, b in zip(face, face[1:] + face[:1]):
                        edges[tuple(sorted((a, b)))] += 1
                        directed[a, b] += 1
                self.assertTrue(all(n == 2 for n in edges.values()))
                self.assertTrue(all(directed[a, b] == directed[b, a]
                                    for a, b in directed))
                self.assertGreater(geom._volume(mesh['vertices'], mesh['faces']), 0)


if __name__ == '__main__':
    unittest.main()
