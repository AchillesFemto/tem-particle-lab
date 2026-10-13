# Lesson 21: compare thresholds using precision and recall together

Today's concept is the **trade-off between selecting more reference foreground and adding extra pixels**. We use the two metrics you already know rather than introduce another score.

Precision asks how much of our selection agrees with the reference. Recall asks how much reference foreground we selected. Looking at both helps expose the consequences of changing a threshold.

## Run

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe lesson_21.py
```

No new packages are needed. This lesson prints a comparison table, not a new figure. The source image and reference are unchanged.

## A controlled comparison

We keep the same image, manual reference, and crop, and change only the threshold. Otherwise, a difference in scores might be caused by a different field of view or annotation rather than the parameter we intend to study.

Thresholding solves our simple foreground-selection problem by selecting dark pixels against a lighter background. It assumes dark pixels approximately correspond to particles; variable contrast and touching particles limit this assumption.

```python
thresholds = [120, 140, 160]
for threshold in thresholds:
    candidate = roi < threshold
```

`thresholds` is a Python list of three values. The `for` loop runs its indented block three times: first with 120, then 140, then 160. Each iteration creates a new candidate mask from the same original ROI. It does not progressively modify the image or filter the previous mask.

`roi < threshold` selects values strictly below the cutoff. At 120 it selects intensities 0-119; at 140 it also includes 120-139; at 160 it also includes 140-159.

## Verified starting results

| Threshold | Selected pixels | Extra pixels | Missed pixels | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| 120 | 180,155 | 4,812 | 33,900 | 97.33% | 83.80% |
| 140 | 204,722 | 8,654 | 13,175 | 95.77% | 93.70% |
| 160 | 220,441 | 16,722 | 5,524 | 92.41% | 97.36% |

On this crop, raising the threshold finds more annotated foreground but also adds more pixels outside the annotation. Recall rises while precision falls for these three settings.

Moving from 140 to 160 recovers 7,651 previously missed pixels but adds 8,068 extra pixels. That is the concrete cost and benefit of this parameter change relative to the reference.

Recall cannot decrease here because the reference stays fixed and raising the cutoff cannot remove previously selected pixels. Extra-pixel counts cannot decrease either. Precision, however, is a ratio: its direction depends on how many newly selected pixels are shared versus extra. Its decrease in this table is an observation, not a universal rule for every image.

## Is one threshold best?

These scores do not establish a universally best threshold. Selecting too much foreground can enlarge particle boundaries and connect neighboring particles; selecting too little can shrink or miss faint structures. The relevant consequences depend on the scientific measurement you intend to make.

Do not choose a threshold just because it maximizes one score on this crop. Inspect the spatial errors as in Lesson 18, define what errors matter for your measurement, and later evaluate a fixed method on separate representative annotated images. This lesson compares outcomes; it does not claim to validate an optimum.

## Reusing the previous functions

```python
extra, missed = disagreement_masks(reference, candidate)
selected = np.count_nonzero(candidate)
precision = pixel_precision(reference, candidate) if selected else np.nan
recall = pixel_recall(reference, candidate)
```

`disagreement_masks` comes from Lesson 18 and returns extra and missed Boolean arrays. `np.count_nonzero` counts True values in a mask.

The precision line is a conditional expression: if the selection is nonempty, calculate precision using Lesson 19's function; otherwise store `np.nan`, meaning a missing/undefined numerical value. We do not assign perfect precision to an empty selection.

The recall line calls Lesson 20's function. The supplied reference contains foreground, so an empty candidate would have recall zero. If the reference itself were empty, that function would stop with an explanation because recall would be undefined.

The formulas are unchanged:

```text
precision = shared / (shared + extra)
recall    = shared / (shared + missed)
```

## Other important lines

| Code | Meaning |
| --- | --- |
| `from pathlib import Path` | Imports file-path construction. |
| `import numpy as np`, `from PIL import Image` | Import numerical arrays and PNG reading. |
| The three `from lesson_... import ...` lines | Reuse existing functions. Their main guards keep those lessons from executing when imported. |
| `def main():` | Groups the execution steps. |
| `Path(__file__).resolve().parent` | Finds the project folder from this script's location. |
| `project / "data" / "public_tem"` | Joins path components to locate the input folder. |
| `with Image.open(...) as source:` | Opens each PNG and closes its file after the block. |
| `np.array(source)` | Copies stored pixels into a NumPy array. |
| `image.ndim != 2`, `image.dtype != np.uint8` | Check the expected two-dimensional, 8-bit grayscale input. |
| `image.shape != reference_image.shape` | Rejects incompatible dimensions; equal shapes alone cannot prove alignment. |
| `np.all(np.isin(reference_image, [0, 255]))` | Requires only the documented reference label values. |
| `raise ValueError(...)` | Stops with an explanation when an assumption fails. |
| `image[300:1100, 300:1100]` | Crops rows and columns 300 through 1099, excluding the scale bar and image-edge markings. |
| The identical slice of `reference_image`, then `> 0` | Keeps corresponding coordinates and converts labels to Boolean foreground. |
| `print(...)` before the loop | Prints the table heading once. |
| `np.count_nonzero(extra)`, `np.count_nonzero(missed)` | Count the two disagreement types for each threshold. |
| `print(...)` inside the loop | Prints one result row for the current threshold. |
| `:9d`, `:10d` | Display integers right-aligned in fields of 9 or 10 characters. |
| `:11.2%`, `:10.2%` | Display fractions as percentages with two decimal places and specified column widths. |
| `:>9` and similar heading formats | Right-align column names so they match the numbers. |
| Two adjacent formatted strings inside `print` | Join into one line; wrapping the source code does not add a newline between them. |
| `if __name__ == "__main__": main()` | Runs the lesson when executed directly. |

## Scientific limits

All results are pixel comparisons with an approximate human reference. They are not percentages of whole particles detected and do not prove that touching particles are separated correctly. Large regions contribute more pixels to the scores.

Partial particles at the crop edges remain in this pixel comparison. Physical particle-size measurements would need additional decisions about border particles and calibration. These dimensionless metrics require no nanometre conversion.

The three rows use the same crop, so they are not independent samples or evidence of repeatability across specimens. Adjusting parameters using this annotation is exploration, not independent validation. Source and license remain in the [sample README](data/public_tem/README.md).

## Your one experiment

Change only the last value:

```python
thresholds = [120, 140, 180]
```

Before running, predict:

1. Will the results for thresholds 120 and 140 change?
2. Can recall at 180 be lower than recall at 160, with this fixed crop and rule?
3. Does selecting more pixels guarantee higher precision?

Run and compare the final row with the original 160 row. Explain the changes using shared, extra and missed pixels.
