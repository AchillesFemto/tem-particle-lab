"""Tracking review, processing sensitivity, and conditional synthetic errors."""
import csv
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage

from lesson_28 import decode_grayscale, follow_template
from .core import fingerprint, save_json, save_csv


def manual_assessment(path, records, scale, image_shape=None):
    """Compare changes from frame zero; repeated clicks measure repeatability only."""
    if not path.exists():return {'status':'pending','reason':'No human reference annotations supplied.'},[]
    groups={}
    with path.open(newline='',encoding='utf-8-sig') as stream:
        for r in csv.DictReader(stream):
            if not r.get('row_px') or not r.get('column_px'):continue
            frame=int(r['frame']);point=np.array([float(r['column_px']),float(r['row_px'])])
            if not np.all(np.isfinite(point)) or np.any(point<0):raise ValueError('Manual positions must be finite and nonnegative.')
            if frame<0:raise ValueError('Manual frame indices must be nonnegative.')
            if image_shape is not None and np.any(point >= [image_shape[1],image_shape[0]]):
                raise ValueError('Manual point is outside the source frame.')
            groups.setdefault(frame,[]).append(point)
    if not groups or 0 not in groups:return {'status':'pending','reason':'Complete frame-zero and later review coordinates first.'},[]
    track={r['frame']:np.array([r['column_px'],r['row_px']]) for r in records}
    origin=np.mean(groups[0],axis=0); start=track[0];rows=[]
    for frame,points in sorted(groups.items()):
        if frame not in track:continue
        mean=np.mean(points,axis=0)
        mismatch=((track[frame]-start)-(mean-origin))*scale
        repeat=float(np.linalg.norm(np.std(points,axis=0,ddof=1))*scale) if len(points)>1 else None
        rows.append({'frame':frame,'click_count':len(points),'displacement_disagreement_nm':float(np.linalg.norm(mismatch)),
                     'radial_click_repeatability_sd_nm':repeat})
    informative=[r for r in rows if r['frame']!=0]
    return {'status':'reviewed_subset' if informative else 'pending',
            'reviewed_frames':len(rows),'reference_sha256':fingerprint(path),
            'ignored_reference_frames_without_track':[f for f in sorted(groups) if f not in track],
            'displacement_rmse_nm':float(np.sqrt(np.mean([r['displacement_disagreement_nm']**2 for r in informative]))) if informative else None,
            'limits':'Click repeatability is not absolute localization accuracy; frame-zero reference error affects every displacement.'},rows


