# Lesson 20: pixel recall

Today's new concept is **recall**: of all pixels marked as particle foreground in the manual reference, what fraction did our method select?

Lesson 19's precision starts with our selection. Recall starts with the reference. Recall helps us quantify missing annotated foreground, which precision does not account for.

## Run

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe lesson_20.py
```

No new packages are needed. The result prints in the terminal; no new figure is generated. Lesson 18's missed-pixel map shows the omissions counted here. The original image and reference are unchanged.

## The denominator is the reference

Every reference foreground pixel is either selected by us (shared) or missed by us. Therefore:

```text
reference foreground = shared + missed
recall = shared / reference foreground
       = shared / (shared + missed)
```

If the reference contains 100 foreground pixels and our method selects 80 of them, recall is 80/100 = 0.80, or 80%. This statement tells us nothing about how many extra background pixels our method also selects.

## Our TEM result

For the same crop and threshold 140:

```text
reference foreground = 209243 pixels
shared foreground    = 196068 pixels
missed foreground    =  13175 pixels
recall                = 196068 / 209243 = 0.9370
```

**Our method selects 93.70% of the reference's foreground pixels.** This does not mean it detects 93.70% of whole particles. A particle may be partly selected, and larger particles contribute more pixels to the result.

| Metric | Question | Denominator |
| --- | --- | --- |
| Precision, Lesson 19 | How much of our selection agrees with the reference? | Candidate foreground pixels |
| Recall, today | How much reference foreground did we select? | Reference foreground pixels |

Both use shared foreground as the numerator. Their denominators differ because they answer different questions.

## The important limitation

Selecting every pixel in the crop would give recall 1 when the reference contains foreground. It would also select all background. Extra pixels do not appear in the recall formula, so recall alone cannot establish a good segmentation.

Conversely, if the reference has foreground but we select nothing, recall is 0. If the reference itself has no foreground, this lesson treats recall as undefined because its denominator is zero.

## The reusable function

```python
def pixel_recall(reference, candidate):
    _, missed = disagreement_masks(reference, candidate)
    reference_count = np.count_nonzero(reference)
    if reference_count == 0:
        raise ValueError("Recall is undefined when the reference has no foreground.")
    shared_count = reference_count - np.count_nonzero(missed)
    return shared_count / reference_count
```

- `def pixel_recall(...)` defines a reusable function receiving two Boolean masks.
- `disagreement_masks` reuses Lesson 18's shape/dtype checks and its definition of missed pixels. Equal shapes do not prove spatial alignment.
- `_, missed` receives both returned masks, keeping the missed mask for this calculation. `_` is an ordinary variable conventionally used for a result we do not need.
- `np.count_nonzero(reference)` counts reference True values, giving the number of annotated foreground pixels.
- `if reference_count == 0` checks for an empty reference. `raise ValueError` stops with a clear explanation instead of dividing by zero.
- Subtracting missed pixels from reference pixels gives shared pixels.
- `return shared_count / reference_count` returns the fraction.

## Image operations and their scientific purpose

```python
roi = image[300:1100, 300:1100]
reference = reference_image[300:1100, 300:1100] > 0
candidate = roi < threshold
```

The slices select original rows and columns 300 through 1099, producing an 800 by 800 crop. Applying the identical crop to both arrays preserves their coordinate correspondence and avoids the bottom scale bar. Partial particles at the crop boundaries are retained for this pixel comparison.

`> 0` converts reference labels into Boolean values: 255 becomes True, 0 becomes False. These reference values are labels, not microscope intensities.

Thresholding selects dark pixels against the lighter background. The assumption that this roughly identifies particle foreground is imperfect because contrast varies and neighboring particles can touch. `roi < threshold` selects values strictly below the cutoff; values equal to it are excluded. No filtering, calibration, or new segmentation algorithm is introduced.

## Other important lines

| Code | Meaning |
| --- | --- |
| `from pathlib import Path` | Imports path construction. |
| `import numpy as np` | Imports numerical arrays, logical comparisons and counting. |
| `from PIL import Image` | Imports the PNG reader, preserving stored 8-bit values. |
| `from lesson_18 import disagreement_masks` | Reuses the previous function without executing its lesson, because that file has a main guard. |
| `def main():` | Groups the execution steps. |
| `threshold = 140` | Sets the only parameter for the experiment. |
| `Path(__file__).resolve().parent` | Locates the project folder from this script's path. |
| `project / "data" / "public_tem"` | Builds the input folder path. |
| `with Image.open(...) as source:` | Opens each PNG, closing its file at the end of the indented block. |
| `np.array(source)` | Copies the image pixels into a NumPy array. |
| `image.ndim != 2`, `image.dtype != np.uint8` | Check the expected two-dimensional, 8-bit grayscale image. |
| `image.shape != reference_image.shape` | Rejects incompatible dimensions. |
| `np.all(np.isin(reference_image, [0, 255]))` | Checks that every reference label is 0 or 255. |
| `raise ValueError(...)` | Stops when an input assumption fails. |
| `extra, missed = disagreement_masks(...)` | Obtains both disagreement maps for the printed summary. |
| `np.count_nonzero(np.logical_and(reference, candidate))` | Directly counts shared foreground for the printed numerator. |
| `recall = pixel_recall(reference, candidate)` | Calls the new function and stores the fraction. |
| `print(...)` | Reports counts and their interpretation. |
| `:.4f` | Displays four decimal places without changing the stored fraction. |
| `:.2%` | Displays the fraction as a percentage with two decimal places. |
| `if __name__ == "__main__": main()` | Runs the lesson when executed directly, while allowing its function to be imported independently. |

## Scientific limits

The score measures agreement with one human annotation, not guaranteed physical truth. Annotation boundaries can be approximate. A misaligned reference would produce misleading scores even if dimensions match.

Recall alone does not assess extra foreground, correct separation of touching particles, particle counts, or accuracy of sizes. Neither precision nor recall proves that a threshold is scientifically suitable. Inspect spatial disagreements as well as the counts.

This is one crop used for learning. Tuning a threshold while viewing its annotation is exploration, not independent validation. Separate representative annotated images are needed for broader performance claims. This dimensionless ratio needs no nanometre calibration. Source and license are in the [sample README](data/public_tem/README.md).

## Your one experiment

Change only `threshold = 140` to `threshold = 160`. Predict before running:

1. Can recall decrease, or can it only stay the same or increase?
2. Will the number of reference foreground pixels change?
3. Does recall of 1 guarantee there are no extra pixels?

Then run and compare the printed counts. With this fixed reference and the rule `roi < threshold`, increasing the cutoff adds candidate pixels without removing previously selected ones. Use that fact to explain your result. This reasoning assumes the same crop and no additional processing.
