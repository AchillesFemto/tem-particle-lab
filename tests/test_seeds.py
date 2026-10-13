"""Known geometries distinguish a single rod from two touching discs."""
import unittest
import numpy as np
from scipy import ndimage
from microscopy.seeds import collapse_shallow_peak_seeds
from microscopy.core import segment


class PeakGroupingChecks(unittest.TestCase):
    def test_single_rod_ridge(self):
        mask=np.zeros((100,180),bool)
        mask[30:71,20:161]=True
        distance=ndimage.distance_transform_edt(mask)
        seeds=np.array([[50,50],[50,90],[50,130]])
        kept,_=collapse_shallow_peak_seeds(distance,seeds,mask,.25)
        self.assertEqual(len(kept),1)

    def test_touching_discs_retain_two_peaks(self):
        r,c=np.indices((81,101))
        mask=((r-40)**2+(c-35)**2<=25**2)|((r-40)**2+(c-65)**2<=25**2)
        distance=ndimage.distance_transform_edt(mask)
        seeds=np.array([[40,35],[40,65]])
        kept,_=collapse_shallow_peak_seeds(distance,seeds,mask,.25)
        np.testing.assert_array_equal(kept,seeds)

    def test_separate_components_and_coverage(self):
        mask=np.zeros((120,240),bool)
        mask[25:66,20:151]=True
        mask[80:101,180:211]=True
        image=np.where(mask,50,200).astype(np.uint8)
        settings=dict(threshold=140,window_size=21,min_peak_height_px=5,min_seed_separation_px=10)
        _,old,_,_,_=segment(image,settings)
        settings.update(seed_method='prominence_grouping',peak_prominence_fraction=.25)
        _,new,_,_,_=segment(image,settings)
        np.testing.assert_array_equal(old>0,new>0)
        self.assertEqual(new.max(),2)

    def test_invalid_fraction(self):
        mask=np.ones((3,3),bool);distance=np.ones((3,3))
        for fraction in [0,1.1,float('nan')]:
            with self.assertRaises(ValueError):
                collapse_shallow_peak_seeds(distance,[[1,1]],mask,fraction)


if __name__=='__main__':unittest.main()