def tracking_extensions(config, project, output):
    t=config['tracking'];u=config['uncertainty'];output.mkdir(parents=True,exist_ok=True)
    movie=project/t['movie'];scale=t['nm_per_pixel']
    arguments={'initial':tuple(t['initial_row_column']),'half_width':t['half_width_px'],
               'search_radius':t['search_radius_px'],'sigma':t['sigma_px'],'min_score':t['min_score']}
    records,first,last,stopped=follow_template(decode_grayscale(movie),**arguments)
    if len(records)<2:raise ValueError('Tracking did not produce at least two accepted frames.')
    baseline=np.array([[r['column_px'],r['row_px']] for r in records],float)
    sensitivity=[];sample_tracks=[]
    for sigma in u['sensitivity_sigmas_px']:
        variant={**arguments,'sigma':sigma}
        track,*rest=follow_template(decode_grayscale(movie),**variant)
        positions=np.array([[r['column_px'],r['row_px']] for r in track],float)
        sample_tracks.append(positions)
        sensitivity.append({'sigma_px':sigma,'accepted_frames':len(track),'stop_reason':rest[-1]})
    n=min(len(baseline),*(len(p) for p in sample_tracks))
    stacked=np.stack([p[:n]-p[0] for p in sample_tracks])
    spread=np.linalg.norm(np.std(stacked,axis=0),axis=1)*scale
    sensitivity_rows=[{'frame':i,'elapsed_seconds':i/t['acquisition_fps'],'processing_spread_nm':float(spread[i])} for i in range(n)]
    save_csv(output/'processing_sensitivity.csv',sensitivity_rows,list(sensitivity_rows[0]))
    save_csv(output/'track.csv',records,['frame','row_px','column_px','score'])
    manual_path=project/t['manual_reference']
    context_path=manual_path.with_suffix('.json')
    if context_path.exists():
        import json
        context=json.loads(context_path.read_text(encoding='utf-8'))
        if context['movie_sha256']!=fingerprint(movie):
            raise ValueError('Manual review refers to a different movie; do not mix references.')
    manual,manual_rows=manual_assessment(manual_path,records,scale,first.shape)
    manual['movie_context_verified']=context_path.exists()

    save_csv(output/'manual_disagreement.csv',manual_rows,['frame','click_count','displacement_disagreement_nm','radial_click_repeatability_sd_nm'])

    # Explicit idealised model: known translated Gaussian feature plus independent noise.
    rng=np.random.default_rng(u['random_seed']);rr,cc=np.indices((160,160))
    clean=100-25*np.exp(-((rr-80)**2+(cc-80)**2)/(2*7.0**2))
    simulations=[]
    for run in range(u['synthetic_runs']):
        frames=[ndimage.shift(clean,(i,2*i),order=0,mode='constant',cval=100)+rng.normal(0,u['synthetic_noise_sd'],clean.shape) for i in range(5)]
        track,*rest=follow_template(frames,initial=(80,80),half_width=15,search_radius=8,sigma=t['sigma_px'],min_score=t['min_score'])
        squared=[]
        for r in track[1:]:
            truth=np.array([80+2*r['frame'],80+r['frame']])
            estimated=np.array([r['column_px'],r['row_px']])
            squared.append(float(np.sum((estimated-truth)**2)))
        simulations.append({'run':run,'accepted_frames':len(track),'stop_reason':rest[-1],
                            'rmse_px_on_accepted':float(np.sqrt(np.mean(squared))) if squared else None})
    valid=[r['rmse_px_on_accepted'] for r in simulations if r['rmse_px_on_accepted'] is not None]
    save_csv(output/'synthetic_localization.csv',simulations,list(simulations[0]))
    summary={'status':'illustrative_unvalidated_track','movie_sha256':fingerprint(movie),
             'tracked_frames':len(records),'stop_reason':stopped,'min_matching_score':min(r['score'] for r in records[1:]),
             'space_scale_nm_per_px':scale,'elapsed_time_seconds':(len(records)-1)/t['acquisition_fps'],
             'net_anchor_displacement_nm':float(np.linalg.norm(baseline[-1]-baseline[0])*scale),
             'sensitivity_runs':sensitivity,'sensitivity_common_frames':n,
             'max_processing_spread_nm':float(spread.max()),
             'sensitivity_interpretation':'Deterministic processing variation, not a confidence interval or total physical uncertainty.',
             'manual_validation':manual,'synthetic_model':{'runs':u['synthetic_runs'],'noise_sd':u['synthetic_noise_sd'],
                 'seed':u['random_seed'],'signal':'Gaussian depression, amplitude 25, width sigma 7 px; independent Gaussian noise',
                 'known_motion':'1 row and 2 columns per frame',
                 'incomplete_runs':sum(r['accepted_frames']<5 for r in simulations),
                 'mean_run_rmse_px_on_accepted':float(np.mean(valid)) if valid else None,
                 'interpretation':'Conditional idealised-model benchmark, not experimental localization uncertainty.'}}
    save_json(output/'summary.json',summary)
    fig,axes=plt.subplots(1,3,figsize=(13,4),layout='constrained')
    axes[0].imshow(first,cmap='gray',vmin=0,vmax=255)
    axes[0].plot(baseline[:,0],baseline[:,1],color='lime')
    row,column=t['initial_row_column'];axes[0].set_xlim(column-75,column+75);axes[0].set_ylim(row+75,row-75)
    axes[0].set_title('Proposed template trajectory')
    axes[1].plot(np.arange(n)/t['acquisition_fps'],spread)
    axes[1].set_title('Processing sensitivity, not confidence')
    axes[1].set_xlabel('Elapsed time (s)');axes[1].set_ylabel('Across-setting displacement spread (nm)')
    axes[2].plot([r['frame']/t['acquisition_fps'] for r in records[1:]],[r['score'] for r in records[1:]])
    axes[2].set_title('Matching score; human review '+manual['status'])
    axes[2].set_xlabel('Elapsed time (s)');axes[2].set_ylabel('Normalized correlation')
    fig.savefig(output/'tracking_checks.png',dpi=130);plt.close(fig)
    return summary
