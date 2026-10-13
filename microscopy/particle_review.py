"""Non-destructive manual label review, corrections and versioned exports."""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
from scipy import ndimage
from PIL import Image
from skimage.draw import polygon
from .core import fingerprint, save_json, save_csv
from .measurements import measure_labels


STATUSES=['pending','correct','split','merged','uncertain']


def polygon_mask(vertices, shape):
    """GUI vertices are x,y; arrays require row=y,column=x."""
    vertices=np.asarray(vertices,dtype=float)
    if vertices.ndim!=2 or vertices.shape[1]!=2 or len(vertices)<3 or not np.all(np.isfinite(vertices)):
        raise ValueError('Draw at least three finite polygon vertices.')
    if np.any(vertices<0) or np.any(vertices[:,0]>=shape[1]) or np.any(vertices[:,1]>=shape[0]):
        raise ValueError('Polygon vertices must stay inside the crop.')
    rr,cc=polygon(vertices[:,1],vertices[:,0],shape)
    mask=np.zeros(shape,bool);mask[rr,cc]=True
    return mask


def connected(mask):
    return ndimage.label(mask,np.ones((3,3),bool))[1]==1


class ParticleReview:
    def __init__(self, labels, metadata, folder):
        if labels.ndim!=2 or not np.issubdtype(labels.dtype,np.integer) or np.any(labels<0):
            raise ValueError('Require a nonnegative 2D integer label array.')
        self.labels=labels.astype(np.int32,copy=True)
        self.metadata=copy.deepcopy(metadata)
        self.folder=Path(folder)
        self.status={int(i):'pending' for i in np.unique(labels) if i>0}
        self.log=[];self.history=[];self.field_inspected=False

    def _record(self,action,note,details):
        self.history.append((self.labels.copy(),self.status.copy(),copy.deepcopy(self.log),self.field_inspected))
        self.history=self.history[-5:]
        self.log.append(dict(action=action,note=note,details=details,
                             utc=datetime.now(timezone.utc).isoformat()))

    def apply(self, action, selected=(), vertices=None, note=''):
        """Validate the whole proposed edit before changing any pixels."""
        selected=sorted(set(int(i) for i in selected))
        if any(i not in self.status for i in selected):raise ValueError('Unknown selected label.')
        if action in STATUSES:
            if not selected:raise ValueError('Select at least one particle.')
            self._record(action,note,{'labels':selected})
            for i in selected:self.status[i]=action
            return
        if not note.strip():raise ValueError('Write a reason before correcting a boundary or identity.')
        proposed=self.labels.copy();statuses=self.status.copy()
        details={'old_labels':selected}
        new_id=max(self.status,default=0)+1
        if action=='merge':
            if len(selected)<2:raise ValueError('Select at least two touching regions to merge.')
            combined=np.isin(proposed,selected)
            if not connected(combined):raise ValueError('Selected regions are disconnected; do not join them across background.')
            proposed[combined]=selected[0]
            for i in selected:statuses.pop(i)
            statuses[selected[0]]='pending';details['new_labels']=[selected[0]]
        elif action=='remove':
            if not selected:raise ValueError('Select the false-positive region(s).')
            proposed[np.isin(proposed,selected)]=0
            for i in selected:statuses.pop(i)
        elif action in ['add','replace','split_region']:
            mask=polygon_mask(vertices,proposed.shape)
            details['vertices_xy']=np.asarray(vertices).tolist()
            if action=='add':
                if selected:raise ValueError('Clear the selection before adding a missed particle.')
                if np.any(proposed[mask]>0):raise ValueError('New polygon overlaps an existing label; resolve the overlap first.')
                if not connected(mask):raise ValueError('New particle must be one connected region.')
                proposed[mask]=new_id;statuses[new_id]='pending';details['new_labels']=[new_id]
            else:
                if len(selected)!=1:raise ValueError('Select exactly one region.')
                old=selected[0];old_mask=proposed==old
                if action=='replace':
                    if np.any((proposed[mask]!=0)&(proposed[mask]!=old)):
                        raise ValueError('Replacement overlaps another region; resolve identities first.')
                    if not connected(mask):raise ValueError('Replacement must be one connected region.')
                    proposed[old_mask]=0;proposed[mask]=old;statuses[old]='pending'
                    details['new_labels']=[old]
                else:
                    inside=old_mask&mask;outside=old_mask&~mask
                    if not connected(inside) or not connected(outside):
                        raise ValueError('The polygon must divide the selected region into two nonempty connected pieces.')
                    proposed[inside]=new_id;statuses[old]='pending';statuses[new_id]='pending'
                    details['new_labels']=[old,new_id]
        else:raise ValueError('Unknown review action.')
        self._record(action,note,details)
        self.labels=proposed;self.status=statuses;self.field_inspected=False

    def inspect_field(self,note):
        if not note.strip():raise ValueError('Record your whole-field inspection method.')
        self._record('inspect_field',note,{})
        self.field_inspected=True

    def undo(self):
        if not self.history:raise ValueError('No unsaved-session undo history remains.')
        reverted=self.log[-1]
        labels,status,log,inspected=self.history.pop()
        self.labels=labels;self.status=status;self.field_inspected=inspected
        self.log=log+[dict(action='undo',utc=datetime.now(timezone.utc).isoformat(),note='Reverted preceding session edit',reverted_action=reverted)]

    def save(self):
        """Every save is a separate revision; original labels are never overwritten."""
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:6]
        output=self.folder/'revisions'/stamp;output.mkdir(parents=True)
        np.savez_compressed(output/'reviewed_labels.npz',labels=self.labels)
        rows=measure_labels(self.labels,self.metadata['nm_per_pixel'])
        for row in rows:
            row['review_status']=self.status[row['label']]
            row['eligible_reviewed_measurement']=row['review_status']=='correct' and not row['touches_crop_border']
        fields=list(rows[0]) if rows else ['label','review_status','eligible_reviewed_measurement']
        save_csv(output/'reviewed_regions.csv',rows,fields)
        save_csv(output/'accepted_complete_regions.csv',[r for r in rows if r['eligible_reviewed_measurement']],fields)
        summary=dict(total_regions=len(rows),status_counts={s:sum(v==s for v in self.status.values()) for s in STATUSES},
                     accepted_complete_count=sum(r['eligible_reviewed_measurement'] for r in rows),
                     crop_border_regions=sum(r['touches_crop_border'] for r in rows),
                     field_coverage_reviewed=self.field_inspected,
                     review_decisions_complete=all(s=='correct' for s in self.status.values()) and self.field_inspected,
                     caveat='Accepted count is a reviewed subset, not a validated total. Missing objects and image-wide coverage require human assessment.')
        save_json(output/'review.json',dict(metadata=self.metadata,status={str(k):v for k,v in self.status.items()},
                                         actions=self.log,summary=summary,labels_sha256=fingerprint(output/'reviewed_labels.npz'),
                                         review_code_sha256={name:fingerprint(Path(__file__).parent/name) for name in ['particle_review.py','measurements.py']}))
        save_json(self.folder/'latest.json',{'revision':str(output.relative_to(self.folder))})
        return output


