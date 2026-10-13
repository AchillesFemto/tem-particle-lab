"""Compare the frozen rod revision with the original seeds on identical crops."""
import copy
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from skimage.measure import find_contours, regionprops
from microscopy.core import analyse_image, load_config, protocol_matches, save_json, fingerprint
from lesson_25 import reference_instances, overlap_diagnostics


def main():
    project=Path(__file__).resolve().parent
    config=load_config(project/'analysis_config_rods_v2.json')
    protocol=json.loads((project/'validation_protocol_rods_v2.json').read_text())
    if not protocol_matches(config,protocol):
        raise ValueError('Revision differs from the frozen rod protocol.')
    output=project/'results'/'rod_revision_comparison'
    output.mkdir(parents=True,exist_ok=True)
    results=[];measurement_rows=[]
    for entry in config['datasets']:
        arrays={}
        for method in ['local_peaks','prominence_grouping']:
            trial=copy.deepcopy(config)
            trial['segmentation']['seed_method']=method
            folder=output/entry['id']/method
            summary=analyse_image(entry,trial,project,folder)
            summary['method']=method
            results.append(summary)
            with np.load(folder/'arrays.npz') as archive:
                arrays[method]={k:archive[k] for k in ['candidate','labels']}
            with (folder/'matched_errors.csv').open() as stream:
                errors=list(csv.DictReader(stream))
            measurement_rows.append(dict(image=entry['id'],method=method,eligible=len(errors),
                mean_abs_area_error_percent=float(np.mean([abs(float(e['area_error_percent'])) for e in errors])) if errors else None,
                mean_abs_eccentricity_difference=float(np.mean([abs(float(e['eccentricity_difference'])) for e in errors])) if errors else None))
            print(entry['id'],method,'splits',summary['possible_splits'],'merges',summary['possible_merges'],flush=True)
        # Grouping changes particle identity, not which foreground pixels are assigned.
        np.testing.assert_array_equal(arrays['local_peaks']['candidate'],arrays['prominence_grouping']['candidate'])
        np.testing.assert_array_equal(arrays['local_peaks']['labels']>0,arrays['prominence_grouping']['labels']>0)
        if entry['role']=='development':
            rod_preview(entry,config,project,output,arrays)
    save_json(output/'comparison_summary.json',{'protocol_sha256':protocol['sha256'],
        'config_sha256':fingerprint(project/'analysis_config_rods_v2.json'),
        'code_sha256':{name:fingerprint(project/name) for name in ['compare_rods.py','microscopy/core.py','microscopy/seeds.py']},
        'foreground_coverage_identical':True,'results':results,'measurement_errors':measurement_rows})
    rows=''.join(f"<tr><td>{r['id']}</td><td>{r['method']}</td><td>{r['predicted_regions']}</td><td>{r['possible_splits']}</td><td>{r['possible_merges']}</td><td>{r['eligible_matches']}</td><td>{r['mean_abs_diameter_error_percent'] if r['mean_abs_diameter_error_percent'] is not None else 'undefined'}</td></tr>" for r in results)
    (output/'report.html').write_text('''<!doctype html><meta charset="utf-8"><title>Rod seed revision</title>
<style>body{font:17px system-ui;max-width:1100px;margin:40px auto;padding:20px}td,th{padding:10px;border:1px solid #ccc}table{border-collapse:collapse}img{max-width:100%}</style>
<h1>Rod seed revision: identical-crop comparison</h1>
<p>Original local peaks versus prominence grouping, fraction 0.25. Threshold and assigned foreground are identical. Both methods use rows and columns [100:2100], a larger crop than the original lesson. Original results and protocol are preserved.</p>
<table><tr><th>Image</th><th>Method</th><th>Regions</th><th>Possible splits</th><th>Possible merges</th><th>Eligible matches</th><th>Mean absolute diameter error (%)</th></tr>'''+rows+'''</table>
<p>Size errors describe only complete, unique accepted matches. Eligibility changes between methods; these averages do not represent all particles and should not be treated as paired improvement estimates. Area and eccentricity errors are in comparison_summary.json; individual measurements and overlap links are in each method folder.</p>
<h2>One development rod</h2><img src="rod_preview.png" alt="Same rod with original and revised seeds">
<p>Green outlines are manual annotation; cyan outlines are predicted regions; red crosses are seeds. The distance map measures distance to background, so a long rod can have several local peaks along its centre. Grouping shallow peaks removes artificial divisions. A real touching pair with a shallow neck can also be merged incorrectly.</p>
<p>L2-3-B is development data for this revision. L2-2-D was acquired only after freezing the revision; no subsequent retuning. Same source dataset, independent specimens unverified. Calibration unverified: sizes are pixels, never assumed nanometres. These images cannot establish universal performance.</p>
<p>Sources: <a href="https://data-collections.psdi.ac.uk/records/sgvf0-j3g53">Stewart and Da Silva De Sa, PSDI dataset v2</a>, CC BY 4.0; experimental images and manual annotations.
<a href="https://scikit-image.org/docs/0.25.x/api/skimage.morphology.html#skimage.morphology.h_maxima">scikit-image h_maxima documentation</a>.</p>''',encoding='utf-8')
    print('Report:',output/'report.html',flush=True)


