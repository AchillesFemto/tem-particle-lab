# Research workflow additions

The new configurable workflow adds five capabilities to the lesson project: additional-image validation, tracking review and conditional error checks, central settings, batch analysis, and an automatic report. It reuses the numerical methods already taught; it does not introduce machine learning.

## Run the complete configured analysis

From the project folder:

```powershell
.\.venv\Scripts\python.exe analyse.py
```

The configuration defaults to `analysis_config.json`. Change it without changing Python:

```powershell
.\.venv\Scripts\python.exe analyse.py --config analysis_config.json
```

For image validation only:

```powershell
.\.venv\Scripts\python.exe analyse.py --skip-tracking
```

Each run creates a new UTC-labelled folder under `results/`. Previous runs are preserved. The terminal prints its `report.html` path. Open that file in a browser; keep its accompanying folders when sharing the report. It uses local images and links, with no external scripts or services.

## 1. Central configuration

`analysis_config.json` has these sections:

| Section | Settings and scientific role |
| --- | --- |
| segmentation | Threshold, crop, peak window/height and duplicate-seed separation; identical across the batch |
| validation | Substantial-overlap link fraction and one-to-one match IoU cutoff |
| datasets | Unique ID, source/annotation paths, development/held-out role and per-image calibration |
| tracking | Movie, initial patch, search radius, smoothing, score cutoff, source scale and acquisition rate |
| uncertainty | Processing-sensitivity settings, synthetic noise model, repeat count and reproducible random seed |
| scientific_notes | Interpretation limits carried into the report |

JSON dictionaries group settings by named keys. Lists describe several images or parameter variants. `null` means calibration is unknown, not zero. Held-out measurement CSVs leave physical-unit columns empty and retain pixel measurements. We do not transfer the development image's bar calibration to other images.

The loader checks parameter ranges and expected types before a run. It does not verify instrument calibration or scientific suitability automatically. Relative input paths resolve against the project folder. A malformed configuration stops rather than proceeding with hidden defaults.

## 2. Additional-image validation with frozen settings

Two new experimental images were selected from the same public source dataset: L2-3-B and L3-elite-3-A. The segmentation/evaluation settings were recorded in `validation_protocol.json` before those images were inspected. The pipeline uses the same crop and settings for development and held-out images.

A digest identifies the frozen parameter dictionary. The run compares the current settings with it and records whether they match. Changing threshold or evaluation settings marks the new result exploratory under a changed protocol. Do not overwrite the frozen record merely to make this flag pass.

These images are independent of our previous parameter tuning, not established independent specimens. Their morphology and sampling differ. We do not average their metrics into an unsupported claim of universal accuracy.

### Findings at the frozen settings

| Image | Threshold IoU | Assigned-foreground IoU | Possible split / merge flags | Eligible complete size pairs |
| --- | ---: | ---: | ---: | ---: |
| Development L1-1-D | 0.898 | 0.806 | 0 / 2 | 8 |
| Held-out L2-3-B | 0.968 | 0.894 | 5 / 2 | 0 |
| Held-out L3-elite-3-A | 0.952 | 0.769 | 0 / 0 | 2 |

Threshold IoU compares all selected dark pixels against the polygon union. Assigned IoU compares only pixels reached by watershed seeds; seedless foreground is not silently counted as correctly rejected background. Neither score establishes correct object separation.

L2-3-B contains elongated particles. Its high foreground overlap coexists with artificial divisions into multiple labels. Multiple distance maxima/ridges can belong to one elongated particle; our compact-particle seed assumptions do not transfer reliably to that morphology. Border and ambiguous-object exclusions also limit size comparisons. Zero eligible pairs is reported explicitly, not converted into zero measurement error.

After using these failures to change the method, these images become development data for the changed method. Another untouched set is needed to test that revision. This first validation run demonstrates limitations rather than claiming the method is fully validated.

## 3. Tracking checks and uncertainty

The batch runner follows the configured template and repeats tracking at smoothing sigmas 1.0, 1.5 and 2.0 pixels. It compares displacement trajectories over their common accepted frames. Their across-setting standard-deviation magnitude has a maximum of approximately **0.074 nm** in the current run.

This is deterministic processing sensitivity, not a confidence interval. It can miss systematic identity, drift and localization errors shared by every setting. The three parameter variants are not independent experimental replicates.

A second check uses 30 explicitly synthetic sequences: a known translating Gaussian dark feature plus independent Gaussian noise. The default signal/noise model produces a mean run-wise localization RMSE of approximately **1.51 pixels** on accepted positions, with incomplete runs separately counted. This verifies conditional behaviour of the tracker under an idealised model. It is not a measured uncertainty for the experimental movie and must not be combined automatically with sensitivity to produce a total error bar.

Calibration, acquisition-rate assumptions, source export/compression, drift, appearance changes and identity errors remain unresolved uncertainty contributions.

### Human reference review

We have not invented human ground truth. Until independent review points are entered, the report marks tracking validation **pending**.

To supply them:

```powershell
.\.venv\Scripts\python.exe review_tracking.py
```

