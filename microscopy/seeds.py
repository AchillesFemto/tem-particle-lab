"""Group existing seeds using significant distance-map maxima, preserving coverage."""
import numpy as np
from scipy import ndimage
from skimage.morphology import h_maxima
from skimage.segmentation import watershed


def collapse_shallow_peak_seeds(distance, seeds, mask, prominence_fraction=0.25):
    """Keep one existing seed per significant peak basin within each component."""
    if mask.shape!=distance.shape or mask.dtype!=bool:
        raise ValueError('Require an aligned Boolean mask and distance map.')
    if not np.all(np.isfinite(distance)) or np.any(distance<0):
        raise ValueError('Distance values must be finite and nonnegative.')
    if not np.isfinite(prominence_fraction) or not 0<prominence_fraction<=1:
        raise ValueError('Prominence fraction must lie in (0,1].')
    seeds=np.asarray(seeds,dtype=int).reshape(-1,2)
    if len(seeds)==0:return seeds,[]
    if np.any(seeds<0) or np.any(seeds>=np.asarray(mask.shape)) or not np.all(mask[seeds[:,0],seeds[:,1]]):
        raise ValueError('Every seed must lie inside foreground.')
    structure=np.ones((3,3),bool)
    components,count=ndimage.label(mask,structure)
    boxes=ndimage.find_objects(components)
    seed_components=components[seeds[:,0],seeds[:,1]]
    retained=[];diagnostics=[]
    for component in np.unique(seed_components):
        indices=np.flatnonzero(seed_components==component)
        if len(indices)==1:
            retained.extend(indices.tolist());continue
        box=boxes[int(component)-1]
        local_mask=components[box]==component
        local_distance=np.where(local_mask,distance[box],0)
        height=float(local_distance.max())*prominence_fraction
        significant=h_maxima(local_distance,height,footprint=structure).astype(bool)&local_mask
        guides,guide_count=ndimage.label(significant,structure)
        if guide_count==0:raise ValueError('A seeded component must have a significant maximum.')
        basins=watershed(-local_distance,guides,mask=local_mask,connectivity=structure)
        local_seeds=seeds[indices]-[box[0].start,box[1].start]
        assignments=basins[local_seeds[:,0],local_seeds[:,1]]
        kept=[]
        for basin in np.unique(assignments):
            candidates=indices[assignments==basin]
            heights=distance[seeds[candidates,0],seeds[candidates,1]]
            best=int(candidates[np.argmax(heights)])
            kept.append(best);retained.append(best)
        diagnostics.append({'component':int(component),'original_seeds':len(indices),
                            'retained_seeds':len(kept),'significant_peak_groups':guide_count,
                            'prominence_height_px':height})
    return seeds[np.sort(retained)],diagnostics
