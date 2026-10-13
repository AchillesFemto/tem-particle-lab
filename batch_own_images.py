"""Analyse a user TIFF manifest sequentially, retaining per-image settings and failures."""
import argparse
from datetime import datetime,timezone
import html
import json
from pathlib import Path
import re
from uuid import uuid4
import matplotlib
matplotlib.use('Agg')
from microscopy.core import save_json,save_csv
from microscopy.user_images import load_tiff_plane,export_user_analysis


def run_batch(project,manifest_path):
    project=Path(project);manifest_path=Path(manifest_path).resolve()
    manifest=json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    if not isinstance(manifest,dict):raise ValueError('Manifest must be a JSON object.')
    entries=manifest.get('images');defaults=manifest.get('defaults',{})
    if not isinstance(entries,list) or not entries:raise ValueError('Manifest needs a nonempty images list.')
    if not all(isinstance(e,dict) for e in entries) or not isinstance(defaults,dict):raise ValueError('Each image and defaults must be JSON objects.')
    if 'nm_per_pixel' in defaults:raise ValueError('Set calibration per image; do not inherit a batch calibration.')
    names=[e.get('id') for e in entries]
    if any(not isinstance(name,str) or not re.fullmatch('[A-Za-z0-9_-]+',name) for name in names) or len(set(names))!=len(names):
        raise ValueError('Use unique safe per-image IDs.')
    output=project/'results'/('batch_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:6]);output.mkdir(parents=True)
    save_json(output/'manifest_snapshot.json',manifest);records=[]
    initial=dict(polarity='dark',method='connected',min_area=1,window_size=11,min_peak_height=2,
                 min_seed_separation=5,prominence=.25,gaussian_sigma=0,background_radius=0,histogram_bins=12,
                 link_fraction=.1,min_match_iou=.5)
    allowed=set(initial)|{'threshold','crop','page','channel'}
    if set(defaults)-allowed:raise ValueError('Unknown batch defaults: '+', '.join(sorted(set(defaults)-allowed)))
    for entry in entries:
        record={'id':entry['id'],'image':entry.get('image'),'status':'failed'}
        try:
            extra=set(entry)-allowed-{'id','image','nm_per_pixel','reference'}
            if extra:raise ValueError('Unknown per-image settings: '+', '.join(sorted(extra)))
            options={**initial,**defaults,**{k:v for k,v in entry.items() if k in allowed}}
            if 'threshold' not in options:raise ValueError('Supply a native/corrected intensity threshold per image or in defaults.')
            source=manifest_path.parent/entry['image'];plane,selection=load_tiff_plane(source,options.pop('page',None),options.pop('channel',None))
            r0,r1,c0,c1=options.pop('crop',None) or [0,plane.shape[0],0,plane.shape[1]]
            options.update(crop_rows=[r0,r1],crop_columns=[c0,c1])
            reference=manifest_path.parent/entry['reference'] if entry.get('reference') else None
            run,summary=export_user_analysis(project,source,plane,selection,options,entry.get('nm_per_pixel'),
                         'Per-image user declaration; not independently verified' if entry.get('nm_per_pixel') is not None else 'not provided',
                         reference_path=reference,run_parent=output/'images'/entry['id'])
            unit='nm' if entry.get('nm_per_pixel') is not None else 'px'
            distribution=summary['distribution']['metrics']['diameter_'+unit]
            record.update(status='completed',report=(run/'report.html').relative_to(output).as_posix(),
                          run=str(run.relative_to(project)),predicted_regions=summary['predicted_regions'],
                          distribution_regions=summary['distribution']['included_regions'],median_diameter=distribution['median'],units=unit,
                          validation_status=summary['validation_status'])
        except (ValueError,OSError,KeyError,TypeError,ImportError,MemoryError) as error:record['error']=str(error) or 'Insufficient memory for this image.'
        records.append(record);print(entry['id'],record['status'],record.get('error',''),flush=True)
    failures=sum(r['status']=='failed' for r in records)
    save_json(output/'batch_summary.json',{'records':records,'failures':failures,
                'caveat':'No particle pooling or replicate-level inference. Threshold units, calibration and exclusions remain per image.'})
    fields=['id','image','status','predicted_regions','distribution_regions','median_diameter','units','validation_status','run','error']
    save_csv(output/'batch_summary.csv',[{k:r.get(k) for k in fields} for r in records],fields)
    table=''.join('<tr><td>'+html.escape(r['id'])+'</td><td>'+html.escape(r['status'])+'</td><td>'+str(r.get('median_diameter',''))+' '+r.get('units','')+'</td><td>'+
                  ('<a href="'+html.escape(r['report'],quote=True)+'">Image report</a>' if 'report' in r else html.escape(r.get('error','')))+'</td></tr>' for r in records)
    (output/'report.html').write_text('<!doctype html><meta charset="utf-8"><title>User TIFF batch</title><style>body{font:17px system-ui;margin:40px}td,th{padding:12px;border:1px solid #ccc}table{border-collapse:collapse}</style><h1>Your TIFF batch</h1><p>'+str(failures)+' failures recorded. Per-image descriptive statistics; no pooling or independent-replicate inference.</p><table><tr><th>ID</th><th>Status</th><th>Median equivalent diameter</th><th>Details</th></tr>'+table+'</table>',encoding='utf-8')
    return output,failures


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,required=True);args=parser.parse_args()
    try:output,failures=run_batch(Path(__file__).resolve().parent,args.manifest)
    except (ValueError,OSError) as error:parser.error(str(error))
    print('Batch report:',output/'report.html')
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