def rod_preview(entry,config,project,output,arrays):
    s=config['segmentation'];r0,r1=s['crop_rows'];c0,c1=s['crop_columns']
    image=np.asarray(Image.open(project/entry['image']))[r0:r1,c0:c1]
    if image.ndim==3:image=image[:,:,0]
    dataset=json.loads((project/entry['annotations']).read_text())
    masks,refs=reference_instances(dataset['annotations'],s['crop_rows'],s['crop_columns'])
    *_,links=overlap_diagnostics(masks,arrays['local_peaks']['labels'],.1)
    choices=[i for i,r in enumerate(refs) if r['complete_in_crop'] and links[i].sum()>1]
    if not choices:raise ValueError('No complete split development rod available for demonstration.')
    chosen=max(choices,key=lambda i:np.count_nonzero(masks[i]))
    def measurements(region):
        return dict(area_px=float(region.area),equivalent_diameter_px=float(region.equivalent_diameter_area),eccentricity=float(region.eccentricity))
    example={'reference_id':refs[chosen]['reference_id'],'manual':measurements(regionprops(masks[chosen].astype(np.uint8))[0])}
    for method in arrays:
        ids,*_,method_links=overlap_diagnostics(masks,arrays[method]['labels'],.1)
        related=set(ids[method_links[chosen]])
        example[method]=[dict(label=int(p.label),**measurements(p)) for p in regionprops(arrays[method]['labels']) if p.label in related]
    save_json(output/'example_rod_measurements.json',example)
    rr,cc=np.nonzero(masks[chosen]);a=max(0,rr.min()-30);b=min(image.shape[0],rr.max()+31);x=max(0,cc.min()-30);y=min(image.shape[1],cc.max()+31)
    fig,axes=plt.subplots(1,3,figsize=(13,5),layout='constrained')
    from lesson_22 import foreground_distance
    distance=foreground_distance(arrays['local_peaks']['candidate'])
    for ax,method in zip(axes[:2],['local_peaks','prominence_grouping']):
        ax.imshow(image[a:b,x:y],cmap='gray',vmin=0,vmax=255)
        labels=arrays[method]['labels'][a:b,x:y]
        for label in np.unique(labels[labels>0]):
            for contour in find_contours(np.pad(labels==label,1),.5):
                ax.plot(contour[:,1]-1,contour[:,0]-1,color='cyan',linewidth=1)
        for contour in find_contours(np.pad(masks[chosen][a:b,x:y],1),.5):
            ax.plot(contour[:,1]-1,contour[:,0]-1,color='lime',linewidth=1)
        with np.load(output/entry['id']/method/'arrays.npz') as archive:
            seed_r,seed_c=np.nonzero(archive['markers'][a:b,x:y])
        ax.scatter(seed_c,seed_r,c='red',marker='x',s=45)
        ax.set_title('Original seeds' if method=='local_peaks' else 'Grouped seeds')
    im=axes[2].imshow(distance[a:b,x:y],cmap='magma');fig.colorbar(im,ax=axes[2],label='Distance to background (pixels)')
    axes[2].set_title('Distance ridge inside the rod')
    for ax in axes:ax.set_axis_off()
    fig.suptitle('Development manual particle ID '+str(refs[chosen]['reference_id']))
    fig.savefig(output/'rod_preview.png',dpi=150);plt.close(fig)


if __name__=='__main__':main()
