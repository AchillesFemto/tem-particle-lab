# Lesson 19: pixel precision

Today's one new concept is **precision**: of all the pixels our method selects as particle foreground, what fraction are also foreground in the manual reference?

This helps assess how much unwanted foreground our selection includes, relative to that reference. It does not measure how many whole particles we found. Here, precision is a segmentation metric, not the measurement-science meaning of repeatability.

## Run

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe lesson_19.py
```

No new packages are needed. This lesson prints its result in the terminal; it does not generate a new figure. The Lesson 18 maps already show the pixels we are counting. Source images remain unchanged.

## Start with the selected pixels

Every selected pixel belongs to exactly one of two groups:

- Shared foreground: selected by our method and by the reference. These are pixel-level true positives relative to the reference.
- Extra foreground: selected by our method but not by the reference. These are pixel-level false positives relative to the reference.

Therefore:

```text
selected = shared + extra
precision = shared / selected
          = shared / (shared + extra)
```

For example, if we select 100 pixels and 90 are also in the reference, precision is 90/100 = 0.90, or 90%. The remaining 10 selected pixels are extra relative to the reference.

## Our TEM result

With the same 800 by 800 crop and threshold 140:

```text
selected pixels = 204722
shared pixels   = 196068
extra pixels    =   8654
precision       = 196068 / 204722 = 0.9577
```

**95.77% of our selected pixels are also selected by the reference.**

Compare the denominators carefully: IoU from Lesson 17 divides by the union, whereas precision divides only by our candidate selection. Their values answer different questions and are not competing estimates of one quantity.

## The important limitation

There are also 13,175 missed reference pixels at this threshold. They do not enter the precision formula.

Imagine selecting only 10 pixels, all well inside one annotated particle. Precision could equal 1 even if we missed almost every other particle pixel in the image. Thus, maximizing precision alone can produce an incomplete selection. A high value does not establish good overall segmentation.

## The reusable function

```python
def pixel_precision(reference, candidate):
    extra, _ = disagreement_masks(reference, candidate)
    selected_count = np.count_nonzero(candidate)
    if selected_count == 0:
        raise ValueError("Precision is undefined when no pixels are selected.")
    shared_count = selected_count - np.count_nonzero(extra)
    return shared_count / selected_count
```

- `def pixel_precision(...)` defines a function with two input masks.
- `disagreement_masks` is imported from Lesson 18. It checks that both masks have the same shape and Boolean dtype, then returns extra and missed masks. Equal shape does not prove correct alignment.
- `extra, _` keeps the extra mask; `_` is an ordinary variable conventionally used for a result we do not need here. The missed mask is not part of this formula.
- `np.count_nonzero(candidate)` counts selected True pixels.
- The zero check stops with an explanation when nothing is selected. We do not silently treat an empty selection as perfect precision.
- Subtracting extra pixels from selected pixels gives the shared foreground count.
- `return` gives the fraction back to the caller, between 0 and 1 for valid, nonempty selections.

## The image operations stay the same

```python
roi = image[300:1100, 300:1100]
reference = reference_image[300:1100, 300:1100] > 0
candidate = roi < threshold
```

The slices include original rows and columns 300 through 1099. Using identical slices keeps the image and annotation on the same coordinate grid and avoids the scale bar. We compare all pixels in this crop, including partial particles at its boundary.

`> 0` converts the reference's labels (0 and 255) into False and True. `roi < threshold` makes the candidate mask. Thresholding solves the simple task of selecting dark pixels against a lighter background. The scientific assumption is that these dark pixels correspond approximately to particle foreground; variable contrast and touching particles make that assumption imperfect. No filtering or new segmentation method is introduced.

## Other important lines

| Code | Meaning |
| --- | --- |
| `from pathlib import Path` | Imports file-path construction. |
| `import numpy as np` | Imports numerical array operations and counting. |
| `from PIL import Image` | Imports the PNG reader, keeping stored 8-bit pixel values. |
| `from lesson_18 import disagreement_masks` | Reuses the previous lesson's function rather than redefining its logic. Its main guard prevents the previous lesson from running when imported. |
| `def main():` | Groups this lesson's execution steps. |
| `threshold = 140` | Sets the experiment's intensity cutoff; values equal to the cutoff are excluded. |
| `Path(__file__).resolve().parent` | Finds the project folder from this script's location. |
| `project / "data" / "public_tem"` | Builds the folder path containing the downloaded sample. |
| `with Image.open(...) as source:` | Opens a PNG and closes its file after the indented block. |
| `np.array(source)` | Copies its pixels to a NumPy array. |
| `image.ndim != 2`, `image.dtype != np.uint8` | Check the expected two-dimensional grayscale array with 8-bit values. |
| `image.shape != reference_image.shape` | Rejects mismatched image/reference dimensions. |
| `np.all(np.isin(reference_image, [0, 255]))` | Checks that every reference value is one of its documented labels. |
| `raise ValueError(...)` | Stops with an explanation if an input assumption fails. |
| `extra, missed = disagreement_masks(...)` | Gets both maps for the terminal summary. |
| `np.count_nonzero(np.logical_and(reference, candidate))` | Counts shared foreground directly for the printed numerator. |
| `precision = pixel_precision(reference, candidate)` | Calls the reusable function and stores the fraction. |
| `print(...)` | Reports the counts and their interpretation. |
| `:.4f` | Displays four decimal places without changing the stored value. |
| `:.2%` | Formats a fraction as a percentage with two decimal places. |
| `if __name__ == "__main__": main()` | Executes the lesson when run directly, allowing functions to be imported without running it. |

## Scientific limits

The human annotation is a reference, not perfect physical truth. Extra pixels may include uncertain boundary pixels, so avoid interpreting precision as a guaranteed probability that a pixel is physically particle material.

This metric does not assess whether touching particles were separated correctly, whether particle sizes are accurate, or how repeatable measurements are. Large regions contribute more pixels. Physical calibration is unnecessary for this dimensionless pixel ratio, but remains necessary for measurements in nanometres.

Results from one chosen crop do not establish general performance. Adjusting thresholds against this reference is exploration, not independent validation. See the [sample provenance and license](data/public_tem/README.md).

## Your one experiment

Change only `threshold = 140` to `threshold = 160`. Before running, predict:

1. Will our candidate select more or fewer pixels?
2. Must precision increase just because more pixels are selected?
3. Will the manual reference mask change?

Run the script and compare shared pixels and extra pixels. Precision depends on the balance between those two groups, not only on the total selected count. Raising a threshold does not guarantee that precision moves in a particular direction for arbitrary images.
