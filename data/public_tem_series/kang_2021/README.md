# Experimental TEM series for learning

Source: Kang et al., *Real-space imaging of nanoparticle transport and interaction dynamics by graphene liquid cell TEM*, Science Advances 7, eabi5419 (2021), [DOI](https://doi.org/10.1126/sciadv.abi5419).

Retrieved 13 October 2026 using the [Europe PMC supplementary-files API](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8641935/supplementaryFiles). Source material is licensed [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/); retain attribution and respect the noncommercial condition when reusing it.

## Files and provenance

- `sciadv.abi5419_movie_s1.mp4`: unchanged supplementary Movie S1. The authors describe it as a drift-corrected TEM movie of nanoparticle diffusion in a quiescent liquid cell.
- `movie_s1_frame_*.png`: five unmodified decoded RGB frame arrays, saved losslessly as PNG. These are exports from a compressed movie, not raw detector data.
- `sciadv.abi5419-f3.jpg`: unchanged published Figure 3.
- `published_coalescence_sequence.png`: crop of Figure 3A, retaining its colour-enhanced images, labels and scale bar. This is a publication illustration, kept separate from the experimental frame exports.
- `provenance.json`: source, license, frame indices, movie metadata and extraction record.
- `SHA256SUMS.txt`: fingerprints of the saved media.

The outer supplement archive and nested movie archive passed all ZIP CRC checks. Full archives remain in the project's working area, not this sample folder.

## Start with the illustrated sequence

Read the five panels from left to right. Follow the two marked objects labelled 1 and 2. Compare their separation and outlines; the last panel labels the joined object 1+2. The timestamps are relative to the illustrated coalescence event, with zero at that event.

Then open the full movie or the generated frame preview to see how much harder visual interpretation becomes when the broader field, noise and motion are present. Do not treat an apparent join in one noisy frame alone as proof of a physical merger.

## What we can investigate next

We can inspect whether the same objects persist, establish suitable calibration, track positions and compare boundary changes. Association across time requires identity checks: moving particles, merging objects and disappearing detections cannot all be handled as independent single-frame counts.

Before using a Fourier comparison, establish that fields, spatial calibration, valid image areas and processing conventions correspond. A changing image spectrum can reflect noise or particle appearance as well as movement. Two objects coalescing is a useful visible event; a population structure factor needs reliable positions for many particles.

This sample does not inherit the earlier PNG's 100 nm bar calibration, threshold, annotations or validated matches. Its visible bars require their own calibration. Movie playback is 15 frames per second, but printed experimental timestamps progress at a different rate. Read those timestamps; do not convert playback duration directly into experimental time.

These downloads do not constitute a new completed analysis lesson. They supply real sequential data for the remaining dynamics work.

## Preview script

From the project folder:

```powershell
.\.venv\Scripts\python.exe preview_tem_series.py
```

The script requires no additional installation in the current environment. ImageIO and its FFmpeg support were installed for decoding, recorded in requirements; the preview script itself reads the exported PNGs.

Important lines in `preview_tem_series.py`:

| Code | Meaning |
| --- | --- |
| `Path`, Matplotlib, NumPy and Pillow imports | Supply paths, plot layout, arrays and PNG reading. |
| `Path(__file__).resolve().parent` | Locate the project folder from the script. |
| `data = project / ...` | Build the sample folder path. |
| `indices = [...]` | Choose the previously exported zero-based movie-frame indices. |
| `plt.subplots(2, 3, ...)` | Create five image panels and one explanatory panel. |
| `zip(axes.flat, indices)` | Pair successive axes with each chosen index. |
| Formatted PNG filename | Insert the frame index with three digits and leading zeros. |
| `with Image.open(...)`, `np.array(source)` | Read a saved frame into an array, then close the file. |
| `imshow(..., interpolation="nearest")` | Display the frame without smoothing the displayed pixels. |
| `set_title`, `axis("off")` | Label frame identity and hide axes that are not physical calibration. |
| The last panel's `text` | Explain timing and attribution; it does not alter image arrays. |
| `suptitle`, `savefig`, `show` | Label, save and display the comparison. |
| Main guard | Run the preview when executed directly. |
