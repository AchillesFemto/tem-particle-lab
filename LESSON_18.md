# Lesson 18: where does our TEM selection disagree?

Lesson 17 gave one overlap score. Today we learn one new concept: **separating disagreement into extra and missed foreground pixels**. Two masks can have similar IoU scores but make different kinds of mistakes. Seeing their locations helps us understand what a threshold is doing.

We keep the same image, manual reference and crop. There is no new segmentation algorithm. The threshold selects pixels darker than 140 because the particles are generally dark against a lighter background. This rule is an approximation, not a proven particle detector.

## Run

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe lesson_18.py
```

No additional packages are needed. The script saves `lesson_18.png`. If no plot window appears, open that file. The source image and reference are unchanged.

## Two kinds of disagreement

Here, True means selected as particle foreground.

| Reference | Candidate | Interpretation |
| --- | --- | --- |
| True | True | Shared foreground |
| False | True | Extra pixel: false positive relative to the reference |
| True | False | Missed pixel: false negative relative to the reference |
| False | False | Shared background |

These names describe pixels, not whole particles. A particle can be mostly selected but have some missed boundary pixels.

```python
extra = np.logical_and(candidate, np.logical_not(reference))
missed = np.logical_and(reference, np.logical_not(candidate))
```

`np.logical_not(reference)` reverses the Boolean values: True becomes False and False becomes True. It creates a new array and does not change the reference. It means "positions the reference did not select."

The first line asks for pixels selected by the candidate AND not selected by the reference. These are extra pixels.

The second line asks for pixels selected by the reference AND not selected by the candidate. These are missed pixels.

For one example pixel, suppose its intensity is 130 and its reference value is 0. With threshold 140, our rule selects it, but the annotation does not: it is an extra pixel. Another pixel with intensity 150 and reference value 255 is missed by the same rule.

## Count them and connect to IoU

```python
extra_count = np.count_nonzero(extra)
missed_count = np.count_nonzero(missed)
```

`np.count_nonzero` counts True values in a Boolean mask. At threshold 140, the supplied crop gives:

| Selection | Pixel count |
| --- | ---: |
| Shared foreground | 196,068 |
| Extra | 8,654 |
| Missed | 13,175 |

Shared, extra and missed foreground are three disjoint sets: none of their pixels is counted twice. Together they make the union from Lesson 17:

```text
IoU = shared / (shared + extra + missed)
    = 196068 / (196068 + 8654 + 13175)
    = approximately 0.900
