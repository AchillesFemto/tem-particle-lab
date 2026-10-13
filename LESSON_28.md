# Lesson 28: image-series dynamics and a reusable project

This is the fifth and final larger lesson in our revised course. Work through four sections: alignment, tracking, motion/structural changes, and reproducible project use. The scientific objective is to understand what the measurements describe and how they could fail.

## Run

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe lesson_28.py
```

The installed environment includes video decoding support. The script saves `lesson_28.png` and `lesson_28_results/track.csv`, `msd.csv`, and `parameters.json`. No new download is needed. Rerunning replaces generated results while preserving source movies.

## A. Alignment: separate image drift from local motion

Registration solves a coordinate problem: the same stationary structure can appear at different pixel coordinates if the specimen or camera shifts. Measuring those shifts as particle motion would give a misleading trajectory.

A translation-registration algorithm compares corresponding image patterns to estimate the shift needed to align them. It assumes enough shared, stable content and can fail when contrast, rotation, deformation or genuine motion dominates.

Our supplied Movie S1 is already drift-corrected by its authors. We therefore do not automatically apply a second global correction. Instead, we learn the sign and units using a controlled check:

```python
imposed = np.array([3., -5.])
shifted = ndimage.shift(reference, imposed, order=0, mode="constant", cval=reference.mean())
recovered, error, _ = phase_cross_correlation(reference, shifted,
                                            upsample_factor=10, normalization=None)
