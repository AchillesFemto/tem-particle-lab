"""Native-intensity TIFF planes and annotation-free particle measurements."""
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import html
import numpy as np
import tifffile
from scipy import ndimage
from skimage.measure import regionprops,find_contours
from .core import segment,save_csv,save_json,fingerprint
from .measurements import measure_labels,SHAPE_FIELDS


def inspect_tiff(path):
    with tifffile.TiffFile(path) as tif:
        return {'pages':[{'index':i,'shape':list(p.shape),'dtype':str(p.dtype),'axes':p.axes,
                          'photometric':p.photometric.name} for i,p in enumerate(tif.pages)],
                'series':[{'index':i,'shape':list(s.shape),'axes':s.axes} for i,s in enumerate(tif.series)]}


def load_tiff_plane(path,page=None,channel=None):
    """Read one explicit TIFF page; never quantize intensities to uint8."""
    with tifffile.TiffFile(path) as tif:
        if page is None:
            if len(tif.pages)!=1:raise ValueError('TIFF has multiple pages. Choose --page INDEX after --inspect, or select a page in the window.')
            page=0
        if not isinstance(page,int) or not 0<=page<len(tif.pages):raise ValueError('Page index is outside this TIFF.')
        source=tif.pages[page];array=source.asarray();axes=source.axes
        info=dict(page=page,page_count=len(tif.pages),page_axes=axes,original_shape=list(array.shape),
                  original_dtype=str(array.dtype),channel=channel,channel_handling='single grayscale plane')
        if array.ndim==3:
            sample_axes=[i for i,name in enumerate(axes) if name in 'SC']
            if len(sample_axes)!=1:raise ValueError('This TIFF page is a volume, not one 2D plane. Export a 2D plane or separate TIFF pages first.')
            axis=sample_axes[0];count=array.shape[axis]
            if channel is None:
                first=np.take(array,0,axis=axis)
                if source.photometric.name=='RGB' and count in [3,4] and all(np.array_equal(first,np.take(array,i,axis=axis)) for i in [1,2]):
                    if count==4:raise ValueError('RGBA requires an explicit --channel selection; alpha is not a particle-intensity channel.')
                    array=first;info['channel_handling']='Identical RGB planes; first plane used without changing values'
                else:raise ValueError(f'TIFF page has {count} channels/samples. Choose --channel INDEX; no silent colour averaging.')
            else:
                if not isinstance(channel,int) or not 0<=channel<count:raise ValueError('Channel index is outside this page.')
                if source.photometric.name=='RGB' and count==4 and channel==3:raise ValueError('Alpha is transparency, not a particle-intensity channel. Choose channel 0, 1 or 2.')
                array=np.take(array,channel,axis=axis);info['channel_handling']='Explicit channel selection'
        elif channel is not None:raise ValueError('This page is already grayscale; do not specify a channel.')
        if array.ndim!=2 or array.dtype.kind not in 'uif':raise ValueError('Select a 2D real numeric grayscale plane.')
        if not np.all(np.isfinite(array)):raise ValueError('Image contains NaN or infinite values; establish a masking strategy before analysis.')
        info.update(selected_shape=list(array.shape),selected_dtype=str(array.dtype),
                    intensity_min=float(array.min()),intensity_max=float(array.max()),source_sha256=fingerprint(path))
        return array,info


