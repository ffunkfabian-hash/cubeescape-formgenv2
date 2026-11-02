import unittest

from tools import acceptance

BACK='5f87122f314c0a572edc52015703d2af4f91730caf9a11aad5a3991aef5f7ce4'
RIGHT='777de0821e8b544de3318fe4e7a5cdb10c0e19725287bf0e6d4583137b51fb90'
FRONT='7102eade6963867822e18977d8888615346f94ca8f9e8a46c317ca5055c72650'


def bands(first, rest=1.0):
    return [{'from_bottom':i,'ratio':first if i==0 else rest} for i in range(10)]


class AcceptanceExceptionTests(unittest.TestCase):
    def setUp(self):
        self.doc=acceptance.load()

    def test_general_limits_unchanged(self):
        self.assertEqual(self.doc['general'],{'iou_min':.9,'band_ratio_min':.92,'band_ratio_max':1.08})

    def test_r01_back_measured_values_pass_with_reasoned_exception(self):
        v=acceptance.judge('R01','back',0.8859483142429271,bands(1.0970891339721571),BACK,self.doc)
        self.assertTrue(v['iou_pass']);self.assertTrue(v['bands_pass'])
        self.assertEqual(v['iou_min'],.88)
        self.assertEqual({e['metric'] for e in v['exceptions_used']},{'iou','band'})
        self.assertTrue(all(e['reason'] and '234 A' in e['source'] for e in v['exceptions_used']))

    def test_exception_floor_still_enforced(self):
        self.assertFalse(acceptance.judge('R01','back',.8799,bands(1.0),BACK,self.doc)['iou_pass'])
        self.assertFalse(acceptance.judge('R01','back',.95,bands(1.11),BACK,self.doc)['bands_pass'])

    def test_iou_exception_only_for_r01_back(self):
        for figure,view,sha in (('R01','front',FRONT),('R01','side-right',RIGHT),('R02','back',BACK)):
            v=acceptance.judge(figure,view,.8859,bands(1.0),sha,self.doc)
            self.assertFalse(v['iou_pass'],(figure,view));self.assertEqual(v['iou_min'],.9)

    def test_band_exception_only_band_zero(self):
        v=acceptance.judge('R01','back',.95,[{'from_bottom':i,'ratio':1.09 if i==3 else 1.0} for i in range(10)],BACK,self.doc)
        self.assertFalse(v['bands_pass'])
        self.assertFalse(acceptance.judge('R01','front',.95,bands(1.09),FRONT,self.doc)['bands_pass'])

    def test_changed_reference_mask_drops_exception(self):
        v=acceptance.judge('R01','back',.8859,bands(1.097),'0'*64,self.doc)
        self.assertFalse(v['iou_pass']);self.assertFalse(v['bands_pass']);self.assertEqual(v['exceptions_used'],[])

    def test_side_band_zero_has_no_exception(self):
        """Freigabe 234 A gilt nur für den R01-Rücken; Seiten-Band 0 (1,42) bleibt offen."""
        v=acceptance.judge('R01','side-right',.9038,bands(1.417),RIGHT,self.doc)
        self.assertTrue(v['iou_pass']);self.assertFalse(v['bands_pass'])
        self.assertEqual({e['view'] for e in self.doc['exceptions']},{'back'})

    def test_no_exception_reported_when_general_limit_holds(self):
        v=acceptance.judge('R01','back',.95,bands(1.0),BACK,self.doc)
        self.assertEqual(v['exceptions_used'],[])


if __name__=='__main__':
    unittest.main()
