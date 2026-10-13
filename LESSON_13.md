# Lesson 13: pixels to physical units

We can count a region's pixels, but a pixel count alone does not tell us its physical size. Calibration supplies the physical distance represented by one pixel step.

This lesson uses invented values only. It does not load, calibrate or measure PG.tif. The 100-pixel scale-bar span below was not measured from your image. Even though your TIFF has a visible 50 nm scale bar, its span and provenance still need to be verified separately.

## Run

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe lesson_13.py
```

No new packages are needed. This script uses basic Python arithmetic and prints results only.

## First calibrate distance

Suppose a trustworthy scale bar represents **50 nm** and spans **100 pixels** in the same image array you will measure.

```text
nm per pixel = known physical length / pixel span
             = 50 / 100
             = 0.5 nm/pixel
```

Then a feature length of 20 pixel steps corresponds to:

```text
20 pixels × 0.5 nm/pixel = 10 nm
```

The Python lines are:

```python
nm_per_pixel = scale_bar_nm / scale_bar_pixels
feature_length_nm = feature_length_pixels * nm_per_pixel
```

`/` divides and `*` multiplies. The variable names record the intended units; Python does not automatically check units for ordinary numbers.

## Area needs both dimensions

Assuming each pixel represents a square 0.5 nm wide and 0.5 nm high:

```text
Area per pixel = 0.5 × 0.5 = 0.25 nm²
200 selected pixels × 0.25 nm² per pixel = 50 nm²
```

```python
pixel_area_nm2 = nm_per_pixel ** 2
region_area_nm2 = region_pixel_count * pixel_area_nm2
```

`** 2` means square the value. We square the distance calibration because area has two dimensions. Multiplying pixel count by nm/pixel only once does not produce a valid physical area.

For non-square physical pixels, use pixel width in nm multiplied by pixel height in nm instead. A horizontal scale bar alone does not establish vertical calibration when sampling or resizing may be anisotropic.

Area is not diameter. A region with an area of 50 nm² does not have a diameter of 50 nm. Shape measurements require separate definitions.

## Every important line

| Code | Meaning |
| --- | --- |
| Triple-quoted opening text | Identifies this file as an example, not a calibration of your TIFF. |
| `def main():` | Groups the lesson into a function. |
| `scale_bar_nm = 50.0` | Sets the invented known physical bar length in nm. |
| `scale_bar_pixels = 100.0` | Sets its invented pixel span. This is the experiment parameter. |
| `feature_length_pixels = 20.0` | Sets a separate invented feature length in pixel steps. |
| `region_pixel_count = 200` | Sets the number of selected pixels in an invented region. |
| `if scale_bar_nm <= 0 or scale_bar_pixels <= 0:` | Checks for invalid zero or negative calibration inputs. `<=` means less than or equal to; `or` means either invalid condition is sufficient. |
| `raise ValueError(...)` | Stops with an explanation rather than dividing by zero or reporting an invalid calibration. |
| `nm_per_pixel = ...` | Divides physical bar length by pixel span. |
| `feature_length_nm = ...` | Converts the feature's pixel length to nm. |
| `pixel_area_nm2 = nm_per_pixel ** 2` | Computes area per pixel under the square-pixel assumption. |
| `region_area_nm2 = ...` | Converts a count of selected pixels into physical area. |
| `print(...)` | Displays results and the synthetic-data warning. |
| `f"...{value:.2f}"` and `:.4f` | Insert numbers into text with two or four decimal places. Formatting is not evidence of measurement accuracy. |
| `if __name__ == "__main__": main()` | Runs the lesson when executed directly. |

## Applying calibration scientifically

Prefer trustworthy acquisition metadata with explicit units when available. A displayed magnification value alone does not give pixel size for an exported digital image.

If using a drawn scale bar, measure its intended endpoint-to-endpoint span in the original image array, not in a resized screenshot or Matplotlib figure. Include neither its text nor the thickness of decorative end caps. Endpoint coordinate difference is not necessarily the number of colored pixels counted inclusively. Record how endpoints were defined and the uncertainty of their placement.

The bar must belong to that image and remain valid for its current geometry. Resizing changes nm/pixel; merely cropping without resampling does not. Stretching differently along the two axes requires separate calibrations. A copied or independently resized annotation is not trustworthy calibration.

Your current PG.tif has embedded annotations and no explicit physical pixel-size field found in our earlier inspection. We have not independently verified its scale bar or export history. Do not copy today's example calibration into your real region measurements.

Calibration converts units; it does not validate segmentation. The fragmented dark regions from Lesson 12 remain unvalidated particle regions even with perfect calibration. Pixel counting also approximates a boundary on a discrete grid.

## Your one experiment

Change only `scale_bar_pixels = 100.0` to `scale_bar_pixels = 200.0`. Keep the physical bar length at 50 nm, the feature at 20 pixel steps and the region at 200 pixels. This compares two hypothetical calibrations, not an actual resizing operation on one image.

Before running, predict:

1. Will nm/pixel increase or decrease?
2. Will the example feature's physical length increase or decrease?
3. Will the example region's physical area become half, one quarter or twice its original value?

Check the arithmetic by hand, then compare the printed results. The original TIFF is not involved and remains unchanged.