def segment_user_plane(plane,threshold,polarity='dark',method='connected',min_area=1,
                       window_size=11,min_peak_height=2,min_seed_separation=5,prominence=.25):
    """Threshold in original intensity units; optional seeded separation."""
    if plane.ndim!=2 or not np.all(np.isfinite(plane)) or not np.isfinite(threshold):raise ValueError('Require a finite 2D image and threshold.')
    if polarity not in ['dark','bright']:raise ValueError('Polarity must be dark or bright.')
    if not isinstance(min_area,int) or min_area<1:raise ValueError('Minimum area must be a positive integer.')
    candidate=plane<threshold if polarity=='dark' else plane>threshold
    notes=[]
    if not np.any(candidate):notes.append('No foreground: check threshold, polarity and crop.')
    if np.all(candidate):notes.append('All pixels are foreground: thresholding has not distinguished particles from background.')
    if method=='connected':
        labels,_=ndimage.label(candidate,np.ones((3,3),bool))
        notes.append('Connected-component mode: touching foreground remains one region; inspect for merged particles.')
    elif method=='watershed':
        if not isinstance(window_size,int) or window_size<3 or window_size%2==0:raise ValueError('Peak window must be an odd integer >=3.')
        if not 0<prominence<=1:raise ValueError('Prominence fraction must lie in (0,1].')
        # Floating point avoids unsigned-integer overflow when bright contrast is inverted.
        working=plane.astype(float) if polarity=='dark' else -plane.astype(float)
        settings=dict(threshold=float(threshold) if polarity=='dark' else -float(threshold),window_size=window_size,
                      min_peak_height_px=min_peak_height,min_seed_separation_px=min_seed_separation,
                      seed_method='prominence_grouping',peak_prominence_fraction=prominence)
        _,labels,_,_,seed_notes=segment(working,settings);notes.extend(seed_notes)
        notes.append('Watershed settings are exploratory for this image. Thin or border foreground may remain seedless; inspect splits, merges and unassigned pixels.')
    else:raise ValueError('Choose connected or watershed segmentation.')
    if np.all(candidate):labels=np.zeros(plane.shape,np.int32)
    removed_pixels=0;removed_regions=0
    if labels.max():
        sizes=np.bincount(labels.ravel());drop=np.flatnonzero((sizes<min_area)&(np.arange(len(sizes))>0))
        remove=np.isin(labels,drop);removed_pixels=int(remove.sum());removed_regions=len(drop);labels[remove]=0
    stats={'threshold_foreground_pixels':int(candidate.sum()),'filtered_regions':removed_regions,
           'filtered_foreground_pixels':removed_pixels,
           'seedless_foreground_pixels':int((candidate&(labels==0)).sum())-removed_pixels}
    return candidate,labels,notes,stats