def prepare_review(project,run,dataset_id,folder=None):
    project=Path(project);run=Path(run)
    config=json.loads((run/'config_snapshot.json').read_text())
    entries=[e for e in config['datasets'] if e['id']==dataset_id]
    if len(entries)!=1:raise ValueError('Dataset ID must appear once in this run.')
    entry=entries[0];s=config['segmentation'];source=project/entry['image'];arrays=run/dataset_id/'arrays.npz'
    r0,r1=s['crop_rows'];c0,c1=s['crop_columns']
    if entry.get('kind')=='user_image':
        with np.load(arrays) as stored:image=stored['image']
    else:
        image=np.array(Image.open(source))[r0:r1,c0:c1]
        if image.ndim==3:image=image[:,:,0]
    summary=json.loads((run/dataset_id/'summary.json').read_text())
    if fingerprint(source)!=summary['image_sha256']:raise ValueError('Source image changed since this analysis run.')
    folder=Path(folder) if folder else run/dataset_id/'particle_review'
    metadata=dict(dataset_id=dataset_id,source_image=str(source.resolve()),image_sha256=fingerprint(source),
                  original_arrays=str(arrays.resolve()),original_arrays_sha256=fingerprint(arrays),
                  crop_rows=[r0,r1],crop_columns=[c0,c1],nm_per_pixel=entry['nm_per_pixel'],
                  source_run=str(run.resolve()),coordinate_convention='Crop-local row,column; polygon vertices are x=column,y=row',
                  reference_polygons_displayed=False)
    if entry.get('kind')=='user_image':
        if fingerprint(arrays)!=summary['arrays_sha256']:raise ValueError('Original TIFF run arrays changed outside the analysis tool.')
        metadata['source_selection']=entry['selection']
    if (folder/'latest.json').exists():
        revision=folder/json.loads((folder/'latest.json').read_text())['revision']
        record=json.loads((revision/'review.json').read_text())
        if record['metadata']!=metadata:raise ValueError('Review provenance disagrees with this input run.')
        if fingerprint(revision/'reviewed_labels.npz')!=record['labels_sha256']:raise ValueError('Saved review labels changed outside the review tool.')
        with np.load(revision/'reviewed_labels.npz') as a:model=ParticleReview(a['labels'],metadata,folder)
        model.status={int(k):v for k,v in record['status'].items()};model.log=record['actions']
        model.field_inspected=record['summary']['field_coverage_reviewed']
        if set(model.status)!=set(np.unique(model.labels[model.labels>0])) or any(v not in STATUSES for v in model.status.values()):
            raise ValueError('Saved review statuses disagree with the labels.')
    else:
        folder.mkdir(parents=True,exist_ok=True)
        with np.load(arrays) as a:model=ParticleReview(a['labels'],metadata,folder)
        original=model.labels.copy()
        np.savez_compressed(folder/'automatic_labels.npz',labels=original)
        rows=measure_labels(original,entry['nm_per_pixel'])
        save_csv(folder/'automatic_regions.csv',rows,list(rows[0]) if rows else ['label'])
        save_json(folder/'source.json',metadata)
    if model.labels.shape!=image.shape:raise ValueError('Review labels and source crop have different shapes.')
    return model,image
