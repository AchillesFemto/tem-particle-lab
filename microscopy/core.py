"""Configuration validation, segmentation, and object-level assessment."""
import csv
import hashlib
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.measure import regionprops, find_contours
from skimage.segmentation import watershed

from lesson_22 import foreground_distance
from lesson_23 import distance_peak_seeds, suppress_nearby_seeds
from lesson_25 import reference_instances, overlap_diagnostics
from .seeds import collapse_shallow_peak_seeds
from .measurements import shape_measurements, SHAPE_FIELDS


def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')


def save_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer=csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def load_config(path):
    config=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if config.get('schema_version') != 1: raise ValueError('Expected configuration schema version 1.')
    s=config['segmentation']; v=config['validation']; t=config['tracking']; u=config['uncertainty']
    def positive(value, name):
        if not isinstance(value,(int,float)) or not np.isfinite(value) or value<=0:
            raise ValueError(name+' must be finite and positive.')
    if not isinstance(s['threshold'],int) or not 0<=s['threshold']<=255:
        raise ValueError('Threshold must be an integer from 0 to 255.')
    for name in ['crop_rows','crop_columns']:
        a=s[name]
        if len(a)!=2 or any(not isinstance(x,int) for x in a) or not 0<=a[0]<a[1]:
            raise ValueError('Crop intervals must contain ordered nonnegative integer endpoints.')
    if not isinstance(s['window_size'],int) or s['window_size']<3 or s['window_size']%2==0:
        raise ValueError('Seed window must be an odd integer of at least three.')
    for key in ['min_peak_height_px','min_seed_separation_px']: positive(s[key],key)
    if s.get('seed_method','local_peaks') not in ['local_peaks','prominence_grouping']:raise ValueError('Unknown seed method.')
    if s.get('seed_method')=='prominence_grouping' and not 0<s['peak_prominence_fraction']<=1:raise ValueError('Prominence fraction must be in (0,1].')
    for key in ['link_fraction','min_match_iou']:
        if not 0<v[key]<=1: raise ValueError(key+' must be in (0,1].')
    if not config['datasets']:raise ValueError('Configure at least one image.')
    ids=set()
    for entry in config['datasets']:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',entry['id']) or entry['id'] in ids:
            raise ValueError('Use unique safe dataset IDs.')
        ids.add(entry['id'])
        if entry['role'] not in ['development','held_out_image']:raise ValueError('Unknown dataset role.')
        if entry['nm_per_pixel'] is not None:positive(entry['nm_per_pixel'],'nm_per_pixel')
    for key in ['half_width_px','search_radius_px']:
        if not isinstance(t[key],int) or t[key]<1:raise ValueError(key+' must be a positive integer.')
    for key in ['sigma_px','nm_per_pixel','acquisition_fps']:positive(t[key],key)
    if not 0<t['min_score']<=1:raise ValueError('min_score must be in (0,1].')
    if len(t['initial_row_column'])!=2 or any(not isinstance(x,int) or x<0 for x in t['initial_row_column']):
        raise ValueError('Initial tracking position must be a pair of nonnegative integers.')
    if not isinstance(t['repeats_per_frame'],int) or t['repeats_per_frame']<2:raise ValueError('At least two manual repeats are needed for repeatability.')
    if not isinstance(u['synthetic_runs'],int) or u['synthetic_runs']<1:raise ValueError('At least one synthetic run is required.')
    positive(u['synthetic_noise_sd'],'synthetic_noise_sd')
    if not u['sensitivity_sigmas_px']:raise ValueError('Configure at least one sensitivity setting.')
    for x in u['sensitivity_sigmas_px']:positive(x,'sensitivity sigma')
    if not isinstance(u['random_seed'],int) or u['random_seed']<0:raise ValueError('Random seed must be a nonnegative integer.')
    if not t['review_frames'] or any(not isinstance(f,int) or f<0 for f in t['review_frames']):raise ValueError('Review frames must be nonnegative integers.')
    return config


def protocol_matches(config, protocol):
    settings={'segmentation':config['segmentation'],'validation':config['validation']}
    digest=hashlib.sha256(json.dumps(settings,sort_keys=True).encode()).hexdigest()
    return digest==protocol['sha256'] and settings==protocol['frozen_parameters']


