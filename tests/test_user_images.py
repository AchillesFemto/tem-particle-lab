"""User TIFF planes, native thresholds, calibration and review integration."""
import csv
import json
from pathlib import Path
import tempfile
import unittest
import matplotlib
matplotlib.use('Agg')
import numpy as np
import tifffile
from microscopy.user_images import inspect_tiff,load_tiff_plane,segment_user_plane,export_user_analysis
from microscopy.particle_review import prepare_review
from microscopy.run_selection import resolve_analysis


class OwnImageChecks(unittest.TestCase):
    def discs(self,dtype=np.uint16):
        r,c=np.indices((100,140))
        first=(r-30)**2+(c-35)**2<=10**2
        second=(r-65)**2+(c-100)**2<=15**2
        return np.where(first|second,10000,50000).astype(dtype)

    def settings(self,plane,**changes):
        values=dict(crop_rows=[0,plane.shape[0]],crop_columns=[0,plane.shape[1]],threshold=30000,
                    polarity='dark',method='connected',min_area=1,window_size=11,min_peak_height=2,
                    min_seed_separation=5,prominence=.25)
        values.update(changes);return values

    def test_uint16_native_threshold_known_discs_and_export(self):
        with tempfile.TemporaryDirectory() as folder:
            project=Path(folder);path=project/'input.tif';original=self.discs();tifffile.imwrite(path,original)
            plane,selection=load_tiff_plane(path);np.testing.assert_array_equal(plane,original)
            self.assertEqual(plane.dtype,np.uint16)
            run,summary=export_user_analysis(project,path,plane,selection,self.settings(plane),.2)
            self.assertEqual(summary['predicted_regions'],2);self.assertEqual(summary['validation_status'],'not performed: no reference annotations supplied')
            with (run/'own_image/regions.csv').open() as stream:rows=list(csv.DictReader(stream))
            self.assertAlmostEqual(float(rows[0]['diameter_px']),20,delta=.5)
            self.assertAlmostEqual(float(rows[1]['diameter_px']),30,delta=.5)
            self.assertAlmostEqual(float(rows[0]['diameter_nm']),4,delta=.1)
            self.assertFalse(summary['calibration_verified_by_software'])
            self.assertTrue((run/'report.html').exists())
            selected,identity=resolve_analysis(project);self.assertEqual((selected,identity),(run,'own_image'))
            model,image=prepare_review(project,run,'own_image')
            np.testing.assert_array_equal(image,original);self.assertEqual(len(model.status),2)
            self.assertTrue(all(v=='pending' for v in model.status.values()))
            model.apply('correct',[1],note='Known synthetic disc');revision=model.save()
            with (revision/'accepted_complete_regions.csv').open() as stream:
                accepted=list(csv.DictReader(stream))
            self.assertAlmostEqual(float(accepted[0]['diameter_nm']),4,delta=.1)

    def test_multipage_requires_selection_and_review_uses_correct_page(self):
        with tempfile.TemporaryDirectory() as folder:
            project=Path(folder);path=project/'stack.tif'
            with tifffile.TiffWriter(path) as writer:
                writer.write(np.full((100,140),50000,np.uint16),photometric='minisblack')
                writer.write(self.discs(),photometric='minisblack')
            self.assertEqual(len(inspect_tiff(path)['pages']),2)
            with self.assertRaisesRegex(ValueError,'multiple pages'):load_tiff_plane(path)
            plane,selection=load_tiff_plane(path,page=1)
            run,summary=export_user_analysis(project,path,plane,selection,self.settings(plane))
            self.assertEqual(summary['predicted_regions'],2)
            _,review_image=prepare_review(project,run,'own_image');np.testing.assert_array_equal(review_image,self.discs())
            with self.assertRaises(ValueError):load_tiff_plane(path,page=2)

    def test_rgb_explicit_channel_and_identical_planes(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'rgb.tif';r,c=np.indices((20,30))
            rgb=np.stack([r,c,r+c],axis=-1).astype(np.uint8);tifffile.imwrite(path,rgb,photometric='rgb')
            with self.assertRaisesRegex(ValueError,'Choose --channel'):load_tiff_plane(path)
            plane,selection=load_tiff_plane(path,channel=2);np.testing.assert_array_equal(plane,rgb[:,:,2])
            self.assertEqual(selection['channel'],2)
            with self.assertRaises(ValueError):load_tiff_plane(path,channel=3)
            tifffile.imwrite(path,np.repeat(rgb[:,:,0,None],3,axis=2),photometric='rgb')
            plane,selection=load_tiff_plane(path);np.testing.assert_array_equal(plane,rgb[:,:,0])
            self.assertIn('Identical RGB',selection['channel_handling'])

    def test_planar_rgb_selection(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'planar.tif';image=np.arange(3*20*30,dtype=np.uint16).reshape(3,20,30)
            tifffile.imwrite(path,image,photometric='rgb',planarconfig='separate')
            plane,_=load_tiff_plane(path,channel=1);np.testing.assert_array_equal(plane,image[1])

    def test_uint8_and_float_bright_thresholds(self):
        for dtype in [np.uint8,np.float32]:
            plane=np.zeros((40,60),dtype=dtype);plane[10:25,20:40]=100
            candidate,labels,_,_=segment_user_plane(plane,50,polarity='bright')
            self.assertEqual(candidate.sum(),300);self.assertEqual(labels.max(),1)
            _,watershed,_,stats=segment_user_plane(plane,50,polarity='bright',method='watershed',window_size=5)
            self.assertEqual(watershed.max(),1);self.assertEqual(stats['seedless_foreground_pixels'],0)

    def test_small_region_filter_and_degenerate_foreground(self):
        plane=np.full((20,30),200,np.uint8);plane[3:8,3:8]=10;plane[15,20]=10
        _,labels,_,stats=segment_user_plane(plane,100,min_area=2)
        self.assertEqual(len(np.unique(labels[labels>0])),1);self.assertEqual(stats['filtered_regions'],1)
        self.assertEqual(stats['filtered_foreground_pixels'],1);self.assertEqual(stats['seedless_foreground_pixels'],0)
        _,empty,_,_=segment_user_plane(plane,0);self.assertEqual(empty.max(),0)
        _,all_fg,notes,_=segment_user_plane(plane,256);self.assertEqual(all_fg.max(),0)
        self.assertTrue(any('All pixels' in note for note in notes))

    def test_invalid_pixels_crop_calibration_and_source_change(self):
        with tempfile.TemporaryDirectory() as folder:
            project=Path(folder);path=project/'input.tif';plane=self.discs();tifffile.imwrite(path,plane)
            image,selection=load_tiff_plane(path)
            with self.assertRaises(ValueError):export_user_analysis(project,path,image,selection,self.settings(image,crop_rows=[0,101]))
            with self.assertRaises(ValueError):export_user_analysis(project,path,image,selection,self.settings(image),-1)
            tifffile.imwrite(path,np.zeros_like(plane))
            with self.assertRaisesRegex(ValueError,'changed after loading'):export_user_analysis(project,path,image,selection,self.settings(image))
            invalid=np.zeros((10,10),np.float32);invalid[2,2]=np.nan;tifffile.imwrite(path,invalid)
            with self.assertRaisesRegex(ValueError,'NaN'):load_tiff_plane(path)

    def test_compressed_tiff_and_pixel_only_empty_csv(self):
        with tempfile.TemporaryDirectory() as folder:
            project=Path(folder);path=project/'compressed.tif';tifffile.imwrite(path,self.discs(),compression='lzw')
            plane,selection=load_tiff_plane(path);np.testing.assert_array_equal(plane,self.discs())
            run,_=export_user_analysis(project,path,plane,selection,self.settings(plane,threshold=0))
            with (run/'own_image/regions.csv').open() as stream:
                reader=csv.DictReader(stream);self.assertIn('diameter_nm',reader.fieldnames);self.assertEqual(list(reader),[])


if __name__=='__main__':unittest.main()
