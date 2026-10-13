"""Known geometries and review edits, without inventing human observations."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
from skimage.measure import regionprops
from microscopy.measurements import shape_measurements,measure_labels
from microscopy.particle_review import ParticleReview,polygon_mask,prepare_review
from microscopy.core import fingerprint
from PIL import Image


class ShapeChecks(unittest.TestCase):
    def test_rectangle_axes_calibration_and_transpose(self):
        labels=np.zeros((50,50),np.int32);labels[10:31,15:24]=1
        p=regionprops(labels)[0];m=shape_measurements(p,.2)
        self.assertAlmostEqual(m['ellipse_major_px'],4*np.sqrt((21**2-1)/12))
        self.assertAlmostEqual(m['ellipse_minor_px'],4*np.sqrt((9**2-1)/12))
        self.assertAlmostEqual(m['feret_max_px'],np.hypot(21,8))
        self.assertAlmostEqual(m['feret_max_nm'],.2*m['feret_max_px'])
        transposed=shape_measurements(regionprops(labels.T)[0])
        for name in ['ellipse_major_px','ellipse_minor_px','feret_max_px','ellipse_aspect_ratio']:
            self.assertAlmostEqual(m[name],transposed[name])
        self.assertIsNone(transposed['feret_max_nm'])

    def test_degenerate_width_and_border(self):
        labels=np.zeros((8,8),np.int32);labels[0,2]=1
        r=measure_labels(labels)[0]
        self.assertTrue(r['touches_crop_border']);self.assertIsNone(r['ellipse_aspect_ratio'])

    def test_display_axis_follows_positive_diagonal_rod(self):
        import matplotlib.pyplot as plt
        from review_particles import ReviewWindow
        r,c=np.indices((80,80))
        mask=(abs(r-c)<=4)&(r+c>=35)&(r+c<=115)
        with tempfile.TemporaryDirectory() as folder:
            model=ParticleReview(mask.astype(np.int32),{'nm_per_pixel':None},folder)
            window=ReviewWindow(model,np.where(mask,50,200).astype(np.uint8))
            window.selected=[1];window.redraw()
            line=next(line for line in window.detail.lines if line.get_color()=='red')
            dx=np.diff(line.get_xdata())[0];dy=np.diff(line.get_ydata())[0]
            self.assertGreater(dx*dy,0)
            window.action('correct');self.assertEqual(model.status[1],'correct')
            window.action('undo');self.assertEqual(model.status[1],'pending')
            plt.close(window.fig)


class ReviewChecks(unittest.TestCase):
    def model(self,folder):
        labels=np.zeros((30,40),np.int32)
        labels[10:20,5:15]=1;labels[10:20,15:25]=2
        return ParticleReview(labels,{'nm_per_pixel':None},folder)

    def test_merge_undo_and_split_preserve_foreground(self):
        m=self.model('.');original=m.labels.copy()
        m.apply('merge',[1,2],note='Known single rectangle was divided.')
        self.assertEqual(set(m.status),{1});self.assertEqual(m.status[1],'pending')
        np.testing.assert_array_equal(m.labels>0,original>0)
        m.undo();np.testing.assert_array_equal(m.labels,original)
        m.apply('split_region',[1],vertices=[(5,10),(9,10),(9,19),(5,19)],note='Known two subregions.')
        self.assertEqual(len(m.status),3)
        np.testing.assert_array_equal(m.labels>0,original>0)

    def test_collision_failure_is_atomic(self):
        m=self.model('.');original=m.labels.copy()
        with self.assertRaises(ValueError):
            m.apply('replace',[1],vertices=[(5,10),(24,10),(24,19),(5,19)],note='Overlap trial')
        np.testing.assert_array_equal(m.labels,original);self.assertEqual(m.log,[])
        with self.assertRaises(ValueError):m.apply('merge',[1,2])

    def test_add_remove_and_field_inspection_reset(self):
        m=self.model('.');m.inspect_field('Full test field inspected')
        m.apply('add',vertices=[(30,3),(34,3),(34,7),(30,7)],note='Known missed square')
        self.assertEqual(int((m.labels==3).sum()),25);self.assertFalse(m.field_inspected)
        m.apply('remove',[3],note='Known false-positive square');self.assertNotIn(3,m.status)
        m.apply('replace',[1],vertices=[(5,10),(13,10),(13,19),(5,19)],note='Known narrower rectangle')
        self.assertEqual(int((m.labels==1).sum()),90)

    def test_pending_export_then_accepted_subset_and_versions(self):
        with tempfile.TemporaryDirectory() as folder:
            m=self.model(folder);first=m.save()
            r=json.loads((first/'review.json').read_text());self.assertEqual(r['summary']['accepted_complete_count'],0)
            m.apply('correct',[1],note='Visual inspection of test region');second=m.save()
            r=json.loads((second/'review.json').read_text());self.assertEqual(r['summary']['accepted_complete_count'],1)
            self.assertNotEqual(first,second);self.assertTrue((first/'reviewed_labels.npz').exists())
            self.assertFalse(r['summary']['review_decisions_complete'])

    def test_resume_and_source_change_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            project=Path(folder);run=project/'run';out=run/'test';out.mkdir(parents=True)
            source=project/'image.png';Image.fromarray(np.full((30,40),200,np.uint8)).save(source)
            labels=self.model('.').labels;np.savez_compressed(out/'arrays.npz',labels=labels)
            (out/'summary.json').write_text(json.dumps({'image_sha256':fingerprint(source)}))
            config={'datasets':[{'id':'test','image':'image.png','nm_per_pixel':None}],
                    'segmentation':{'crop_rows':[0,30],'crop_columns':[0,40]}}
            (run/'config_snapshot.json').write_text(json.dumps(config))
            m,_=prepare_review(project,run,'test');m.apply('correct',[1]);m.save()
            resumed,_=prepare_review(project,run,'test');self.assertEqual(resumed.status[1],'correct')
            Image.fromarray(np.zeros((30,40),np.uint8)).save(source)
            with self.assertRaises(ValueError):prepare_review(project,run,'test')

    def test_polygon_coordinates_and_clipping_rejected(self):
        mask=polygon_mask([(10,2),(12,2),(12,4),(10,4)],(20,20))
        self.assertTrue(mask[3,11]);self.assertFalse(mask[11,3])
        with self.assertRaises(ValueError):polygon_mask([(-1,2),(12,2),(12,4)],(20,20))


if __name__=='__main__':unittest.main()
