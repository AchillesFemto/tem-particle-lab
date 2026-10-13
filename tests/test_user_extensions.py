"""Controlled preprocessing, reference mistakes, distributions and batch failures."""
import csv
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import tifffile
import matplotlib
matplotlib.use('Agg')
from microscopy.user_extensions import preprocess_image,describe,save_distributions,validate_instance_reference,endpoint_measurement
from microscopy.user_images import load_tiff_plane,export_user_analysis
from batch_own_images import run_batch


class ExtensionChecks(unittest.TestCase):
    def test_background_dark_and_bright_preserve_raw(self):
        image=np.full((60,80),1000,np.uint16);image[25:33,35:43]=100
        original=image.copy();processed,bg,_=preprocess_image(image,background_radius=5)
        np.testing.assert_array_equal(image,original);np.testing.assert_array_equal(bg,np.full(image.shape,1000))
        self.assertEqual(processed[28,38],-900);self.assertEqual(processed[5,5],0)
        bright=np.full((60,80),1000,np.uint16);bright[25:33,35:43]=60000
        result,bg,_=preprocess_image(bright,background_radius=5,polarity='bright')
        self.assertEqual(result[28,38],59000);self.assertEqual(result[5,5],0)

    def test_gaussian_reduces_checkerboard_fluctuations(self):
        r,c=np.indices((64,64));image=(128+20*((r+c)%2*2-1)).astype(np.uint8)
        original=image.copy();smoothed,_,_=preprocess_image(image,gaussian_sigma=1)
        self.assertLess(smoothed[5:-5,5:-5].std(),image.std()/10)
        np.testing.assert_array_equal(image,original)
        with self.assertRaises(ValueError):preprocess_image(image,gaussian_sigma=-1)

    def test_descriptive_summary_and_review_border_exclusions(self):
        self.assertEqual(describe([])['n'],0);self.assertIsNone(describe([2])['sample_sd'])
        self.assertEqual(describe([1,2,3])['median'],2);self.assertEqual(describe([1,2,3])['sample_sd'],1)
        rows=[dict(diameter_px=10,feret_max_px=12,ellipse_aspect_ratio=2,touches_crop_border=False,review_status='correct'),
              dict(diameter_px=20,feret_max_px=22,ellipse_aspect_ratio=3,touches_crop_border=False,review_status='pending'),
              dict(diameter_px=100,feret_max_px=110,ellipse_aspect_ratio=4,touches_crop_border=True,review_status='correct')]
        with tempfile.TemporaryDirectory() as folder:
            automatic=save_distributions(folder,rows)
            self.assertEqual(automatic['included_regions'],2);self.assertEqual(automatic['metrics']['diameter_px']['median'],15)
            reviewed=save_distributions(folder,rows,reviewed_only=True)
            self.assertEqual(reviewed['included_regions'],1);self.assertEqual(reviewed['border_excluded'],1);self.assertEqual(reviewed['review_excluded'],1)
            self.assertTrue((Path(folder)/'distributions.png').exists())

    def reference(self):
        ref=np.zeros((40,60),np.uint16);ref[5:15,5:15]=1;ref[5:15,25:35]=2;ref[25:35,5:15]=3
        return ref

    def test_reference_split_miss_and_zero_errors_for_unique_pair(self):
        ref=self.reference();pred=np.zeros_like(ref,np.int32)
        pred[5:15,5:10]=10;pred[5:15,10:15]=11;pred[5:15,25:35]=12
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'ref.tif';tifffile.imwrite(path,ref)
            summary,_=validate_instance_reference(path,pred,pred>0,ref.shape,[0,40,0,60],folder=folder)
            self.assertEqual(summary['possible_splits'],1);self.assertEqual(summary['possible_merges'],0)
            self.assertEqual(summary['references_without_link'],1);self.assertEqual(summary['eligible_matches'],1)
            with (Path(folder)/'reference_measurement_errors.csv').open() as stream:rows=list(csv.DictReader(stream))
            self.assertEqual(float(rows[0]['diameter_px_error_percent']),0)

    def test_reference_merge_and_extra_prediction(self):
        ref=self.reference();pred=np.zeros_like(ref,np.int32);pred[5:15,5:35]=9;pred[25:35,45:55]=11
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'ref.tif';tifffile.imwrite(path,ref)
            summary,_=validate_instance_reference(path,pred,pred>0,ref.shape,[0,40,0,60])
            self.assertEqual(summary['possible_merges'],1);self.assertEqual(summary['references_without_link'],1)
            self.assertEqual(summary['extra_predictions_without_link'],1);self.assertEqual(summary['eligible_matches'],0)

    def test_reference_border_and_invalid_alignment(self):
        ref=np.zeros((40,60),np.uint16);ref[5:15,0:10]=1
        pred=np.zeros_like(ref,np.int32);pred[5:15,1:10]=2
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'ref.tif';tifffile.imwrite(path,ref)
            summary,_=validate_instance_reference(path,pred,pred>0,ref.shape,[0,40,0,60])
            self.assertEqual(summary['eligible_matches'],0)
            with self.assertRaises(ValueError):validate_instance_reference(path,pred,pred>0,(41,60),[0,40,0,60])
            ref[30:32,30:32]=1;tifffile.imwrite(path,ref)
            with self.assertRaisesRegex(ValueError,'one connected particle'):validate_instance_reference(path,pred,pred>0,ref.shape,[0,40,0,60])

    def test_manual_endpoint_geometry(self):
        result=endpoint_measurement([(2,3),(5,7)],.2)
        self.assertEqual(result['span_px'],5);self.assertEqual(result['span_nm'],1)
        self.assertIsNone(endpoint_measurement([(0,0),(3,4)])['span_nm'])
        with self.assertRaises(ValueError):endpoint_measurement([(1,1),(1,1)])

    def test_annotation_export_with_preprocessing_and_raw_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            project=Path(folder);source=project/'image.tif';refpath=project/'reference.tif'
            image=np.full((60,80),1000,np.uint16);image[25:33,35:43]=100
            ref=np.zeros(image.shape,np.uint16);ref[25:33,35:43]=1
            tifffile.imwrite(source,image);tifffile.imwrite(refpath,ref)
            plane,selection=load_tiff_plane(source)
            settings=dict(crop_rows=[0,60],crop_columns=[0,80],threshold=-450,polarity='dark',method='connected',min_area=1,background_radius=5)
            run,summary=export_user_analysis(project,source,plane,selection,settings,reference_path=refpath)
            self.assertEqual(summary['reference_validation']['eligible_matches'],1)
            with np.load(run/'own_image/arrays.npz') as stored:
                np.testing.assert_array_equal(stored['image'],image);self.assertEqual(stored['processed'][28,38],-900)
            self.assertTrue((run/'own_image/preprocessing.png').exists())

    def test_batch_per_image_units_and_failure_record(self):
        with tempfile.TemporaryDirectory() as folder:
            project=Path(folder);a=project/'a.tif';b=project/'b.tif'
            image=np.full((40,60),200,np.uint8);image[10:25,20:40]=20;tifffile.imwrite(a,image)
            tifffile.imwrite(b,image.astype(np.uint16)*200)
            manifest={'defaults':{'method':'connected'},'images':[
                {'id':'a','image':'a.tif','threshold':100,'nm_per_pixel':.2},
                {'id':'b','image':'b.tif','threshold':20000},
                {'id':'missing','image':'missing.tif','threshold':100}]}
            path=project/'batch.json';path.write_text(json.dumps(manifest))
            output,failures=run_batch(project,path);self.assertEqual(failures,1)
            records=json.loads((output/'batch_summary.json').read_text())['records']
            self.assertEqual([r['status'] for r in records],['completed','completed','failed'])
            self.assertEqual(records[0]['units'],'nm');self.assertEqual(records[1]['units'],'px')
            self.assertAlmostEqual(records[0]['median_diameter'],records[1]['median_diameter']*.2)
            report=(project/records[0]['run']/'report.html').read_text()
            self.assertIn(records[0]['run'],report)
            manifest['defaults']['nm_per_pixel']=.2;path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'per image'):run_batch(project,path)


if __name__=='__main__':unittest.main()
