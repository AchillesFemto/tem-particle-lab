# Lesson 22: distance inside a foreground mask

Today we start the touching-particle section with one concept: the **Euclidean distance transform**.

## What problem does this solve?

Thresholding can join neighboring particles into one connected region. That region can still contain several thick, rounded interiors. Before trying to divide it, we need a numerical description of where its interior is far from background.

A distance map gives each selected pixel its straight-line distance to the nearest background pixel centre. Background pixels have distance zero. This can reveal high-distance areas near the interiors of approximately round particles. Later, we will investigate candidate centres and use them to guide separation. Today we do not split or count particles.

## Run

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe lesson_22.py
```

SciPy is already installed. The script prints a summary, saves `lesson_22.png`, and requests a plot window. Open the saved PNG if no window appears.

## The key operation

```python
candidate = roi < threshold
distance = foreground_distance(candidate)
```

The first line selects dark pixels, as before. This approximates particles against the brighter background but can also include extra pixels and join touching objects.

The second calls our reusable function, whose numerical operation is:

```python
return ndimage.distance_transform_edt(mask)
```

`ndimage` is SciPy's image-processing module. `edt` means Euclidean distance transform. The function receives a Boolean foreground mask and returns a new floating-point distance array of the same shape. It does not change the image or split the mask.

With default spacing, one step between horizontally or vertically adjacent pixel centres is one pixel. A diagonal step is approximately 1.414 pixels. This is why a distance value need not be an integer. Values describe distances to background pixel centres, not exact distances to a continuous physical boundary.

For an easily understood one-dimensional example:

```text
mask:      False  True  True  True  False
distance:    0     1     2     1     0
```

Our image calculation searches for the nearest background in two dimensions, in any direction, not just along a row.

## Read the figure

1. Left: original TEM intensities. Dark areas are generally particles.
2. Middle: threshold selection. White means foreground, regardless of the original intensity within that selection.
3. Right: distance map. Dark purple is zero or low distance; brighter colours mean farther from background. Read the colour bar in pixels.

Brightness in the distance map is **not TEM intensity**. A dark particle centre in the original image can be bright in the distance map because it is deep inside the selected region.

At threshold 140, the mask selects 204,722 pixels. The distance map has shape `(800, 800)`, dtype `float64`, and a largest distance of approximately **63.07 pixels**. That maximum is not a calibrated particle radius or an average particle size.

The colour scale stays fixed at 0-80 pixels so successive runs are visually comparable. The triangular extension on the colour bar indicates that values above 80, if any, use the top colour; the underlying array is not clipped.

## Important lines

| Code | Explanation |
| --- | --- |
| `from pathlib import Path` | Imports file-path construction. |
| `import matplotlib.pyplot as plt`, `import numpy as np` | Import plotting and numerical arrays. |
| `from PIL import Image` | Imports the PNG reader, preserving stored 8-bit values. |
| `from scipy import ndimage` | Imports image-processing operations, including the distance transform. |
| `def foreground_distance(mask):` | Defines a reusable function receiving one mask. |
| `mask.ndim != 2 or mask.dtype != bool` | Rejects inputs that are not two-dimensional Boolean masks. |
| `np.any(mask)` | Checks whether at least one foreground pixel exists. |
| `np.all(mask)` | Checks whether every pixel is foreground. We reject this case because we need observed background. |
| `raise ValueError(...)` | Stops with an explanation when a lesson assumption fails. |
| `return ndimage.distance_transform_edt(mask)` | Computes and returns the distance array. |
| `def main():` | Groups the steps that run the lesson. |
| `threshold = 140` | Sets the only experiment parameter. |
| `Path(__file__).resolve().parent` | Finds the folder containing the script. |
| `project / "data" / "public_tem" / "L1-1-D.png"` | Builds the source-image path. |
| `with Image.open(image_path) as source:` | Opens the PNG and closes its file after the block. |
| `image = np.array(source)` | Copies its pixels into a NumPy array. |
| The image ndim/dtype check | Requires the expected two-dimensional, 8-bit grayscale image. |
| `image[300:1100, 300:1100]` | Selects rows and columns 300 through 1099, keeping our established 800 by 800 crop away from the scale bar. |
| `candidate = roi < threshold` | Creates a Boolean selection of pixels strictly below the cutoff. |
| `distance = foreground_distance(candidate)` | Calls the function and stores its output. |
| `np.count_nonzero(candidate)` | Counts selected True pixels. |
| `distance.shape`, `distance.dtype` | Report array dimensions and numeric type. |
| `distance.max()` and `:.2f` | Find the largest distance and print it to two decimal places. |
| `plt.subplots(1, 3, ..., layout="constrained")` | Creates three panels and allows space for labels and the colour bar. |
| `axes[0]`, `axes[1]`, `axes[2]` | Refer to the left, middle and right plotting areas. |
| `imshow` with grayscale and limits 0-255 or 0-1 | Displays image intensities or the Boolean mask on the appropriate scale. |
| `imshow(distance, cmap="viridis", vmin=0, vmax=80)` | Maps numerical distances to colours on a fixed scale. |
| `interpolation="nearest"` | Avoids smoothing displayed pixels. |
| `display = ...` | Keeps the plotted distance image so the colour bar uses its scale. |
| `fig.colorbar(..., extend="max")` | Adds units and indicates possible values above the display maximum. |
| `set_title`, the loop over `axes`, and axis labels | Name panels and label coordinates within the crop. |
| `fig.savefig(output_path, dpi=150)` | Saves a figure without modifying scientific arrays or source data. |
| `plt.show()` | Requests a plot window. |
| `if __name__ == "__main__": main()` | Runs the lesson only when directly executed, allowing function reuse. |

## Scientific limits

- Distances describe our threshold selection, including its errors. Small background holes can shorten distances; bridges and merged regions can alter the high-distance pattern.
- A high-distance location is not guaranteed to be a physical particle centre. Irregular or elongated objects can produce several peaks or ridges, and overlapping particles need not produce separable peaks.
- Partial particles touch this crop's borders. Outside the crop is unobserved; we have not added an artificial background border. Missing background outside the crop can distort distance interpretation near its edges. Do not infer complete-particle sizes from these edge regions.
- Default distances use equal row/column pixel spacing. Conversion to physical distances needs verified calibration and appropriate spacing, especially if pixels are anisotropic. No nanometre measurements are made here.
- A distance map is preparation for separation, not evidence that separation is correct. Particle-level validation will be a separate part of our course.

Source image provenance is in the [sample README](data/public_tem/README.md). Algorithm reference: [SciPy 1.15.3 distance_transform_edt](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.ndimage.distance_transform_edt.html).

## Your one experiment

Change only `threshold = 140` to `threshold = 160`. Before running, predict:

1. Will more or fewer pixels become foreground?
2. Can the largest distance decrease, or can it only stay the same or increase, while some background remains?
3. Will the original TEM intensities change?

Then compare the figures and printed maximum. With this fixed crop and rule, increasing the threshold removes background positions from consideration as nearest background. That cannot shorten the distance for previously selected pixels. This depends on retaining background and performing no additional processing.