def segment(roi, settings):
    candidate=roi<settings['threshold']
    markers=np.zeros(roi.shape,dtype=np.int32)
    if not np.any(candidate) or np.all(candidate):
        return candidate, markers.copy(), markers, 0, ['Foreground/background separation is degenerate.']
    distance=foreground_distance(candidate)
    raw=distance_peak_seeds(distance,settings['window_size'],settings['min_peak_height_px'])
    seeds=suppress_nearby_seeds(distance,raw,candidate,settings['min_seed_separation_px'])
    grouping=[]
    if settings.get('seed_method','local_peaks')=='prominence_grouping':
        seeds,grouping=collapse_shallow_peak_seeds(distance,seeds,candidate,settings['peak_prominence_fraction'])
    for number,(row,column) in enumerate(seeds,start=1):markers[row,column]=number
    labels=watershed(-distance,markers,mask=candidate,connectivity=np.ones((3,3),bool)) if len(seeds) else markers.copy()
    notes=[] if len(seeds) else ['No seeds: all threshold foreground remains unassigned.']
    if grouping:notes.append('Shallow-peak grouping: '+str(grouping))
    return candidate, labels, markers, len(raw), notes


def iou_score(a,b):
    union=np.count_nonzero(a|b)
    return float(np.count_nonzero(a&b)/union) if union else None


