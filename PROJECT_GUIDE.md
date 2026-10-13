# TEM Particle Lab project guide

This project contains the incremental Lessons 1-28 and a portable advanced workflow using the included public TEM examples. Its outputs are exploratory scientific measurements, with recorded calibration and validation assumptions. They are not a certified or universally validated particle-analysis method.

## Recreate the environment

Python 3.12 was used. From this project folder on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`requirements.txt` lists direct packages used in the lessons. `requirements-lock.txt` records all installed versions for this tested environment. An exact version snapshot improves repeatability; it does not remove platform differences or guarantee identical external downloads indefinitely.

On macOS/Linux, use `.venv/bin/python` in place of `.venv\Scripts\python.exe`.

## Run one coherent workflow

```powershell
.\.venv\Scripts\python.exe run_workflow.py static
.\.venv\Scripts\python.exe run_workflow.py dynamics
```

Or run both, in order:

```powershell
.\.venv\Scripts\python.exe run_workflow.py all
```

Figures save without opening windows by default. Add `--show` for interactive windows. The runner stops if a stage fails.

| Stage | Inputs and purpose | Saved results |
| --- | --- | --- |
| 24 | Public single TEM image; threshold, seeds, suppression, watershed and calibration | Region measurements, masks, parameters, diagnostic figure |
| 25 | Saved stage-24 labels and manual polygons | Overlap relationships, split/merge/miss flags, eligible measurement comparisons |
| 26 | Manual full-polygon centres; saved crop/calibration, detected positions for comparison | Nearest-neighbour diagnostics, pair correlations, model simulations |
| 27 | Stage-26 centre positions and source image | Image Fourier power, position structure factor, reciprocal axes and radial values |
| 28 | Separate public movie | Controlled registration check, illustrative one-template trajectory, displacement and MSD |

The stages deliberately preserve the teaching code and reusable functions. Parameters remain explicit near each script's `main()` function. Change one at a time, then review that run's saved settings. Rerunning overwrites generated figures and result folders.

Lessons 1-16 retain their original teaching examples, including exercises originally based on a personal PG.tif file. That TIFF is not included. Supply your own path with `--image PATH` or the `TEM_PARTICLE_LAB_TIFF` environment variable; check the lesson's image-specific assumptions. Use Lessons 24-28 for the portable public-data workflow.

## Data and output organisation

- `data/public_tem/`: single experimental image, reference mask/polygons, provenance and checksums.
- `data/public_tem_series/kang_2021/`: published movie, decoded examples, publication illustration and source records.
- `lesson_XX.py`, `LESSON_XX.md`: runnable code and explanation.
- `tests/test_core.py`: known-answer numerical checks.
- `lesson_XX_results/` and root PNGs: generated outputs, ignored by Git.
- `.venv/`: local installed environment, ignored by Git.

Input files are preserved. Recorded SHA256 hashes identify exact inputs. ZIP archive checks and numerical tests check data integrity/calculations; they do not establish physical truth.

## Before interpreting a scientific result

Review source identity, pixel calibration, acquisition timing, sampling area and processing status. Inspect actual boundaries and identities rather than relying only on summary scores. Report exclusions, omissions, possible splits/merges, border effects and representative sampling limitations.

The one-template track requires identity review and localization/drift uncertainty assessment before physical diffusion inference. The static crop's point-pattern and Fourier summaries require more representative data and justified comparison models before material-order claims.

## Prepare a GitHub repository

Keep the source, guides, requirements, tests, public-data provenance and `.gitignore` together. The code is licensed under MIT in `LICENSE`; source datasets retain their separate licence conditions in [DATA_LICENSES.md](DATA_LICENSES.md).

The single-image sample is CC BY 4.0. The movie/publication series is CC BY-NC 4.0, including derivatives such as decoded frames and publication crops. A code licence does not override either dataset licence. Preserve attribution and processing descriptions when sharing outputs.

For a new local repository in this folder, after reviewing files:

```powershell
git init
git status --short
git add .
git status --short
git commit -m "Add scientific microscopy analysis learning workflow"
```

Review what is staged; `.venv` and generated output folders should be absent. A GitHub upload additionally requires a repository/account and chosen remote. The prepared project archive contains portable files and public data, excluding the environment and generated results.

The included GitHub Actions definition runs the numerical tests on Python 3.12 when the project is hosted in a repository. Its configuration is prepared locally; successful local tests do not claim that hosted CI has run.


[Configuration-driven research additions](RESEARCH_WORKFLOW.md) add a three-image validation batch, tracking review/uncertainty checks, and a local HTML report. Run `analyse.py` to use `analysis_config.json`. Review status comes from the available local records: the author's local tracking review is a reviewed subset; a fresh checkout has no personal review records and starts pending.

## Portable rod measurements and particle review

Generate your own analysis first; no contributor's timestamped results are included:

```powershell
.\.venv\Scripts\python.exe analyse.py --config analysis_config_rods_v2.json --protocol validation_protocol_rods_v2.json --skip-tracking
.\.venv\Scripts\python.exe measure_rods.py
.\.venv\Scripts\python.exe review_particles.py
```

The last two commands print their selected run and dataset. Without arguments, they select the newest compatible saved run by configuration-snapshot modification time and prefer its first successful development dataset. Incomplete runs are skipped. To ensure a particular input, supply `--run results/YOUR_RUN --dataset YOUR_DATASET_ID`. Missing outputs produce instructions to generate a run instead of a traceback pointing to the author's computer.

See [Particle review and rod dimensions](PARTICLE_REVIEW_AND_RODS.md) for measurements, controls and limitations. New particle reviews start pending; saved reviews resume with their recorded statuses. The local test suite currently has **27 passing tests**, covering numerical calculations, review edits, geometry, provenance and portable run selection. Hosted GitHub Actions remains unverified until this project is uploaded and CI actually runs.
