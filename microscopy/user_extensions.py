"""Optional preprocessing, descriptive distributions and instance references."""
from collections import Counter
from pathlib import Path
import numpy as np
import tifffile
from scipy import ndimage
from .core import save_json,save_csv,fingerprint
from .measurements import measure_labels


def preprocess_image(image,gaussian_sigma=0,background_radius=0,polarity='dark'):
    """Return working floats and optional background; preserve source pixels."""
    if image.ndim!=2 or not np.all(np.isfinite(image)):raise ValueError('Preprocessing requires a finite 2D image.')
    if not np.isfinite(gaussian_sigma) or gaussian_sigma<0:raise ValueError('Gaussian sigma must be finite and nonnegative.')
    if not isinstance(background_radius,int) or background_radius<0:raise ValueError('Background half-window must be a nonnegative integer.')
    if polarity not in ['dark','bright']:raise ValueError('Choose dark or bright polarity.')
    working=image.astype(float,copy=True);background=None;notes=[]
    if gaussian_sigma:
        working=ndimage.gaussian_filter(working,gaussian_sigma,mode='reflect')
        notes.append('Gaussian smoothing reduces fine fluctuations but blurs edges; sigma is in pixels.')
    if background_radius:
        operation=ndimage.grey_closing if polarity=='dark' else ndimage.grey_opening
        background=operation(working,size=2*background_radius+1,mode='reflect')
        working=working-background
        notes.append('Background estimated with a square morphological window and subtracted. Choose a window larger than feature widths; large/dense objects can bias the estimate. Threshold now applies to corrected intensities, often negative for dark particles.')
    return working,background,notes


def describe(values):
    values=np.asarray(values,float)
    if not len(values):return dict(n=0,mean=None,median=None,sample_sd=None,q25=None,q75=None,min=None,max=None)
    if not np.all(np.isfinite(values)):raise ValueError('Distribution values must be finite.')
    return dict(n=len(values),mean=float(values.mean()),median=float(np.median(values)),
                sample_sd=float(values.std(ddof=1)) if len(values)>1 else None,
                q25=float(np.percentile(values,25)),q75=float(np.percentile(values,75)),
                min=float(values.min()),max=float(values.max()))


def save_distributions(folder,rows,nm_per_pixel=None,reviewed_only=False,bins=12):
    from matplotlib.figure import Figure
    if not isinstance(bins,int) or not 1<=bins<=512:raise ValueError('Histogram bins must be an integer from 1 to 512.')
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    complete=[r for r in rows if str(r.get('touches_crop_border',False)).lower() not in ['true','1']]
    chosen=[r for r in complete if not reviewed_only or r.get('review_status')=='correct']
    units='nm' if nm_per_pixel is not None else 'px'
    metrics=[('diameter_'+units,'Area-equivalent diameter',units),('feret_max_'+units,'Maximum Feret span',units),('ellipse_aspect_ratio','Ellipse aspect ratio','dimensionless')]
    summary=dict(cohort='reviewed Correct, complete regions' if reviewed_only else 'complete automatic predictions; not validated',
                 input_regions=len(rows),border_excluded=len(rows)-len(complete),
                 review_excluded=len(complete)-len(chosen),included_regions=len(chosen),
                 histogram_bins=bins,metrics={},
                 caveat='Descriptive per-image statistics, not confidence intervals or independent experimental replicates. Exclusions and segmentation can bias the distribution.')
    fig=Figure(figsize=(12,4),layout='constrained');axes=fig.subplots(1,3)
    for ax,(field,title,unit) in zip(axes,metrics):
        values=[float(r[field]) for r in chosen if r.get(field) not in [None,'']]
        summary['metrics'][field]=dict(units=unit,**describe(values))
        if values:ax.hist(values,bins=bins,color='steelblue',edgecolor='white')
        else:ax.text(.5,.5,'No eligible measurements',ha='center',va='center',transform=ax.transAxes)
        ax.set_xlabel(title+' ('+unit+')');ax.set_ylabel('Region count');ax.set_title('n = '+str(len(values)))
    fig.suptitle(summary['cohort']);fig.savefig(folder/'distributions.png',dpi=140);fig.clear()
    save_json(folder/'distribution_summary.json',summary)
    return summary


