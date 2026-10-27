import unittest
import numpy as np

from tools.robot_evidence import band_metrics


class BandMetricTests(unittest.TestCase):
    def test_leg_spacing_changes_width_even_when_area_is_identical(self):
        reference=np.zeros((100,40),dtype=bool)
        reference[:,10:15]=True;reference[:,25:30]=True
        model=np.zeros_like(reference)
        model[:,5:10]=True;model[:,30:35]=True
        bands=band_metrics(reference,model,np.arange(100),0,100)
        for band in bands:
            self.assertEqual(band['reference_mean_width_px'],20)
            self.assertEqual(band['model_mean_width_px'],30)
            self.assertEqual(band['ratio'],1.5)
            self.assertEqual(band['occupied_area_ratio'],1)

    def test_empty_rows_are_not_independently_discarded(self):
        reference=np.ones((100,20),dtype=bool)
        model=reference.copy();model[::2]=False
        bands=band_metrics(reference,model,np.arange(100),0,100)
        self.assertTrue(all(b['ratio']==.5 for b in bands))
        empty=band_metrics(np.zeros_like(reference),model,np.arange(100),0,100)
        self.assertTrue(all(b['ratio'] is None for b in empty))
