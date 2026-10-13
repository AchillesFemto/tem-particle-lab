"""Run configurable batch validation and tracking checks; write a local HTML report."""
import argparse
import importlib.metadata
import json
import os
import sys
import platform
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

os.environ['MPLBACKEND']='Agg'
from microscopy.core import load_config, protocol_matches, analyse_image, save_json, save_csv, fingerprint
from microscopy.tracking import tracking_extensions
from microscopy.report import render_report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='analysis_config.json')
    parser.add_argument('--protocol',default='validation_protocol.json',help='Frozen protocol record for this method revision.')
    parser.add_argument('--skip-tracking',action='store_true',help='Run image validation only.')
    args=parser.parse_args()
    project=Path(__file__).resolve().parent
    path=project/args.config;config=load_config(path)
    protocol=json.loads((project/args.protocol).read_text(encoding='utf-8'))
    matches=protocol_matches(config,protocol)
    label=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:6]
    output=project/'results'/label;output.mkdir(parents=True)
    save_json(output/'config_snapshot.json',config)
    images=[];failures=[]
    for entry in config['datasets']:
        print('Analysing',entry['id'],flush=True)
        try:result=analyse_image(entry,config,project,output/entry['id'])
        except Exception as error:
            result={'id':entry['id'],'role':entry['role'],'error':str(error)}
            failures.append(entry['id']+': '+str(error))
        images.append(result)
    print('Running tracking sensitivity and conditional simulations...',flush=True)
    if args.skip_tracking:tracking={'manual_validation':{'status':'not run'},'error':'Tracking skipped explicitly.'}
    else:
        try:tracking=tracking_extensions(config,project,output/'tracking')
        except Exception as error:tracking={'error':str(error)};failures.append('tracking: '+str(error))
    fields=['id','role','threshold_iou','assigned_foreground_iou','predicted_regions',
            'reference_instances','complete_references_without_link','possible_splits','possible_merges','eligible_matches','error']
    save_csv(output/'batch_summary.csv',[{key:r.get(key) for key in fields} for r in images],fields)
    versions={p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-image','matplotlib','pillow','imageio','imageio-ffmpeg']}
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'configuration_sha256':fingerprint(path),
              'protocol_matches':matches,'frozen_protocol':protocol,'package_versions':versions,
              'python_version':sys.version,'platform':platform.platform(),
              'source_sha256':{str(p.relative_to(project)):fingerprint(p) for p in list((project/'microscopy').glob('*.py'))+[project/'analyse.py',project/'lesson_22.py',project/'lesson_23.py',project/'lesson_25.py',project/'lesson_28.py']},
              'image_results':images,'tracking':tracking,'failures':failures}
    save_json(output/'run_manifest.json',manifest)
    render_report(output,config,images,tracking,matches)
    print('Report:',output/'report.html',flush=True)
    print('Frozen protocol match:',matches,'; failures:',len(failures),flush=True)
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
