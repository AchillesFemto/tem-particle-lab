# Lesson 17: does our TEM selection agree with a manual reference?

Today we learn **intersection over union (IoU)** using the downloaded gold-nanoparticle TEM image. IoU compares where two masks select pixels. This replaces the earlier synthetic-square example.

## Why do this?

A threshold produces a selection, but a plausible-looking selection is not proof that it identifies the intended structures. We compare it with the dataset's human annotation to quantify foreground agreement. The annotation is a useful reference, not perfect physical truth.

We use thresholding, which you have already studied: the particles in this image are generally darker than the background, so selecting intensities below a chosen value gives a simple candidate particle mask. This assumption is imperfect because contrast varies and neighboring particles can merge. `140` is a teaching starting point, not a scientifically established optimum.

## Run

From PowerShell in the microscopy-analysis project folder:

```powershell
.\.venv\Scripts\python.exe lesson_17.py
```

The script prints counts, saves `lesson_17.png`, and requests a plot window. Open the saved PNG if no window appears. Pillow is already installed with Matplotlib; it is now listed explicitly in requirements because we import it directly. No new installation is needed in the existing environment.

## 1. Read the image and its reference

```python
with Image.open(data / "L1-1-D.png") as source:
    image = np.array(source)
with Image.open(data / "L1-1-D_mask.png") as source:
    reference_image = np.array(source)
```

`Image.open` comes from Pillow and reads PNG files. `with` closes each file after its block finishes. `np.array(source)` copies the pixels into a NumPy array. Both arrays have shape `(2362, 2362)` and dtype `uint8`. Unlike an RGB image, each pixel has one value. We keep the published pixel values; no grayscale conversion or intensity normalization is applied.

In the reference PNG, 255 means annotated particle foreground and 0 means background. Those numbers are labels, not microscope intensities.

## 2. Select the same crop in both arrays

```python
roi = image[300:1100, 300:1100]
reference = reference_image[300:1100, 300:1100] > 0
candidate = roi < threshold
```

- `300:1100` includes indices 300 through 1099. The first slice selects rows, the second columns. This produces an 800 by 800 crop away from the scale bar and edge markings.
- Exactly the same coordinates are used for the reference, keeping corresponding pixels aligned. Equal dimensions alone would not establish alignment.
- `> 0` converts the reference labels into Boolean values: white regions become `True`, background becomes `False`.
- `roi < threshold` makes our candidate Boolean mask. At `threshold = 140`, values 0 through 139 are selected; 140 itself is excluded. The original image is unchanged.

We retain partial particles at the crop edges for this foreground-overlap exercise. Measuring complete particle sizes would require separate handling of those particles.

## 3. Count intersection and union

```python
overlap = np.logical_and(reference, candidate)
combined = np.logical_or(reference, candidate)
```

**Intersection** means pixels selected by BOTH masks. `logical_and` returns True only where both inputs are True.

**Union** means pixels selected by EITHER mask. `logical_or` returns True if either input is True, counting a shared position only once.

For example, if the reference selects 10 pixels, the candidate selects 12, and 8 are shared, the union has `10 + 12 - 8 = 14` pixels. IoU is `8 / 14`, about 0.571.

```python
intersection = np.count_nonzero(np.logical_and(reference, candidate))
union = np.count_nonzero(np.logical_or(reference, candidate))
return intersection / union
```

For Boolean arrays, `np.count_nonzero` counts True values. Dividing the intersection count by the union count gives IoU. A score of 1 means identical nonempty selections; 0 means no shared foreground pixels. Two empty masks are treated as undefined in this lesson.

## Your starting result

With the supplied crop and threshold 140:

| Quantity | Pixels |
| --- | ---: |
| Manual reference selection | 209,243 |
| Threshold selection | 204,722 |
| Intersection | 196,068 |
| Union | 217,897 |

`IoU = 196068 / 217897`, approximately **0.900**.

About 90% of the pixels selected by at least one mask are selected by both. This is **not the percentage of correctly counted particles**, and it is not accuracy over all image pixels. Background pixels rejected by both masks do not enter this ratio.

## What the four panels mean