A Tk plotting window shows a selected frame around the same prominent particle. Click a consistent visual particle centre. The tool requests three clicks for each of six frames in shuffled order, hiding the predicted locations. Close a window to skip a point. Review records are saved incrementally to `data/tracking_review/manual_centres.csv`, with a movie fingerprint sidecar at completion.

If a review already exists, `--replace` backs it up before recording another. The blank `review_template.csv` also supports external annotation; enter independent observations rather than copying predicted coordinates.

Rerun `analyse.py` afterward. It compares displacement relative to frame zero, avoiding a constant offset between a visual centroid and a template anchor. It reports disagreement and within-frame click repeatability. Repeatability on one image is not absolute physical accuracy, and reference error at frame zero affects all displacement comparisons. Untracked reference frames are listed rather than silently treated as successful matches. A movie fingerprint mismatch stops the comparison.

The interactive tool requires a display and Tk support, which was checked locally. The author's local tracking review now contains 18 clicks across six frames and has status `reviewed_subset`, with the movie fingerprint verified. In the reviewed run, displacement disagreement RMSE was approximately 0.127 nm. This is agreement with that human-reviewed subset, not absolute physical accuracy or validation of every frame. Personal click records are excluded from Git and the portable archive, so a fresh checkout starts pending until its user records a review. Known numerical fixtures also test the comparison arithmetic.

## 4. Batch processing without hidden failure

`analyse.py` processes each configured image into its own output directory. A failed image receives an explicit error entry; other images can still be analysed. The report is written even when a stage fails, and the process exits with a failure status. Missing data, wrong crop bounds, incompatible annotation identity/dimensions or undefined grayscale conversion are not silently skipped.

Degenerate masks and absent seeds are recorded as diagnostic conditions. Empty or undefined overlap scores are represented as `null`/undefined, not perfect performance. CSV files retain headers even if there are no eligible rows.

For each image, outputs include region measurements, object relationships, eligible size errors, masks and a comparison figure. Optional physical measurements require a stated positive image-specific scale. A positive numerical scale still needs scientific verification.

## 5. Automatic report and reproducibility

The local HTML report combines batch metrics, comparison figures, tracking checks, model limits and links to all detailed results. It explicitly highlights changed protocols, unverified calibration, omitted foreground and pending human review.

Each run saves:

- `config_snapshot.json`: settings actually used.
- `run_manifest.json`: UTC time, package/Python/platform versions, source/input fingerprints, frozen protocol and failures.
- `batch_summary.csv`: one row per image with roles and diagnostic values.
- Per-image folders: measurements, comparisons and numerical arrays.
- `tracking/`: proposed track, processing sensitivity, human-comparison status and conditional synthetic benchmarks.

Hashes identify exact bytes, not correctness. Retain code versions and source data with the run to reproduce it; a hash alone does not store a file. Numeric tests do not validate physical interpretations.

The `.gitignore` excludes generated run folders, environments and personal review records. The public datasets retain separate licences, including the movie's noncommercial restriction; see DATA_LICENSES.md. A portable source archive includes configuration, package modules, tests and public inputs, while generated reports can be shared as their own bundle.

## Understand the reusable code

| File or operation | Meaning |
| --- | --- |
| analyse.py | Parse command choices, load/validate settings, create a new run, process datasets, collect failures and write the report |
| microscopy/core.py | Configuration checks, shared segmentation, polygon/object validation and named CSV/JSON output |
| microscopy/tracking.py | Human-reference comparisons, smoothing sensitivity and synthetic controlled-noise experiments |
| microscopy/report.py | Assemble escaped HTML and relative local links; values are displayed with their assumptions |
| review_tracking.py | Collect actual user clicks without showing predictions; preserve previous review when replacing it |
| JSON keys and dictionary lookup | Select explicit named parameters instead of editing algorithm code |
| for entry in config['datasets'] | Repeat the same calculation for each listed input, keeping outputs separate |
| try/except per dataset | Record failures explicitly while retaining other useful results |
| UTC timestamp plus random suffix | Give each run a unique folder without replacing previous runs |
| SHA256 fingerprints | Detect a change in input/configuration/code bytes |
| protocol_matches | Compare current segmentation/evaluation settings with the recorded frozen settings |
| CSV DictWriter | Save rows under named columns with explicit units |
| save_json with allow_nan=False | Prevent ambiguous NaN values in JSON records; use None/null for undefined results |
| Image/annotation consistency checks | Require the expected source and pixel grid before overlap calculations |
| HTML escape | Treat configured text/error messages as text rather than executable markup |
| Model seed and saved parameters | Make the idealised noise experiments reproducible |

Run the checks:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The suite now has **27 passing tests**, including known mask/motion/Fourier examples, frozen-parameter change detection, pixel-only measurements, empty selections, human-displacement/repeatability arithmetic, rod peak grouping, shape geometry, review edits/undo/provenance and portable run selection. Run the command above to obtain the current count; successful local tests do not establish that hosted CI has run.

## A small experiment

Copy `analysis_config.json` to a new file and change only the threshold in that copy. Run with `--config` pointing to it. Predict whether the frozen-protocol flag will stay true. The point of this experiment is to understand parameter tracking, not to tune the held-out images into a favourable score. Keep the original frozen run as the baseline.