def validate_instance_reference(reference_path,labels,candidate,full_shape,crop,nm_per_pixel=None,link_fraction=.1,min_match_iou=.5,folder=None):
    """Compare an aligned full-plane instance-label TIFF without dense mask stacks."""
    if not 0<link_fraction<=1 or not 0<min_match_iou<=1:raise ValueError('Reference overlap cutoffs must be in (0,1].')
    with tifffile.TiffFile(reference_path) as tif:
        if len(tif.pages)!=1:raise ValueError('Reference must be a single-page, full-plane instance-label TIFF.')
        reference=tif.pages[0].asarray()
    if reference.ndim!=2 or reference.shape!=tuple(full_shape) or reference.dtype.kind not in 'uib' or np.any(reference<0):
        raise ValueError('Reference must be a nonnegative integer 2D label image matching the full selected image plane. Background = 0; distinct particles need distinct IDs.')
    full_ids,full_counts=np.unique(reference[reference>0],return_counts=True)
    for identity in full_ids:
        if ndimage.label(reference==identity,np.ones((3,3),bool))[1]!=1:
            raise ValueError('Each reference ID must describe one connected particle; a binary mask of disconnected objects is not an instance reference.')
    r0,r1,c0,c1=crop;ref=reference[r0:r1,c0:c1]
    if ref.shape!=labels.shape:raise ValueError('Reference crop and predictions have different shapes.')
    ref_ids=np.unique(ref);pred_ids=np.unique(labels)
    ref_index={int(i):j for j,i in enumerate(ref_ids)};pred_index={int(i):j for j,i in enumerate(pred_ids)}
    width=len(pred_ids);pairs=Counter()
    for start in range(0,len(labels),128):
        ri=np.searchsorted(ref_ids,ref[start:start+128]).ravel();pi=np.searchsorted(pred_ids,labels[start:start+128]).ravel()
        encoded,counts=np.unique(ri*width+pi,return_counts=True)
        pairs.update({int(k):int(n) for k,n in zip(encoded,counts)})
    ref_area=Counter();pred_area=Counter()
    for encoded,n in pairs.items():
        i,j=divmod(encoded,width);ref_area[int(ref_ids[i])]+=n;pred_area[int(pred_ids[j])]+=n
    links=[];ref_degree=Counter();pred_degree=Counter()
    for encoded,n in pairs.items():
        i,j=divmod(encoded,width);r=int(ref_ids[i]);p=int(pred_ids[j])
        if r==0 or p==0:continue
        iou=n/(ref_area[r]+pred_area[p]-n)
        if n/min(ref_area[r],pred_area[p])>=link_fraction:
            links.append(dict(reference_id=r,label=p,iou=iou));ref_degree[r]+=1;pred_degree[p]+=1
    full_border_ids=set(np.concatenate([reference[0],reference[-1],reference[:,0],reference[:,-1]]).tolist())
    complete={int(i):ref_area[int(i)]==int(n) and int(i) not in full_border_ids for i,n in zip(full_ids,full_counts)}
    predicted={r['label']:r for r in measure_labels(labels,nm_per_pixel)}
    errors=[]
    for link in links:
        r=link['reference_id'];p=link['label'];unique=ref_degree[r]==1 and pred_degree[p]==1
        accepted=unique and link['iou']>=min_match_iou
        eligible=accepted and complete[r] and not predicted[p]['touches_crop_border']
        link.update(unique=unique,accepted=accepted,eligible=eligible)
        if eligible:
            manual=measure_labels((ref==r).astype(np.int32),nm_per_pixel)[0]
            row=dict(reference_id=r,label=p,iou=link['iou'])
            for field in ['area_px','diameter_px','feret_max_px','ellipse_major_px','ellipse_minor_px','ellipse_aspect_ratio']:
                a=manual[field];b=predicted[p][field]
                row['reference_'+field]=a;row['predicted_'+field]=b
                row[field+'_error_percent']=None if a in [None,0] or b is None else 100*(b/a-1)
            errors.append(row)
    visible=[int(i) for i in ref_ids if i>0]
    union=int(((ref>0)|candidate).sum());intersection=int(((ref>0)&candidate).sum())
    summary=dict(status='compared with user-supplied instance reference',reference_sha256=fingerprint(reference_path),
                 reference_instances_in_crop=len(visible),possible_splits=sum(ref_degree[i]>1 for i in visible),
                 possible_merges=sum(pred_degree[p]>1 for p in predicted),
                 references_without_link=sum(ref_degree[i]==0 for i in visible),
                 extra_predictions_without_link=sum(pred_degree[p]==0 for p in predicted),
                 eligible_matches=len(errors),threshold_iou=intersection/union if union else None,
                 link_fraction=link_fraction,min_match_iou=min_match_iou,
                 registration_verified_by_software=False,
                 caveat='Same shape does not prove alignment or independent annotation. Errors refer to complete, unique accepted pairs, not all-particle accuracy.')
    summary['mean_absolute_error_percent']={}
    for field in ['area_px','diameter_px','feret_max_px','ellipse_major_px','ellipse_minor_px','ellipse_aspect_ratio']:
        values=[abs(r[field+'_error_percent']) for r in errors if r[field+'_error_percent'] is not None]
        summary['mean_absolute_error_percent'][field]=float(np.mean(values)) if values else None
    if folder:
        folder=Path(folder);save_json(folder/'validation_summary.json',summary)
        save_csv(folder/'overlap_links.csv',links,['reference_id','label','iou','unique','accepted','eligible'])
        save_csv(folder/'reference_measurement_errors.csv',errors,list(errors[0]) if errors else ['reference_id','label','iou'])
    return summary,ref


def endpoint_measurement(points,nm_per_pixel=None):
    points=np.asarray(points,float)
    if points.shape!=(2,2) or not np.all(np.isfinite(points)):raise ValueError('Choose two finite x,y endpoints.')
    if nm_per_pixel is not None and (not np.isfinite(nm_per_pixel) or nm_per_pixel<=0):raise ValueError('Calibration must be positive and finite.')
    length=float(np.linalg.norm(points[1]-points[0]))
    if length==0:raise ValueError('Endpoints must be distinct.')
    return dict(column_1_px=float(points[0,0]),row_1_px=float(points[0,1]),
                column_2_px=float(points[1,0]),row_2_px=float(points[1,1]),
                span_px=length,span_nm=None if nm_per_pixel is None else length*nm_per_pixel)
