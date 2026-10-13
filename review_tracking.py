"""Click independently chosen centres; predictions are hidden during review."""
import argparse
import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import imageio.v2 as iio
import matplotlib
matplotlib.use("TkAgg")  # Interactive clicks require a GUI backend, even after a headless run.
import matplotlib.pyplot as plt
import numpy as np

from microscopy.core import load_config, fingerprint, save_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='analysis_config.json')
    parser.add_argument('--replace',action='store_true',help='Back up an earlier review and record a new one.')
    args=parser.parse_args();project=Path(__file__).resolve().parent
    t=load_config(project/args.config)['tracking'];path=project/t['manual_reference']
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if not args.replace:raise SystemExit('Review exists. Use --replace to back it up before recording again.')
        backup=path.with_name(path.stem+'_backup_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.csv')
        shutil.copyfile(path,backup)
    requests=[(frame,repeat) for frame in t['review_frames'] for repeat in range(1,t['repeats_per_frame']+1)]
    np.random.default_rng(281).shuffle(requests)
    movie=project/t['movie'];reader=iio.get_reader(movie,format='FFMPEG');rows=[]
    try:
        for frame,repeat in requests:
            image=reader.get_data(frame)
            fig,ax=plt.subplots(figsize=(7,7))
            ax.imshow(image,interpolation='nearest')
            row,column=t['initial_row_column'];ax.set_xlim(column-75,column+75);ax.set_ylim(row+75,row-75)
            ax.set_title(f'Frame {frame}, independent review {repeat}\nClick the same particle centre. Close the window to skip.\nPredicted locations are hidden.')
            point=plt.ginput(1,timeout=-1);plt.close(fig)
            if point:
                x,y=point[0]
                rows.append({'frame':frame,'repeat':repeat,'row_px':y,'column_px':x,'method':'human_visual_centre'})
                with path.open('w',newline='',encoding='utf-8') as stream:
                    writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    finally:reader.close();plt.close('all')
    if rows:
        save_json(path.with_suffix('.json'),{'movie_sha256':fingerprint(movie),
                  'created_utc':datetime.now(timezone.utc).isoformat(),'review_method':'Human visual centre clicks; model predictions hidden',
                  'requested_frames':t['review_frames'],'requested_repeats':t['repeats_per_frame'],
                  'recorded_clicks':len(rows),'limits':'Repeated clicks quantify review precision, not independent physical ground truth.'})
        print('Saved:',path,'; rerun analyse.py to update manual comparisons.')
    else:print('No review points recorded; validation remains pending.')


if __name__=='__main__':main()
