"""Explicitly named 2D outline and ellipse measurements."""
import numpy as np
from skimage.measure import regionprops


SHAPE_FIELDS=['feret_max_px','ellipse_major_px','ellipse_minor_px','ellipse_aspect_ratio',
              'feret_max_nm','ellipse_major_nm','ellipse_minor_nm']


def shape_measurements(region, nm_per_pixel=None):
    """Ellipse dimensions are shape summaries, not literal rod endpoints."""
    if nm_per_pixel is not None and (not np.isfinite(nm_per_pixel) or nm_per_pixel<=0):
        raise ValueError('Calibration must be finite and positive, or None.')
    major=float(region.axis_major_length)
    minor=float(region.axis_minor_length)
    feret=float(region.feret_diameter_max)
    result=dict(feret_max_px=feret,ellipse_major_px=major,ellipse_minor_px=minor,
                ellipse_aspect_ratio=major/minor if minor>0 else None)
    for name,value in [('feret_max',feret),('ellipse_major',major),('ellipse_minor',minor)]:
        result[name+'_nm']=None if nm_per_pixel is None else value*nm_per_pixel
    return result


def measure_labels(labels, nm_per_pixel=None):
    """Measure each nonzero label; flag region boundaries cut by the crop."""
    rows=[]
    for region in regionprops(labels):
        r0,c0,r1,c1=region.bbox
        rows.append(dict(label=int(region.label),area_px=int(region.area),
                         diameter_px=float(region.equivalent_diameter_area),
                         area_nm2=None if nm_per_pixel is None else float(region.area)*nm_per_pixel**2,
                         diameter_nm=None if nm_per_pixel is None else float(region.equivalent_diameter_area)*nm_per_pixel,
                         eccentricity=float(region.eccentricity),
                         touches_crop_border=bool(r0==0 or c0==0 or r1==labels.shape[0] or c1==labels.shape[1]),
                         **shape_measurements(region,nm_per_pixel)))
    return rows