```

The first line defines an artificial shift: down three rows and left five columns. `ndimage.shift` creates a deliberately modified copy for this check, using nearest-neighbour resampling and mean-filled borders. It is not an experimental frame or physical particle displacement.

`phase_cross_correlation` estimates the correction required to align that copy with the reference. Here it recovers **[-3, +5] pixels**, the opposite of the imposed shift, with zero residual at the chosen numerical resolution.

`upsample_factor=10` samples the registration estimate at one-tenth-pixel increments. That is computational resolution, not a guarantee of 0.1-pixel physical accuracy. `normalization=None` uses unnormalized correlation, a useful option for noisy data; despite the function name, we are not using its default phase normalization.

For real drift correction, use independently justified stationary reference structure, inspect alignment residuals, and account for interpolation/cropping. Automatically aligning on moving particles can remove genuine collective motion. The controlled test demonstrates an algorithmic capability, not validation of residual drift in the movie.

## B. Tracking: preserve identity across frames

Single-frame detection says where objects might be. Tracking asks whether a later object is the same one. We begin with one visually inspected, prominent particle patch, rather than pretending all particles are reliably detected in this noisy series.

The starting patch centre is `(row=177, column=274)` in frame zero. Its 51 by 51 pixel template includes the particle's appearance and some background. This coordinate is a template anchor; it is not a calibrated area centroid.

### Reduce small-scale noise for comparison

```python
smoothed = ndimage.gaussian_filter(frame, sigma=1.5)
```

Gaussian smoothing reduces pixel-scale fluctuations that can distract matching. It also blurs details and can bias localization. The chosen sigma is 1.5 pixels, approximately 0.106 nm using this movie's calibration. It is not automatically an optimal setting or a physical resolution measurement. We smooth only working arrays; the movie is unchanged.

### Search locally for the same appearance

```python
response = match_template(search_patch, template)
peak_row, peak_column = np.unravel_index(response.argmax(), response.shape)
```

Normalized template correlation solves a similarity problem: it evaluates how well the fixed first-frame template resembles each allowed patch in a later frame. Normalization reduces sensitivity to a simple offset or scaling of brightness, but does not establish identity under structural changes.

`response.argmax()` locates the highest score in a flattened array. `np.unravel_index` converts that index into response-row/column coordinates. Since template positions refer to its top-left corner, the script adds the search origin and template half-width to recover the full-frame anchor.

The search is restricted to eight pixels in each direction from the previous accepted location. This permits motion while reducing confusion with nearby objects. A larger search permits bigger moves but more competing matches. A smaller search can lose a fast-moving object.

The template is fixed rather than updated every frame. This avoids gradually replacing it with the appearance of a different object, but a genuinely rotating or changing particle can stop matching the original.

### Reject suspect associations

We stop when the best score is below 0.5, when the peak reaches the allowed search limit, or when the search approaches excluded image-edge/annotation zones. A low score can indicate noise, changing appearance, an incorrect identity, or missing data. A search-limit peak may mean the object moved farther than permitted. We stop instead of inventing a path across failures.

High scores are not probabilities of correct identity and do not provide localization uncertainty. The first frame's self-match score of one is expected and excluded from the minimum observed score statistic.

At the starting settings, all **136 frames** receive accepted proposed locations. The minimum later match score is approximately **0.875**. Visual inspection remains necessary, including intermediate frames. Endpoints and scores alone cannot establish a correct physical track.

## C. Convert trajectory estimates into motion descriptions

### Use this movie's space and time scales

The first movie frame has a 5 nm bar with raster width 71 pixels, source columns 32 through 102 inclusive. Multiple interior rows show this width. We use:

```python
nm_per_pixel = 5 / 71
frame_interval = 1 / 7.5
```

This gives approximately **0.07042 nm per pixel**. It assumes the published bar is correct, refers to the specimen pixels and applies equally along rows and columns. It is distinct from the earlier 100 nm PNG calibration.

The source reports acquisition at 7.5 frames per second, consistent with the printed timestamps. Encoded playback is 15 frames per second, so using playback duration would give the wrong experimental time. We treat successive movie frames as successive acquired frames, with no dropped/repeated frames established here. Saved elapsed time starts at frame zero; it is not the rounded absolute timestamp printed in the image.

### Displacement from the initial location

```python
positions = pixel_positions * nm_per_pixel
displacement = np.linalg.norm(positions - positions[0], axis=1)
```

Positions use x/y order, while image indexing uses row/column. Subtraction gives displacement vectors from the first anchor. `norm(..., axis=1)` gives the magnitude of each vector.

The illustrative anchor ends approximately **0.947 nm** from its initial location after **18.00 seconds**. This is net displacement, not total path length, mean speed or proven physical centre motion. Contrast changes, residual drift and template-anchor localization can contribute. Early apparent jumps should be inspected, not treated automatically as Brownian motion.

### Mean squared displacement (MSD)

For lag k:

```python
difference = positions[k:] - positions[:-k]
squared = np.sum(difference ** 2, axis=1)
msd = squared.mean()
```

The slices pair every location with the location k frames later. Squaring x/y changes and summing gives squared displacement in nm². Averaging over available time origins gives a time-averaged MSD for this one contiguous track.

At longer lags there are fewer displacement pairs, and overlapping time intervals create correlated estimates. CSV output records pair counts. A straight-looking curve does not prove a diffusion model.

For ideal two-dimensional Brownian motion, ensemble MSD is 4Dt. Applying that model to real data needs justified identity/localization, motion-blur and drift treatment, suitable lag selection, enough trajectories and an uncertainty analysis. We do not fit or report a diffusion coefficient from this illustrative template track.

A localization error of order one pixel already corresponds to approximately 0.070 nm here; this is not a measured uncertainty. The tracker uses integer peaks and a template anchor, so neither its decimals nor its high scores establish subpixel physical precision.

### Structural changes: mergers are identity events

The previously downloaded published sequence shows two objects becoming one. In a multi-particle tracker, a merger should connect two parent identities to a new child identity. Simply forcing one-to-one nearest matches can lose one object and misinterpret its disappearance as detection failure. Splitting needs analogous handling.

Our one-template example follows a different prominent particle patch; it does not automatically detect, validate or quantify the illustrated coalescence event. That event remains a visual, source-documented example for understanding why trajectory association must account for changing topology.

Appearance changes can lower template correlation without indicating a merger. To quantify structural changes, compare registered boundaries and validated identities before and after an event, preserving acquisition conditions and reference uncertainty. Recall the particle-level checks in Lesson 25.

## Read the figure

- Top left: the first frame, initial anchor in red, and proposed trajectory in green. The path is magnified, not rendered as a full-field particle population.
- Top right: last accepted frame and proposed anchor. Compare the particle appearance and position with the first panel.
- Bottom left: distance from the initial anchor versus elapsed time. A decrease means movement back toward the start, not negative speed.
- Bottom right: one-track MSD versus time lag. This averages squared differences across multiple time origins, not just from the initial frame.

The figure shows calculations from an illustrative track. It does not show calibrated physical uncertainty or a validated material diffusion coefficient.

## Important code details

| Code | Explanation |
| --- | --- |
| csv/json/hashlib/Path imports | Save named tables, settings, source fingerprints and portable paths. |
| ImageIO import | Decode the supplementary MP4 using installed FFmpeg support. |
| Matplotlib/NumPy/SciPy imports | Provide plots, arrays, smoothing and the controlled synthetic shift. |
| match_template and phase_cross_correlation imports | Provide local similarity tracking and translation registration. |
| decode_grayscale(...) | Yields one working grayscale frame at a time without storing the whole movie. |
| iio.get_reader(...,format="FFMPEG") | Open the video decoder. |
| frame.astype(float).mean(axis=2) | Convert exported display RGB to a mean-channel grayscale working array; these are not three independent spectral measurements. |
| yield | Pass each decoded frame to the caller when requested. |
| try/finally and reader.close | Ensure the decoder is closed, including when tracking stops early. |
| follow_template(...) | Groups the tracking calculation and parameters. |
| iter(frames), next(frames) | Read the initial frame, then iterate over later frames. |
| Initial template slices and copy | Extract a fixed patch centred on the inspected coordinate, independent of later working arrays. |
| Shape and standard-deviation checks | Require a fully observed patch with nonconstant content. |
| records and last | Initialize the proposed track and last accepted image. |
| enumerate(...,start=1) | Number later frames using zero-based movie indices. |
| Search-bound calculations | Include the template size plus the allowed translation radius on each side. |
| Border checks | Stop if the search would approach frame edges, timestamp or scale-bar zones. |
| response.max/argmax logic | Find the best local similarity and test its height and search-limit position. |
| break | Ends the track at a suspect association instead of filling missing positions. |
| row/column update | Convert template top-left offsets into full-frame anchor coordinates. |
| records.append | Save each accepted location and matching score. |
| return records,first,last,stopped | Return the track, endpoint images and stopping explanation. |
| time_averaged_msd(...) | Compute lag-dependent squared-displacement averages. |
| range and min(max_lag,len(...)-1) | Use only lags with at least one available displacement pair. |
| lag*frame_interval | Convert lag from frames to seconds. |
| main and parameter assignments | Set search radius, initial patch, template size, smoothing, score threshold and calibration. |
| Project-relative movie path | Keep this demonstration portable with its included public sample. |
| len(records)<2 check | Require more than one location for motion calculations. |
| Controlled reference crop | Exclude text/scale-bar regions from the synthetic registration check. |
| recovered+imposed | Measure residual correction relative to a deliberately known shift. |
| Positions and elapsed arrays | Convert recorded coordinates/frame indices to calibrated working units. |
| record.update(...) | Add physical coordinates, displacement and an explicit unvalidated status to each row. |
| output.mkdir and DictWriter | Save CSVs with headers and Windows-compatible newlines. |
| Parameter dictionary | Preserve all settings, source assumptions, stopping reason and validation limits. |
| SHA256 read_bytes fingerprint | Identify the exact input movie, not prove its scientific correctness. |
| json.dumps/write_text | Save a human-readable run record. |
| print and numeric formatting | Report the controlled check and illustrative measured quantities. |
| subplot arrangement, imshow, plot and scatter | Show endpoint images, proposed path and numerical summaries. |
| set_xlim/set_ylim | Magnify the inspected region and retain downward-increasing image rows. |
| Labels/titles | State units and limitations in the generated figure. |
| savefig/show/main guard | Save the figure, request a window, and keep helper functions reusable. |

## D. Reproducible project use and GitHub preparation

See [PROJECT_GUIDE.md](PROJECT_GUIDE.md) for setup, stages, data provenance and review steps. A reusable project retains inputs, parameters, outputs and the assumptions linking them. Reproducibility of a calculation is necessary but does not establish scientific validity.

Run just the movie work:

```powershell
.\.venv\Scripts\python.exe run_workflow.py dynamics
```

Or regenerate the full advanced workflow:

```powershell
.\.venv\Scripts\python.exe run_workflow.py all
```

`static` runs Lessons 24-27 in dependency order. `dynamics` runs Lesson 28. `all` runs both. The runner saves figures without interactive windows by default; `--show` requests windows. It uses each script's current teaching parameters and closes figures after each stage. Changing source parameters changes later outputs, so inspect parameter records rather than assuming every run uses identical settings.

The runner's important operations are `argparse` for command choices, an explicit stage list, `importlib.import_module(...).main()` to call each lesson, and an Agg plotting backend for unattended saving. Its narrow warning filter removes only the noninteractive show warning, not scientific errors or other warnings. Any stage exception stops the workflow.

Check known numerical examples:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Seven tests cover mask metrics, seed suppression, synthetic separation, merge/miss relationships, spatial geometry, reciprocal units and controlled tracking/MSD. Tests use known answers independent of the experimental annotations. Passing them does not validate all real detections or tracks.

The project includes pinned direct dependencies and an exact environment snapshot, data-license records, parameter outputs, ignored environments/generated files and reusable functions. The portable advanced workflow uses included public data. Earlier lessons using your PG.tif retain their original local-input requirements.

## Your one experiment

Change only `search_radius = 8` to `16`. Predict before running:

1. Can the search accommodate a larger frame-to-frame translation?
2. Does a larger search guarantee better particle identity?
3. Will the space/time calibration change?

Compare trajectory, score record and endpoints. A larger search can admit a different competing match even if its score is higher. Do not interpret more accepted frames as automatic improvement. Current output files are overwritten; preserve a copy if comparing runs.

References: scikit-image [translation registration](https://scikit-image.org/docs/0.25.x/api/skimage.registration.html#skimage.registration.phase_cross_correlation) and [template matching](https://scikit-image.org/docs/0.25.x/api/skimage.feature.html#skimage.feature.match_template). Experimental source and movie-processing details: [series README](data/public_tem_series/kang_2021/README.md) and [Kang et al. (2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8641935/).
