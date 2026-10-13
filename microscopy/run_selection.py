"""Select existing analysis outputs without depending on one person's run ID."""
import json
from pathlib import Path


GENERATE_COMMAND=(r'.\.venv\Scripts\python.exe analyse.py --config analysis_config_rods_v2.json '
                  r'--protocol validation_protocol_rods_v2.json --skip-tracking')
REQUIRED=['arrays.npz','summary.json','overlap_links.csv']


def resolve_analysis(project, run=None, dataset=None):
    """Use an explicit run, or the newest compatible run; prefer development data."""
    project=Path(project)
    explicit=run is not None
    if explicit:
        requested=Path(run)
        candidates=[requested if requested.is_absolute() else project/requested]
    else:
        results=project/'results'
        candidates=list(results.glob('*/config_snapshot.json')) if results.exists() else []
        candidates=[p.parent for p in sorted(candidates,key=lambda p:p.stat().st_mtime_ns,reverse=True)]
    for folder in candidates:
        try:
            config=json.loads((folder/'config_snapshot.json').read_text(encoding='utf-8-sig'))
            entries=config['datasets']
            if not isinstance(entries,list) or not all(isinstance(e,dict) and isinstance(e.get('id'),str) for e in entries):
                raise ValueError('Invalid dataset list.')
        except (OSError,ValueError,KeyError) as error:
            if explicit:raise ValueError(f'Cannot read analysis run {folder}: {error}\nGenerate a run first:\n{GENERATE_COMMAND}') from error
            continue
        eligible=[e for e in entries if dataset is None or e['id']==dataset]
        if dataset is None:
            eligible=sorted(eligible,key=lambda e:e.get('role')!='development')
        for entry in eligible:
            identity=entry['id']
            if not identity or Path(identity).name!=identity or identity in ['.','..']:
                continue
            if all((folder/identity/name).is_file() for name in REQUIRED):
                return folder,identity
        if explicit:
            available=', '.join(e['id'] for e in entries)
            raise ValueError(f'No complete outputs for the requested dataset in {folder}. Configured IDs: {available}.\nGenerate a successful run first:\n{GENERATE_COMMAND}')
    label=f' for dataset {dataset!r}' if dataset is not None else ''
    raise ValueError(f'No compatible saved analysis{label} found.\nGenerate a run first:\n{GENERATE_COMMAND}\nThen rerun this command, or supply --run PATH --dataset ID.')
