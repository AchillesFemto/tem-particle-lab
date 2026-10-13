"""Generate a self-contained index with local plots, tables and scientific caveats."""
from html import escape
from pathlib import Path


def render_report(folder,config,images,tracking,protocol_ok):
    parts=['<!doctype html><html><head><meta charset="utf-8"><title>Microscopy analysis report</title>',
           '<style>body{font:16px system-ui;max-width:1100px;margin:30px auto;padding:0 20px;color:#172033}table{border-collapse:collapse;width:100%}td,th{border:1px solid #cbd5e1;padding:8px;text-align:left}img{width:100%;height:auto}code{background:#eef2f7;padding:2px 4px}.notice{padding:15px;background:#fff4d6}section{margin:30px 0}</style></head><body>',
           '<h1>Microscopy analysis report</h1><p>Configuration-driven batch analysis with explicit provenance and validation limits.</p>',
           '<p><a href="config_snapshot.json">Configuration</a> · <a href="run_manifest.json">Run record</a> · <a href="batch_summary.csv">Batch table</a></p>',
           '<div class="notice"><b>Frozen protocol: '+('matches' if protocol_ok else 'CHANGED — held-out results are exploratory for this changed protocol')+'</b>. New images share one dataset; independent-specimen performance is unverified. Human tracking validation is '+escape(tracking.get('manual_validation',{}).get('status','not run'))+'.</div>',
           '<section><h2>Image-level validation</h2><table><tr><th>Image / role</th><th>Threshold IoU</th><th>Assigned IoU</th><th>Regions</th><th>Complete refs without link</th><th>Split / merge flags</th><th>Eligible size pairs</th></tr>']
    for image in images:
        def fmt(key):
            value=image.get(key)
            return 'undefined' if value is None else f'{value:.3f}' if isinstance(value,float) else escape(str(value))
        parts.append('<tr><td>'+escape(image['id'])+'<br>'+escape(image['role'])+'</td><td>'+fmt('threshold_iou')+'</td><td>'+fmt('assigned_foreground_iou')+'</td><td>'+fmt('predicted_regions')+'</td><td>'+fmt('complete_references_without_link')+'</td><td>'+fmt('possible_splits')+' / '+fmt('possible_merges')+'</td><td>'+fmt('eligible_matches')+'</td></tr>')
    parts.append('</table><p>IoU compares rasterized polygon foreground. Split/merge flags use an explicit overlap rule. Matched size errors exclude ambiguous and border-parent cases; they are a selected subset.</p></section>')
    for image in images:
        key=image['id'];parts.append('<section><h2>'+escape(key)+'</h2>')
        if 'error' in image:
            parts.append('<p class="notice">Analysis failed: '+escape(image['error'])+'</p></section>');continue
        parts.append('<p>Physical calibration: '+('unverified; pixel measurements only' if image['nm_per_pixel'] is None else escape(str(image['nm_per_pixel']))+' nm/pixel estimate')+'. Unassigned foreground pixels: '+str(image['unassigned_foreground_pixels'])+'.</p>')
        parts.append('<img src="'+key+'/comparison.png" alt="Source, manual foreground and watershed comparison">')
        parts.append('<p><a href="'+key+'/summary.json">Diagnostics</a> · <a href="'+key+'/regions.csv">Regions</a> · <a href="'+key+'/matched_errors.csv">Eligible size errors</a> · <a href="'+key+'/overlap_links.csv">Object links</a></p>')
        for note in image['notes']:parts.append('<p>'+escape(note)+'</p>')
        parts.append('</section>')
    parts.append('<section><h2>Tracking checks and uncertainty</h2>')
    if 'error' in tracking:parts.append('<p class="notice">'+escape(tracking['error'])+'</p>')
    else:
        parts.append('<img src="tracking/tracking_checks.png" alt="Tracking and processing-sensitivity checks">')
        parts.append('<p>Accepted proposed locations: '+str(tracking['tracked_frames'])+'. Maximum across-setting displacement spread: '+f"{tracking['max_processing_spread_nm']:.3f}"+' nm. This is processing sensitivity, not a confidence interval.</p>')
        model=tracking['synthetic_model']
        parts.append('<p>Conditional noisy-Gaussian simulation: '+str(model['runs'])+' runs; '+str(model['incomplete_runs'])+' incomplete. Mean per-run pixel RMSE on accepted positions: '+escape(str(model['mean_run_rmse_px_on_accepted']))+'. This does not estimate experimental localization uncertainty.</p>')
        parts.append('<p>Human review: '+escape(str(tracking['manual_validation']))+'</p>')
        parts.append('<p><a href="tracking/summary.json">Tracking settings and limits</a> · <a href="tracking/processing_sensitivity.csv">Sensitivity</a> · <a href="tracking/manual_disagreement.csv">Manual comparisons</a> · <a href="tracking/synthetic_localization.csv">Synthetic benchmark</a></p>')
    parts.append('</section><section><h2>Interpretation limits</h2><ul>')
    for note in config['scientific_notes']:parts.append('<li>'+escape(note)+'</li>')
    parts.append('</ul><p>Source PNG/video exports, approximate annotations, boundary effects, field selection, processing choices, and calibration uncertainty remain material. Reproducible computation is not physical validation.</p></section></body></html>')
    parts[-1] = parts[-1].replace('</body>', '<section><h2>Source attribution and media licences</h2><p>Single-image and held-out TEM data: Andrew Stewart and Natalia Da Silva De Sa, <a href="https://data-collections.psdi.ac.uk/records/sgvf0-j3g53">PSDI dataset version 2</a>, CC BY 4.0; experimental validation data associated with Lee Cronin, University of Glasgow. Movie-derived plots: Kang et al., <a href="https://doi.org/10.1126/sciadv.abi5419">Science Advances 7, eabi5419 (2021)</a>, CC BY-NC 4.0. Report figures are analytical derivatives (cropping, contours, tracking overlays); original inputs are preserved.</p></section></body>')
    (folder/'report.html').write_text('\n'.join(parts),encoding='utf-8')