def analyse_image(entry, config, project, output):
    output.mkdir(parents=True,exist_ok=True)
    image_path=project/entry['image']; annotation_path=project/entry['annotations']
    with Image.open(image_path) as source:image=np.array(source)
    if image.ndim==3 and image.shape[2] in [3,4]:
        if not np.array_equal(image[:,:,0],image[:,:,1]) or not np.array_equal(image[:,:,0],image[:,:,2]):
            raise ValueError('RGB planes differ; explicitly establish grayscale conversion before analysis.')
        image=image[:,:,0]
    if image.ndim!=2 or image.dtype!=np.uint8:raise ValueError('This configured pipeline expects grayscale uint8 images.')
    s=config['segmentation'];v=config['validation']
    r0,r1=s['crop_rows'];c0,c1=s['crop_columns']
    if r1>image.shape[0] or c1>image.shape[1]:raise ValueError('Configured crop exceeds the source image.')
    roi=image[r0:r1,c0:c1]
    candidate,labels,markers,raw_count,notes=segment(roi,s)
    dataset=json.loads(annotation_path.read_text(encoding='utf-8'))
    if len(dataset['images'])!=1 or dataset['images'][0]['file_name']!=image_path.name:
        raise ValueError('Annotations must identify the same single source image.')
    if (dataset['images'][0]['height'],dataset['images'][0]['width'])!=image.shape:
        raise ValueError('Annotation dimensions disagree with image dimensions.')
    image_id=dataset['images'][0]['id']
    masks,refs=reference_instances([a for a in dataset['annotations'] if a['image_id']==image_id],s['crop_rows'],s['crop_columns'])
    reference=np.logical_or.reduce(masks) if masks else np.zeros(roi.shape,bool)
    ids,intersections,iou,fractions,links=overlap_diagnostics(masks,labels,v['link_fraction'])
    ref_degree=links.sum(axis=1); pred_degree=links.sum(axis=0)
    components,component_count=ndimage.label(candidate,np.ones((3,3),bool))
    border_ids=np.unique(np.concatenate([components[0],components[-1],components[:,0],components[:,-1]]))
    properties={p.label:p for p in regionprops(labels)}
    border={int(p):bool(components[labels==p][0] in border_ids) for p in ids}
    rows=[]
    for label,p in properties.items():
        scale=entry['nm_per_pixel']
        rows.append({'label':label,'area_px':int(p.area),'diameter_px':p.equivalent_diameter_area,
                     'eccentricity':p.eccentricity,'parent_touches_border':border[label],
                     'area_nm2':None if scale is None else p.area*scale**2,
                     'diameter_nm':None if scale is None else p.equivalent_diameter_area*scale,
                     **shape_measurements(p,scale)})
    save_csv(output/'regions.csv',rows,['label','area_px','diameter_px','eccentricity','parent_touches_border','area_nm2','diameter_nm']+SHAPE_FIELDS)
    edges=[];errors=[]
    for i,j in zip(*np.nonzero(links)):
        unique=bool(ref_degree[i]==1 and pred_degree[j]==1)
        accepted=bool(unique and iou[i,j]>=v['min_match_iou'])
        eligible=bool(accepted and refs[i]['complete_in_crop'] and not border[int(ids[j])])
        edges.append({'reference_id':refs[i]['reference_id'],'label':int(ids[j]),'iou':float(iou[i,j]),
                      'unique':unique,'accepted':accepted,'eligible':eligible})
        if eligible:
            ref=regionprops(masks[i].astype(np.uint8))[0]; pred=properties[int(ids[j])]
            errors.append({'reference_id':refs[i]['reference_id'],'label':int(ids[j]),
                           'area_error_percent':100*(pred.area/ref.area-1),
                           'diameter_error_percent':100*(pred.equivalent_diameter_area/ref.equivalent_diameter_area-1),
                           'eccentricity_difference':pred.eccentricity-ref.eccentricity})
    save_csv(output/'overlap_links.csv',edges,['reference_id','label','iou','unique','accepted','eligible'])
    save_csv(output/'matched_errors.csv',errors,['reference_id','label','area_error_percent','diameter_error_percent','eccentricity_difference'])
    save_csv(output/'reference_diagnostics.csv',[
        {'reference_id':r['reference_id'],'complete_in_crop':r['complete_in_crop'],'linked_regions':int(ref_degree[i])}
        for i,r in enumerate(refs)],['reference_id','complete_in_crop','linked_regions'])
    summary={'id':entry['id'],'role':entry['role'],'image_sha256':fingerprint(image_path),
             'annotation_sha256':fingerprint(annotation_path),'threshold_iou':iou_score(reference,candidate),
             'assigned_foreground_iou':iou_score(reference,labels>0),'predicted_regions':len(ids),
             'reference_instances':len(refs),'complete_references':sum(r['complete_in_crop'] for r in refs),
             'references_without_link':int((ref_degree==0).sum()),
             'complete_references_without_link':int(sum(r['complete_in_crop'] and ref_degree[i]==0 for i,r in enumerate(refs))),
             'possible_splits':int((ref_degree>1).sum()),'possible_merges':int((pred_degree>1).sum()),
             'extra_predictions_without_link':int((pred_degree==0).sum()),
             'eligible_matches':len(errors),'unassigned_foreground_pixels':int((candidate&(labels==0)).sum()),
             'seed_method':s.get('seed_method','local_peaks'),'raw_seed_count':raw_count,'retained_seed_count':int((markers>0).sum()),
             'component_count':component_count,'nm_per_pixel':entry['nm_per_pixel'],
             'mean_abs_diameter_error_percent':float(np.mean([abs(e['diameter_error_percent']) for e in errors])) if errors else None,
             'notes':notes+(['Physical calibration unverified; sizes reported in pixels only.'] if entry['nm_per_pixel'] is None else [])}
    save_json(output/'summary.json',summary)
    np.savez_compressed(output/'arrays.npz',candidate=candidate,labels=labels,markers=markers,reference=reference)
    fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
    for ax in axes:ax.imshow(roi,cmap='gray',vmin=0,vmax=255,interpolation='nearest');ax.set_axis_off()
    if masks:axes[0].contour(reference,levels=[.5],colors=['lime'],linewidths=.8)
    if np.any(candidate):axes[1].contour(candidate,levels=[.5],colors=['cyan'],linewidths=.8)
    for p in properties.values():
        # Trace each small bounding box, avoiding a full-size contour array per region.
        r0,c0,_,_=p.bbox
        for outline in find_contours(np.pad(p.image,1),.5):
            axes[2].plot(outline[:,1]+c0-1,outline[:,0]+r0-1,color='cyan',linewidth=.7)
        rr,cc=p.centroid;axes[2].text(cc,rr,str(p.label),color='yellow',fontsize=7)
    axes[0].set_title('Manual foreground');axes[1].set_title('Configured threshold selection');axes[2].set_title('Watershed regions')
    fig.suptitle(entry['id']+' - '+entry['role']);fig.savefig(output/'comparison.png',dpi=130);plt.close(fig)
    return summary