```

Extra and missed pixels both reduce agreement. Their locations and causes may differ, which a single score cannot show.

## Read the figure

- Left: the original TEM crop, with dark particles and lighter background.
- Middle: white marks extra pixels only. Black means "not an extra pixel," not necessarily background.
- Right: white marks missed pixels only. Black means "not a missed pixel," not necessarily background.

Compare matching coordinates across panels. Look for bands near particle boundaries and selected bridges between neighboring particles. Such patterns can suggest a threshold extending beyond the annotation or failing to include faint edges. The map alone cannot prove which boundary is physically correct.

## Important lines throughout the script

| Code | Explanation |
| --- | --- |
| `from pathlib import Path` | Imports file-path construction. |
| `import matplotlib.pyplot as plt`, `import numpy as np` | Import plotting and array operations. |
| `from PIL import Image` | Imports Pillow's PNG reader, preserving the stored 8-bit values. |
| `from lesson_17 import mask_iou` | Reuses the previous lesson's function. Its main guard prevents Lesson 17 from running when imported. |
| `def disagreement_masks(reference, candidate):` | Defines a reusable function that receives two masks. |
| Shape and Boolean dtype checks | Reject incompatible inputs. Equal shape is necessary but does not prove spatial alignment. |
| `raise ValueError(...)` | Stops with a useful explanation if an assumption fails. |
| `return extra, missed` | Returns both disagreement arrays. |
| `def main():` | Groups the steps executed for the lesson. |
| `threshold = 140` | Sets the intensity cutoff; this is the experiment's only parameter. |
| `Path(__file__).resolve().parent` | Finds the folder containing this script. |
| `project / "data" / "public_tem"` | Joins path components to locate the downloaded sample. |
| `with Image.open(...) as source:` | Opens a PNG and closes the file after its indented block. |
| `np.array(source)` | Copies its pixel values into a NumPy array. |
| `image.ndim != 2`, `image.dtype != np.uint8` | Require the expected two-dimensional, 8-bit grayscale input. |
| `image.shape != reference_image.shape` | Rejects mismatched input dimensions. |
| `np.all(np.isin(reference_image, [0, 255]))` | Checks that the reference contains only its documented foreground/background labels. |
| `image[300:1100, 300:1100]` | Selects rows and columns 300 through 1099: an 800 by 800 crop away from the scale bar. |
| The same slice on `reference_image`, followed by `> 0` | Aligns the reference with the crop and converts its 255 labels to True and 0 labels to False. |
| `candidate = roi < threshold` | Selects intensities below the cutoff. Equality is excluded. |
| `extra, missed = disagreement_masks(...)` | Calls our new function and assigns its two returned arrays. |
| `np.count_nonzero(np.logical_and(reference, candidate))` | Counts shared foreground pixels. |
| `score = mask_iou(reference, candidate)` | Computes the previous lesson's score for the same masks. |
| `print(...)`, `:.3f` | Print counts and a score rounded for display to three decimal places. |
| `plt.subplots(1, 3, figsize=(13, 4.5))` | Creates three plotting areas in a row. |
| `panels`, `titles` | Store the arrays and their corresponding headings. `:,` adds thousands separators to displayed counts. |
| `zip(axes, panels, titles)` | Visits one plotting area, array and heading together per loop iteration. |
| `upper = 255 if panel is roi else 1` | Sets the image display range to 0-255 and the Boolean display range to 0-1. `is` checks object identity. |
| `imshow(..., cmap="gray", vmin=0, vmax=upper)` | Displays the arrays with explicit grayscale limits. |
| `interpolation="nearest", origin="upper"` | Avoids smoothing the displayed pixels and places row zero at the top. |
| `set_title`, `set_xlabel`, `set_ylabel` | Label panels and coordinates within the crop. |
| `fig.suptitle`, `fig.tight_layout` | Add the parameter in a heading and arrange plot labels. |
| `fig.savefig(output_path, dpi=150)` | Saves the figure; this does not change the scientific arrays. |
| `plt.show()` | Requests a plot window. The saved PNG is available even without one. |
| `if __name__ == "__main__": main()` | Runs the lesson only when executed directly, leaving its function reusable. |

## Scientific assumptions

These are disagreements **relative to the manual reference**. Human boundaries may be approximate, particularly near faint or touching particles. An extra pixel is not automatically proven physical background, and a missed pixel is not automatically proven particle material.

The masks must describe the same field, crop, orientation and pixel grid. Misalignment can produce apparent errors around every boundary. Matching dimensions alone cannot detect that problem.

We count pixels, not incorrectly identified particles. Touching particles and partial particles at the crop edges need separate treatment before particle-size or particle-count analysis. No filtering, region removal or calibration is applied here.

One crop is not representative validation of a method. Changing thresholds while inspecting this reference is exploration; general performance claims require separate representative data. The sample's [source and license](data/public_tem/README.md) remain documented.

## Your one experiment

Change only `threshold = 140` to `threshold = 160` in `lesson_18.py`. Before running, predict:

1. Can the number of extra pixels decrease, or can it only stay the same or increase?
2. Can the number of missed pixels increase, or can it only stay the same or decrease?
3. Will the original TEM pixel values change?

Then run the script and inspect both disagreement maps. Increasing this cutoff only adds to the candidate selection; the reference stays fixed. Explain the results using that fact.