def export_user_analysis(project,path,plane,selection,settings,nm_per_pixel=None,calibration_source='not provided'):
    """Write a new local run; no annotation file or image upload is required."""
    project=Path(project);path=Path(path).resolve()
    if selection.get('source_sha256')!=fingerprint(path):raise ValueError('Source TIFF changed after loading; reload it before exporting.')
    if nm_per_pixel is not None and (not np.isfinite(nm_per_pixel) or nm_per_pixel<=0):raise ValueError('Calibration must be positive and finite.')
    r0,r1=settings['crop_rows'];c0,c1=settings['crop_columns']
    if not 0<=r0<r1<=plane.shape[0] or not 0<=c0<c1<=plane.shape[1]:raise ValueError('Crop must lie within the selected plane.')
    roi=plane[r0:r1,c0:c1]
    candidate,labels,notes,stats=segment_user_plane(roi,**{k:v for k,v in settings.items() if k not in ['crop_rows','crop_columns']})
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_user_'+uuid4().hex[:6]
    run=project/'results'/stamp;folder=run/'own_image';folder.mkdir(parents=True)
    entry=dict(id='own_image',role='user_image',kind='user_image',image=str(path),nm_per_pixel=nm_per_pixel,selection=selection)
    save_json(run/'config_snapshot.json',{'schema_version':1,'workflow':'user_tiff','segmentation':settings,'datasets':[entry]})
    np.savez_compressed(folder/'arrays.npz',image=roi,candidate=candidate,labels=labels)
    rows=measure_labels(labels,nm_per_pixel)
    for row in rows:
        row.update(area_nm2=None if nm_per_pixel is None else row['area_px']*nm_per_pixel**2,
                   diameter_nm=None if nm_per_pixel is None else row['diameter_px']*nm_per_pixel,
                   review_status='pending')
    fields=['label','area_px','diameter_px','eccentricity','touches_crop_border']+SHAPE_FIELDS+['area_nm2','diameter_nm','review_status']
    save_csv(folder/'regions.csv',rows,fields)
    # An empty relationship table keeps existing run/review tooling compatible; it is not ground truth.
    save_csv(folder/'overlap_links.csv',[],['reference_id','label','iou','unique','accepted','eligible'])
    summary=dict(id='own_image',role='user_image',predicted_regions=len(rows),
                 complete_predicted_regions=sum(not r['touches_crop_border'] for r in rows),
                 image_sha256=fingerprint(path),arrays_sha256=fingerprint(folder/'arrays.npz'),
                 selection=selection,nm_per_pixel=nm_per_pixel,calibration_source=calibration_source,
                 calibration_verified_by_software=False,validation_status='not performed: no reference annotations supplied',
                 human_review_status='pending',notes=notes+['Exclude scale bars and labels with a crop. Complete predictions remain unvalidated until reviewed.'],**stats)
    save_json(folder/'summary.json',summary)
    save_json(run/'run_manifest.json',dict(workflow='user_tiff',settings=settings,summary=summary,
              source_code_sha256={'user_images.py':fingerprint(Path(__file__))},created_utc=datetime.now(timezone.utc).isoformat()))
    save_preview(roi,labels,candidate,folder/'preview.png')
    escaped=html.escape(path.name)
    (run/'report.html').write_text(f'''<!doctype html><meta charset="utf-8"><title>Your TIFF particle measurements</title>
<style>body{{font:17px system-ui;max-width:1100px;margin:40px auto;padding:20px}}img{{max-width:100%}}pre{{white-space:pre-wrap}}</style>
<h1>Your TIFF: {escaped}</h1><p>{len(rows)} predicted regions; {summary['complete_predicted_regions']} do not touch the crop edge. These are automatic predictions, not validated particle counts.</p>
<p>Page {selection['page']}; channel handling: {html.escape(selection['channel_handling'])}; native dtype {selection['selected_dtype']}. Threshold {settings['threshold']} ({settings['polarity']} foreground). No 8-bit intensity conversion.</p>
<p>Calibration: {nm_per_pixel if nm_per_pixel is not None else 'not provided; pixels only'} nm/pixel. User-provided calibration is not independently verified.</p>
<img src="own_image/preview.png" alt="Original intensity, threshold mask and numbered particle outlines">
<p><a href="own_image/regions.csv">Particle measurements CSV</a> | <a href="own_image/summary.json">Settings, exclusions and limitations</a></p>
<p>Area-equivalent diameter is a circle-based summary, not a literal width for irregular particles. Ellipse axes summarize projected shape. Border-cut particles lack complete size information. No reference agreement score is calculated.</p>
<pre>{html.escape(chr(10).join(summary['notes']))}</pre>
<p>Review this exact run: review_particles.py --run results/{stamp} --dataset own_image</p>''',encoding='utf-8')
    return run,summary


def save_preview(roi,labels,candidate,path):
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(13,5),layout='constrained')
    lo,hi=float(roi.min()),float(roi.max())
    axes[0].imshow(roi,cmap='gray',vmin=lo,vmax=hi)
    axes[1].imshow(candidate,cmap='gray',vmin=0,vmax=1)
    axes[2].imshow(roi,cmap='gray',vmin=lo,vmax=hi)
    for p in regionprops(labels):
        r0,c0,_,_=p.bbox
        for line in find_contours(np.pad(p.image,1),.5):axes[2].plot(line[:,1]+c0-1,line[:,0]+r0-1,color='cyan',lw=.8)
        r,c=p.centroid;axes[2].text(c,r,str(p.label),color='yellow',fontsize=8,clip_on=True)
    for ax,title in zip(axes,['Selected plane: native intensities','Threshold foreground','Predicted regions: review required']):
        ax.set_title(title);ax.set_axis_off()
    fig.savefig(path,dpi=130);plt.close(fig)
