"""Measure saved particles and compare rod dimensions against eligible references."""
import argparse
import csv
import json
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.spatial.distance import cdist
from skimage.measure import regionprops,find_contours
from lesson_25 import reference_instances
from microscopy.core import save_csv,save_json,fingerprint
from microscopy.measurements import measure_labels,shape_measurements
from microscopy.run_selection import resolve_analysis


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',help='Existing run path; default: newest compatible analysis run.')
    parser.add_argument('--dataset',help='Dataset ID; default: first successful development dataset, then another successful dataset.')
    args=parser.parse_args();project=Path(__file__).resolve().parent
    try:run,dataset=resolve_analysis(project,args.run,args.dataset)
    except ValueError as error:parser.error(str(error))
    print('Using run:',run,'; dataset:',dataset,flush=True)
    config=json.loads((run/'config_snapshot.json').read_text());entry=next(e for e in config['datasets'] if e['id']==dataset)
    folder=run/dataset;summary=json.loads((folder/'summary.json').read_text())
    if entry.get('kind')=='user_image':
        if fingerprint(project/entry['image'])!=summary['image_sha256']:raise ValueError('Source TIFF changed since analysis.')
        print('Measurements already exported:',folder/'regions.csv')
        print('No reference annotations supplied: diameter and shape measurements are available, but reference-error metrics are not calculated.')
        return
    image_path=project/entry['image'];annotation_path=project/entry['annotations']
    for path,key in [(image_path,'image_sha256'),(annotation_path,'annotation_sha256')]:
        if fingerprint(path)!=summary[key]:raise ValueError('Source input changed since this run.')
    with np.load(folder/'arrays.npz') as archive:labels=archive['labels']
    with (folder/'overlap_links.csv').open() as stream:links=list(csv.DictReader(stream))
    s=config['segmentation'];annotations=json.loads(annotation_path.read_text())
    masks,refs=reference_instances(annotations['annotations'],s['crop_rows'],s['crop_columns'])
    references={r['reference_id']:mask for r,mask in zip(refs,masks)}
    properties={p.label:p for p in regionprops(labels)}
    rows=measure_labels(labels,entry['nm_per_pixel']);comparisons=[]
    for link in links:
        if link['eligible']!='True':continue
        label=int(link['label']);reference_id=int(link['reference_id'])
        manual=shape_measurements(regionprops(references[reference_id].astype(np.uint8))[0])
        automatic=shape_measurements(properties[label])
        row=dict(label=label,reference_id=reference_id,iou=float(link['iou']))
        for name in ['feret_max_px','ellipse_major_px','ellipse_minor_px','ellipse_aspect_ratio']:
            row['manual_'+name]=manual[name];row['automatic_'+name]=automatic[name]
            row[name+'_error_percent']=None if manual[name] in [None,0] or automatic[name] is None else 100*(automatic[name]/manual[name]-1)
        comparisons.append(row)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:6]
    output=folder/'rod_measurements'/stamp;output.mkdir(parents=True)
    save_csv(output/'automatic_regions.csv',rows,list(rows[0]) if rows else ['label'])
    save_csv(output/'reference_comparison.csv',comparisons,list(comparisons[0]) if comparisons else ['label','reference_id','iou'])
    report={'source_arrays_sha256':fingerprint(folder/'arrays.npz'),'source_run':str(run.resolve()),
            'nm_per_pixel':entry['nm_per_pixel'],'eligible_reference_pairs':len(comparisons),
            'mean_absolute_error_percent':{},
            'interpretation':'Outline span and moment-ellipse dimensions describe 2D projected masks. Eligible one-to-one complete pairs only; not all-particle accuracy.'}
    for name in ['feret_max_px','ellipse_major_px','ellipse_minor_px','ellipse_aspect_ratio']:
        errors=[abs(r[name+'_error_percent']) for r in comparisons if r[name+'_error_percent'] is not None]
        report['mean_absolute_error_percent'][name]=float(np.mean(errors)) if errors else None
    if comparisons:
        example=next((r for r in comparisons if r['label']==32),comparisons[0])
        p=properties[example['label']];r0,c0,r1,c1=p.bbox
        image=np.asarray(Image.open(image_path))[s['crop_rows'][0]:s['crop_rows'][1],s['crop_columns'][0]:s['crop_columns'][1]]
        if image.ndim==3:image=image[:,:,0]
        fig,ax=plt.subplots(figsize=(8,7),layout='constrained');ax.imshow(image,cmap='gray',vmin=0,vmax=255)
        for line in find_contours(np.pad(p.image,1),.5):ax.plot(line[:,1]+c0-1,line[:,0]+r0-1,color='cyan',lw=1,label=None)
        points=np.concatenate(find_contours(np.pad(p.image_convex,2),.5))
        i,j=np.unravel_index(cdist(points,points).argmax(),(len(points),len(points)))
        endpoints=points[[i,j]]+np.array([r0-2,c0-2])
        ax.plot(endpoints[:,1],endpoints[:,0],color='darkorange',lw=2,label='Maximum Feret span')
        r,c=p.centroid;angle=p.orientation
        for length,dr,dc,color,title in [(p.axis_major_length,np.cos(angle),np.sin(angle),'red','Ellipse major axis'),(p.axis_minor_length,-np.sin(angle),np.cos(angle),'deepskyblue','Ellipse minor axis')]:
            ax.plot([c-dc*length/2,c+dc*length/2],[r-dr*length/2,r+dr*length/2],color=color,lw=1.5,label=title)
        ax.set_xlim(c0-70,c1+70);ax.set_ylim(r1+70,r0-70);ax.legend(loc='upper left',fontsize=9)
        ax.set_xlabel('Crop column (pixels)');ax.set_ylabel('Crop row (pixels)')
        m=shape_measurements(p)
        ax.set_title(f"Particle {p.label}: Feret {m['feret_max_px']:.1f} px; ellipse {m['ellipse_major_px']:.1f} x {m['ellipse_minor_px']:.1f} px\nEllipse axes summarize shape; they are not literal endpoints.")
        fig.savefig(output/'rod_dimensions.png',dpi=140);plt.close(fig)
        report['example']=example
    save_json(output/'summary.json',report)
    print('Measurements:',output,flush=True);print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
