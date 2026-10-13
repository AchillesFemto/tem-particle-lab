"""Checks on known examples; experimental correctness still needs validation."""
import unittest
import numpy as np
from scipy import ndimage
from lesson_17 import mask_iou
from lesson_19 import pixel_precision
from lesson_20 import pixel_recall
from lesson_22 import foreground_distance
from lesson_23 import suppress_nearby_seeds
from lesson_24 import separate_foreground
from lesson_25 import overlap_diagnostics
from lesson_26 import nearest_neighbours,radial_pair_correlation
from lesson_27 import image_power_spectrum,position_structure_factor
from lesson_28 import follow_template,time_averaged_msd

class ScientificExamples(unittest.TestCase):
    def test_known_scores(self):
        r=np.array([True,True,False,False]);c=np.array([True,False,True,False])
        self.assertAlmostEqual(mask_iou(r,c),1/3)
        self.assertEqual(pixel_precision(r,c),0.5);self.assertEqual(pixel_recall(r,c),0.5)
        with self.assertRaises(ValueError):pixel_precision(r,np.zeros(4,bool))
        with self.assertRaises(ValueError):pixel_recall(np.zeros(4,bool),c)

    def test_nearby_seeds_and_other_component(self):
        m=np.zeros((30,30),bool);m[5:15,5:15]=True;m[5:15,16:22]=True
        d=np.zeros(m.shape);d[10,10]=8;d[10,12]=7;d[10,17]=6
        s=suppress_nearby_seeds(d,np.array([[10,10],[10,12],[10,17]]),m,10)
        np.testing.assert_array_equal(s,[[10,10],[10,17]])

    def test_two_disc_separation(self):
        rr,cc=np.indices((81,101));m=((rr-40)**2+(cc-35)**2<25**2)|((rr-40)**2+(cc-65)**2<25**2)
        labels,_=separate_foreground(m,foreground_distance(m),np.array([[40,35],[40,65]]))
        self.assertEqual(set(np.unique(labels)),{0,1,2});np.testing.assert_array_equal(labels>0,m)
        self.assertEqual(labels[40,35],1);self.assertEqual(labels[40,65],2)

    def test_merge_and_miss(self):
        a=np.zeros((8,12),bool);a[1:4,1:4]=True
        b=np.zeros_like(a);b[1:4,4:7]=True;c=np.zeros_like(a);c[5:7,9:11]=True
        labels=np.zeros(a.shape,int);labels[a|b]=1
        *_,links=overlap_diagnostics([a,b,c],labels)
        np.testing.assert_array_equal(links.sum(axis=0),[2]);np.testing.assert_array_equal(links.sum(axis=1),[1,1,0])

    def test_spatial_geometry(self):
        d,*_=nearest_neighbours(np.array([[10.,10.],[13.,14.],[25.,10.]]),40,40)
        np.testing.assert_allclose(d[:2],5)
        g,c=radial_pair_correlation(np.array([[10.,10.],[20.,10.]]),40,40,np.array([0.,15.]))
        self.assertEqual(c.tolist(),[1]);self.assertAlmostEqual(g[0],1600*(1600/1200)/(np.pi*225))

    def test_fourier_units_and_interference(self):
        p=np.array([[0.,0.],[10.,0.]]);fx=np.array([0.,0.05,0.1]);fy=np.array([0.])
        s=position_structure_factor(p,fx,fy)
        np.testing.assert_allclose(s[0],[2,0,2],atol=1e-12)
        np.testing.assert_allclose(s,position_structure_factor(p+[3,7],fx,fy),atol=1e-12)
        x=np.arange(64);im=np.tile(np.cos(2*np.pi*4*x/64),(64,1))
        fx,fy,power=image_power_spectrum(im,0.2,False);r,c=np.unravel_index(power.argmax(),power.shape)
        self.assertAlmostEqual(abs(fx[c]),4/(64*0.2));self.assertEqual(fy[r],0)

    def test_motion_and_msd(self):
        rr,cc=np.indices((160,160));im=100-50*np.exp(-((rr-80)**2+(cc-80)**2)/50)
        frames=[ndimage.shift(im,(i,2*i),order=0,mode="constant",cval=100) for i in range(5)]
        track,*_=follow_template(frames,initial=(80,80),half_width=15,search_radius=4,sigma=0.5,min_score=0.9)
        self.assertEqual([(r["row_px"],r["column_px"]) for r in track],[(80+i,80+2*i) for i in range(5)])
        positions=np.array([[r["column_px"],r["row_px"]] for r in track],float)
        np.testing.assert_allclose([r["msd_nm2"] for r in time_averaged_msd(positions,1,4)],[5,20,45,80])

if __name__=="__main__":unittest.main()
