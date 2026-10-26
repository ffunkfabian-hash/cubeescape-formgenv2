"""Montageverträge; bestanden bedeutet noch keine Bildabnahme."""
import unittest
import numpy as np
from formgen import model,geom
from formgen.models.figures import r01_basic_robot as robot

class FigureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=geom.evaluate(model.normalize(robot),bevels=False)

    def test_all_five_assemblies_and_ground_height(self):
        self.assertEqual({p['assembly'] for p in self.doc['parts']},
                         {'head','arms','upper_body','lower_body','legs'})
        self.assertAlmostEqual(self.doc['bounds_m'][0][2],0)
        self.assertAlmostEqual(self.doc['bounds_m'][1][2],1.924)
        self.assertEqual(len({p['id'] for p in self.doc['parts']}),len(self.doc['parts']))

    def test_mating_datums_and_front_joint_heights(self):
        a=self.doc['anchors']
        np.testing.assert_allclose(a['Socket_Neck']['position_m'],a['Socket_Neck_Child']['position_m'])
        for side in ('R','L'):
            np.testing.assert_allclose(a['Socket_Hip_'+side]['position_m'],a['Socket_HipMount_'+side]['position_m'])
            for joint,height in [('Knee',.710),('Ankle',.234),('Elbow',1.275),('Wrist',1.028)]:
                self.assertAlmostEqual(a['Socket_'+joint+'_'+side]['position_m'][2],height)

    def test_every_part_has_provenance_and_only_visor_emits(self):
        emitting=[p for p in self.doc['parts'] if p['role']=='energy']
        self.assertEqual(len(emitting),1)
        self.assertEqual(emitting[0]['assembly'],'head')
        for p in self.doc['parts']:
            self.assertIn(p['provenance']['kind'],('Vorgabe','gemessen','Annahme'))
            self.assertTrue(p['provenance']['source'])
        self.assertEqual(robot.INFO['status'],'draft_not_accepted')
