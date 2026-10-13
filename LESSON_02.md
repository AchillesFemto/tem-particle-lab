# Lesson 2: loading your real TIFF

Today's single concept: reading a file creates an array in memory, which you can inspect without altering the file.

Your `PG.tif` is a single TIFF page stored as RGB, 857 pixels wide and 857 pixels high, with 8 bits per color component. It visibly contains red measurement lines, labels and a 50 nm scale bar. Those annotations are part of the stored pixels. Treat this as an annotated image, not as a confirmed unmodified detector recording.

## Run

From PowerShell in this project folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe lesson_02.py
```

The file location is set near the top of the script. Change that path if you move the TIFF or reuse the script with another file. No TIFF is copied, overwritten or uploaded, and this lesson creates no processed image.

## Read the code slowly

| Important line | What it does and why |
| --- | --- |
| `from pathlib import Path` | Imports the path tool from Lesson 1. |
| `import tifffile` | Imports a library that reads TIFF arrays and their metadata. |
| `def main():` | Groups the lesson into a function, as in Lesson 1. |
| `image_path = Path(r"...")`   | Identifies your original file. The `r` makes backslashes literal characters in the Python string. Double quotes allow the apostrophe in `Master's` to appear normally. This line does not open or change the image. |
| `with tifffile.TiffFile(image_path) as tif:` | Opens the TIFF for reading. The indented block can inspect it; leaving the block closes the file automatically. |
| `len(tif.pages)` | Counts TIFF pages. A TIFF can contain more than one image page. |
| `len(tif.series)` | Counts image series: groups that tifffile interprets as related arrays. A series can contain multiple pages; pages and series are not interchangeable concepts. |
| `series = tif.series[0]` | Selects the first series explicitly, using zero-based indexing. This lesson inspects only that series. |
| `series.axes` | Reports axis labels interpreted by the reader. For this image, `YXS` means rows, columns and samples per pixel. `S` is not a depth axis. |
| `tif.pages[0].photometric.name` | Reports the first page's stored pixel interpretation. `RGB` identifies red, green and blue samples here. |
| `image = series.asarray()` | Reads that series into a NumPy array. No rescaling, filtering or grayscale conversion is requested. |
| `image.ndim`, `image.shape`, `image.dtype` | Inspect the array exactly as in Lesson 1. These statements are outside the `with` block: the loaded array remains in memory after the file closes. |
| `image.min()`, `image.max()` | Report the smallest and largest stored component values across this array, including annotations. They do not isolate the TEM signal. |
| `row = 0`, `column = 0` | Choose the top-left pixel using zero-based coordinates. |
| `image[row, column]` | Reads all three color components at that location. It returns `[red, green, blue]`, rather than the single value in Lesson 1. |
| `print(...)` | Displays results in the terminal; it does not edit the array. |
| `if __name__ == "__main__": main()` | Runs the lesson when you execute this script directly. |

## What the shape means

```text
image.ndim  → 3
image.shape → (857, 857, 3)
image.dtype → uint8
                Y    X  S
```

There are still only two spatial axes. The third array axis holds red, green and blue samples, not depth slices or three separate microscopy acquisition channels. Each component can store integers from 0 to 255.

A gray pixel has equal red, green and blue components. A colored annotation can have unequal components. Thus, a mostly grayscale-looking picture can still be stored as RGB. Never conclude that `ndim == 3` means a 3D specimen.

## Scientific interpretation

The embedded vendor metadata includes a microscope description, a high-tension setting of 200 kV and a magnification entry of 58,000×. These are recorded metadata values, not independent validation of the acquisition. In the inspected TIFF tags, no explicit physical pixel-size field was found. The visible 50 nm scale bar is a drawn annotation, not an automatically loaded nm/pixel calibration.

We will not infer pixel size from magnification alone. Resizing or exporting an image changes the relationship between image pixels and physical size. Calibration from the scale bar would require a separate, careful measurement and checking its provenance.

The red lines and text are not specimen signal. Including them in later intensity or object measurements would contaminate the analysis. The stored 8-bit RGB values also do not establish the original detector bit depth or whether contrast was adjusted before export. This image is useful for learning file inspection; quantitative analysis needs those limitations addressed first.

## One small experiment

Before editing, predict what changing only `row = 0` to `row = 428` will do:

1. Which pixel will be read, while `column` remains zero?
2. Will the printed value still have three components?
3. Will the image shape change?

Rerun and compare. The numerical values may change because you inspected another location. Selecting a pixel does not modify the image.

Reference: [tifffile documentation](https://github.com/cgohlke/tifffile).
