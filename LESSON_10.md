# Lesson 10: Gaussian smoothing

## What problem does it address?

Fine-scale fluctuations can make an image difficult to inspect and cause an intensity threshold to select scattered pixels. Smoothing averages neighboring values to reduce rapid spatial variation. However, small real features also vary rapidly, so smoothing can erase useful detail. We cannot assume the texture in this TEM image is all noise.

Gaussian smoothing calculates a weighted average around each pixel. Nearby pixels receive more weight; more distant ones receive less, following a bell-shaped Gaussian profile. The weights sum to one. This is a local operation, unlike the single mean of an entire ROI.

For a simple illustration of a weighted average (not the exact filter used here), weights 0.25, 0.5 and 0.25 applied to values 90, 150 and 90 give 120. The central bright value is reduced, while neighboring output values can increase. The real filter averages in both spatial directions.

## Run

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe lesson_10.py
```

SciPy is the one new dependency. The script creates a separate processed array and saves the comparison as `lesson_10.png`. It never overwrites the original TIFF. Rerunning replaces the generated figure only.

Setup status: SciPy 1.15.3 is now confirmed installed in the project's virtual environment. The earlier automated download stall is resolved. Lesson 10's previous verification covered syntax only.

## The new lines

```python
gray_float = gray.astype(np.float64)
sigma_pixels = 1.0
smoothed = gaussian_filter(gray_float, sigma=sigma_pixels,
                           mode="reflect", truncate=4.0)
```

`astype(np.float64)` makes a decimal-capable copy: a stored 99 becomes 99.0, not 99/255. The intensity range is not normalized. Weighted averages need fractional values. By default SciPy uses the input dtype for its output and intermediate calculations; passing uint8 could discard fractional information. The original `gray` stays uint8.

`sigma_pixels` controls the spatial width of the Gaussian weights, in pixels. It is not an intensity cutoff, a measured noise level, or the intensity SD from Lesson 9. A larger sigma averages over a wider neighborhood and blurs more strongly.

The single sigma value is applied along both axes of our 2D grayscale array. We do not filter across an RGB axis.

`mode="reflect"` describes what happens at the ROI boundary: the filter uses reflected edge values where neighbors outside the array would be needed. This is an explicit assumption, not a measurement of the surrounding specimen.

`truncate=4.0` limits the otherwise infinite Gaussian to about four sigma on each side. At sigma 1, the filter radius is 4 pixels (9 samples per axis); at sigma 2, it is 8 pixels (17 samples per axis). We keep this setting fixed for the experiment.

`smoothed` is a new array with the same `(200, 300)` shape but changed values. This is actual numerical processing, unlike changing the figure size in Lesson 3.

## Read the comparison

The original and smoothed arrays use the same 0–255 display limits. This avoids independent automatic contrast adjustment confusing the comparison. Look at fine texture, narrow dark boundaries and small bright details. Ask what becomes easier to see and what becomes less distinct.

Both plots still use `interpolation="nearest"`. The smoothing is already in the right-hand array; it is not caused by display interpolation.

The printed intensity SD will describe the processed array's variation. A reduction does not establish that the removed variation was noise. Smoothing can reduce real contrast too.

## Every important line

| Code | Meaning |
| --- | --- |
| `from pathlib import Path` | Imports the familiar path tool. |
| `import matplotlib.pyplot as plt` | Imports plotting functions. |
| `import numpy as np` | Imports comparisons, types and summary operations. |
| `from scipy.ndimage import gaussian_filter` | Imports SciPy's Gaussian image filter. |
| `import tifffile` | Imports the TIFF reader. |
| `def main():` | Groups the lesson into a function. |
| `image_path = Path(r"...")` | Identifies the original TIFF; raw-string notation preserves backslashes. |
| `with tifffile.TiffFile(image_path) as tif:` | Opens the TIFF for reading, closing it after the indented block. |
| `image = tif.series[0].asarray()` | Reads the first series. |
| `roi = image[100:300, 100:400, :].copy()` | Selects the same teaching ROI as earlier lessons. |
| `red`, `green`, `blue` assignments | Extract RGB component views for the equality check. |
| `if not (...)`, `raise ValueError(...)` | Stop if the components are not identical, rather than silently discarding color information. |
| `gray = green.copy()` | Makes the verified grayscale array independent. |
| `gray.astype(np.float64)` | Makes a floating-point copy for fractional calculations, as explained above. |
| `sigma_pixels`, `gaussian_filter(...)` | Set and apply the smoothing operation explained above. |
| `.shape`, `.dtype` | Report that spatial dimensions stay the same while the processed values use floating-point storage. |
| `np.array_equal(gray, green)` | Checks every original grayscale value against the corresponding unprocessed ROI component. |
| `np.std(..., ddof=0)` | Computes descriptive intensity spread before and after processing, as in Lesson 9. |
| `print(f"...{value:.2f}")` | Formats numerical output to two decimal places. |
| `plt.subplots(1, 2, figsize=(10, 4))` | Creates two plots in a figure whose dimensions are in figure inches. |
| `axes[0].imshow(gray, ...)` | Displays the original with fixed intensity limits. |
| `axes[1].imshow(smoothed, ...)` | Displays the processed array with identical display settings. |
| `set_title(...)` | Identifies original versus processed and records sigma. |
| `for ax in axes:` | Applies local pixel-coordinate labels to both panels. |
| `set_xlabel`, `set_ylabel` | Label columns and rows within the ROI. |
| `fig.tight_layout()` | Fits labels and titles. |
| `Path(__file__).resolve().parent / "lesson_10.png"` | Builds the figure path beside the script. |
| `fig.savefig(..., dpi=150)` | Saves a rendered comparison, not quantitative raw data. |
| `plt.show()` | Requests an interactive plot window; the saved PNG is available if none appears. |
| `if __name__ == "__main__": main()` | Runs the lesson when executed directly. |

## Scientific limits

The starting sigma is a teaching choice, not a validated optimum. Processing parameters must eventually be justified against the features and measurements you care about. A smoother appearance alone is not validation.

We filter the cropped ROI. Its outermost pixels depend on the reflected-border assumption; filtering a larger surrounding region and then cropping can produce different edge results. For this setting, be especially cautious within roughly four sigma of the ROI boundary. We are not making measurements there.

Sigma is in pixels because physical pixel calibration is still unresolved. Equal sigma along rows and columns means equal smoothing in pixel coordinates, not necessarily in physical distances if sampling is anisotropic.

Smoothing changes local intensities and edges. Reusing a threshold from an unfiltered image on the result need not select the same pixels. We do not apply thresholds or measure particle sizes today. Smoothing also cannot repair saturation, recover lost acquisition information or turn exported intensities into calibrated quantities.

## Your one experiment

Change only `sigma_pixels = 1.0` to `sigma_pixels = 2.0`. Before running, predict:

1. Will the processed image look more or less blurred?
2. Will its array shape change?
3. Will the original grayscale values change?

Inspect one narrow boundary or small bright feature in both panels. Describe what detail the stronger smoothing loses as well as what variation it suppresses.

Reference: [SciPy Gaussian filter documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html).