1. **TEM intensities:** the actual crop; dark structures are visible against a lighter background.
2. **Manual reference:** white is annotated particle foreground.
3. **Threshold selection:** white is the foreground selected by our intensity rule. Inspect jagged boundaries and bridges between neighboring particles.
4. **Intersection:** white appears only where both masks select a pixel. It shows shared foreground, not the original intensity or the union.

A high overlap score can coexist with joined particles. IoU alone does not tell us whether individual objects were separated correctly.

## Remaining important lines

| Code | Purpose |
| --- | --- |
| `from pathlib import Path` | Imports the tool used to construct file paths. |
| `import matplotlib.pyplot as plt`, `import numpy as np`, `from PIL import Image` | Import plotting, numerical arrays, and PNG reading. |
| `def mask_iou(reference, candidate):` | Defines a reusable overlap calculation for two Boolean masks. |
| Shape and dtype checks in `mask_iou` | Reject differently sized or non-Boolean masks before comparison. They do not prove alignment. |
| `if union == 0: raise ValueError(...)` | Avoids dividing by zero for two empty masks. |
| `def main():` | Groups the steps that run this lesson. |
| `threshold = 140` | Sets the single parameter for the experiment. |
| `Path(__file__).resolve().parent` | Finds the project folder from the script's location, independent of the terminal's current folder. |
| `data = project / "data" / "public_tem"` | Builds the input folder path. Here `/` joins path components. |
| `image.ndim != 2`, `image.dtype != np.uint8` | Require this lesson's expected grayscale array and 8-bit values. |
| `image.shape != reference_image.shape` | Rejects incompatible image/reference sizes. |
| `np.all(np.isin(reference_image, [0, 255]))` | Checks that every reference value is one of its two documented labels. |
| `raise ValueError(...)` | Stops execution with an explanation if an assumption fails. |
| `score = mask_iou(reference, candidate)` | Calls the reusable function and stores its result. |
| `print(...)` and `:.3f` | Report results; the format displays three decimal places without changing the stored score. |
| `plt.subplots(2, 2, figsize=(9, 9))` | Creates a two-by-two arrangement of plotting panels. |
| `panels`, `titles` | Collect the arrays and corresponding headings in matching order. |
| `zip(axes.flat, panels, titles)` | Iterates through one plotting area, array, and title together. `axes.flat` visits the four axes in order. |
| `upper = 255 if panel is roi else 1` | Uses an intensity display range for the image and a Boolean range for the masks. `is` checks whether this is the original ROI object. |
| `imshow(..., cmap="gray", vmin=0, vmax=upper)` | Displays grayscale with an explicit range; white in a mask means selected. |
| `interpolation="nearest", origin="upper"` | Avoids display smoothing and puts row zero at the top. |
| `set_title`, `set_xlabel`, `set_ylabel` | Label the panel and its coordinates within the crop, not the full image. |
| `fig.suptitle`, `fig.tight_layout` | Add the overall score and arrange the panel labels. |
| `fig.savefig(output_path, dpi=150)` | Saves the comparison figure without changing the input image or reference. |
| `plt.show()` | Requests an interactive figure window. |
| `if __name__ == "__main__": main()` | Runs the lesson when the file is executed directly. Importing it allows reuse of `mask_iou` without running the lesson. |

## Scientific limits

The source and reuse license are documented in [the sample README](data/public_tem/README.md). These are published PNG exports, not verified raw detector data. Human boundaries can be approximate, particularly at touching or faint particles. Inspect the image alongside the reference rather than assuming the reference is exact.

This is one fixed crop. Its score cannot establish performance on other images or specimens. Changing the threshold while examining this reference is parameter exploration, not independent validation. A final method needs evaluation on separate, representative annotated data.

IoU compares foreground pixels; it does not measure particle-count accuracy, boundary uncertainty, or the accuracy of a size distribution. Large regions contribute more pixels to the pooled score. No nanometre calibration is needed for this dimensionless ratio, and we make no physical-size measurements here.

## One small experiment

Change only `threshold = 140` to `threshold = 160`. Before running, predict:

1. Will the candidate select fewer pixels, more pixels, or the same number?
2. Will the manual reference mask change?
3. Must IoU increase just because more pixels are selected? Why?

Run the script and compare the printed IoU and the four panels. Think about the extra pixels: some may match the reference, while others may include background.
