"""Lesson 27: image Fourier power and a centre-position structure factor."""

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


def image_power_spectrum(image, nm_per_pixel, use_hann=True):
    """Return frequency axes and a window-energy-normalized 2D image spectrum."""
    if image.ndim != 2 or not np.all(np.isfinite(image)) or nm_per_pixel <= 0:
        raise ValueError("Use a finite 2D image and positive pixel spacing.")
    rows, columns = image.shape
    window = np.outer(np.hanning(rows), np.hanning(columns)) if use_hann else np.ones(image.shape)
    mean = np.sum(image * window) / np.sum(window)
    prepared = (image.astype(float) - mean) * window
    amplitude = np.fft.fftshift(np.fft.fft2(prepared))
    power = np.abs(amplitude) ** 2 / np.sum(window ** 2)
    fx = np.fft.fftshift(np.fft.fftfreq(columns, d=nm_per_pixel))
    fy = np.fft.fftshift(np.fft.fftfreq(rows, d=nm_per_pixel))
    return fx, fy, power


def position_structure_factor(points, fx, fy):
    """Compute |sum exp(-2 pi i f dot r)|^2 / N for equal-weight 2D centres."""
    if points.ndim != 2 or points.shape[1] != 2 or len(points) == 0 or not np.all(np.isfinite(points)):
        raise ValueError("Use a nonempty finite (N, 2) array of x/y positions.")
    grid_x, grid_y = np.meshgrid(fx, fy)
    amplitude = np.zeros(grid_x.shape, dtype=complex)
    for x, y in points:
        phase = -2j * np.pi * (grid_x * x + grid_y * y)
        amplitude += np.exp(phase)
    return np.abs(amplitude) ** 2 / len(points)


def radial_average(values, fx, fy, edges):
    """Average grid values in frequency annuli, excluding the zero-frequency mode."""
    grid_x, grid_y = np.meshgrid(fx, fy)
    radius = np.hypot(grid_x, grid_y)
    means, counts = [], []
    for lower, upper in zip(edges[:-1], edges[1:]):
        selected = (radius >= lower) & (radius < upper) & (radius > 0)
        counts.append(int(selected.sum()))
        means.append(float(values[selected].mean()) if np.any(selected) else np.nan)
    return np.asarray(means), np.asarray(counts)


def main():
    use_hann_window = True  # Experiment: change only this to False.
    max_frequency = 0.4  # cycles per nm, for particle-scale display.
    project = Path(__file__).resolve().parent
    source = project / "lesson_26_results"
    if not (source / "reference_positions.csv").exists():
        raise FileNotFoundError("Run lesson_26.py first to save manual centre positions.")
    summary = json.loads((source / "summary.json").read_text(encoding="utf-8"))
    parameters = summary["segmentation_parameters"]
    with (source / "reference_positions.csv").open(newline="", encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
    points = np.array([[float(r["x_nm"]), float(r["y_nm"])] for r in records])
    r0, r1 = parameters["roi_rows"]
    c0, c1 = parameters["roi_columns"]
    scale = parameters["nm_per_pixel"]
    with Image.open(project / parameters["source"]) as source_image:
        roi = np.array(source_image)[r0:r1, c0:c1]
    fx, fy, image_power = image_power_spectrum(roi, scale, use_hann_window)
    keep_x, keep_y = np.abs(fx) <= max_frequency, np.abs(fy) <= max_frequency
    small_fx, small_fy = fx[keep_x], fy[keep_y]
    displayed_power = image_power[np.ix_(keep_y, keep_x)]
    structure = position_structure_factor(points, small_fx, small_fy)
    width, height = roi.shape[1] * scale, roi.shape[0] * scale
    grid_x, grid_y = np.meshgrid(small_fx, small_fy)
    # Exact finite-rectangle expectation for independent uniform, equal-weight points.
    uniform_expected = 1 + (len(points) - 1) * (
        np.sinc(grid_x * width) * np.sinc(grid_y * height)) ** 2
    radial_edges = np.linspace(0, max_frequency, 21)
    radial_s, counts = radial_average(structure, small_fx, small_fy, radial_edges)
    radial_uniform, _ = radial_average(uniform_expected, small_fx, small_fy, radial_edges)
    output = project / "lesson_27_results"
    output.mkdir(exist_ok=True)
    np.savez_compressed(output / "spectra.npz", fx=fx, fy=fy, image_power=image_power,
                        structure_fx=small_fx, structure_fy=small_fy, structure=structure,
                        uniform_expected=uniform_expected, positions_nm=points)
    with (output / "radial_structure.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["f_start_cycles_nm", "f_stop_cycles_nm", "grid_modes", "mean_structure", "uniform_expectation"])
        writer.writerows(zip(radial_edges[:-1], radial_edges[1:], counts, radial_s, radial_uniform))
    metadata = {"source_parameters": parameters, "position_count": len(points),
                "use_hann_window": use_hann_window, "frequency_units": "cycles per nm",
                "wavevector_conversion": "q = 2*pi*f in radians per nm", "wavelength_conversion": "lambda = 1/|f| for nonzero frequency",
                "frequency_spacing_x": 1 / width, "frequency_spacing_y": 1 / height,
                "nyquist_cycles_nm": 1 / (2 * scale), "display_max_frequency": max_frequency,
                "image_preparation": "Subtract window-weighted mean, apply chosen window; power divided by sum(window^2)",
                "structure_definition": "Equal-weight finite-sample |sum exp(-2*pi*i*f dot r)|^2/N; no physical scattering factors",
                "zero_mode": "Raw S(0)=N saved; omitted only from structure display and radial averages",
                "finite_window_baseline": "1+(N-1)*[sinc(fx*width)*sinc(fy*height)]^2; independent uniform positions",
                "positions_sha256": hashlib.sha256((source / "reference_positions.csv").read_bytes()).hexdigest(),
                "status": "Exploratory projected nanoparticle organisation; no atomic lattice or diffraction claim"}
    (output / "parameters.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    zero_x, zero_y = np.flatnonzero(small_fx == 0)[0], np.flatnonzero(small_fy == 0)[0]
    print("Manual centres:", len(points))
    print("Hann image window:", use_hann_window)
    print(f"Frequency spacing: {1/width:.6f} cycles/nm horizontally; {1/height:.6f} vertically")
    print(f"Pixel-grid Nyquist frequency: {1/(2*scale):.3f} cycles/nm (not a verified instrument resolution)")
    print(f"Raw point S(0): {structure[zero_y, zero_x]:.1f}; excluded from plotted centre and radial means")
    print("Example: f = 0.05 cycles/nm corresponds to wavelength 20 nm.")
    print("Image power includes particle appearance; centre structure uses equal-weight positions only.")

    fig, axes = plt.subplots(2, 2, figsize=(12, 10), layout="constrained")
    axes[0,0].imshow(roi,cmap="gray",vmin=0,vmax=255,extent=(0,width,height,0),interpolation="nearest")
    axes[0,0].scatter(points[:,0],points[:,1],facecolors="none",edgecolors="lime",s=60)
    axes[0,0].set_title("Real-space TEM crop and manual centres")
    axes[0,0].set_xlabel("x (nm)")
    axes[0,0].set_ylabel("y (nm)")
    # Half-bin margins put plotted pixel centres at the specified frequencies.
    dx, dy = small_fx[1]-small_fx[0], small_fy[1]-small_fy[0]
    extent=(small_fx[0]-dx/2,small_fx[-1]+dx/2,small_fy[0]-dy/2,small_fy[-1]+dy/2)
    log_power=np.log10(np.maximum(displayed_power,1e-12))
    display=axes[0,1].imshow(log_power,origin="lower",extent=extent,cmap="magma",vmin=0,vmax=7,interpolation="nearest")
    axes[0,1].set_title("Image Fourier power (log display)")
    fig.colorbar(display,ax=axes[0,1],label="log10 power (arbitrary intensity units)")
    visible_structure=structure.copy()
    visible_structure[zero_y,zero_x]=np.nan
    display=axes[1,0].imshow(visible_structure,origin="lower",extent=extent,cmap="viridis",vmin=0,vmax=8,interpolation="nearest")
    axes[1,0].set_title("Equal-weight centre structure factor; S(0) hidden")
    fig.colorbar(display,ax=axes[1,0],label="S(f), dimensionless",extend="max")
    for ax in [axes[0,1],axes[1,0]]:
        ax.set_xlabel("fx (cycles/nm)")
        ax.set_ylabel("fy (cycles/nm)")
    mid=(radial_edges[:-1]+radial_edges[1:])/2
    axes[1,1].plot(mid,radial_s,"o-",label="Manual-centre radial average")
    axes[1,1].plot(mid,radial_uniform,"k--",label="Uniform finite-window expectation")
    axes[1,1].set_xlabel("Frequency magnitude |f| (cycles/nm)")
    axes[1,1].set_ylabel("Mean S(f) in frequency annulus")
    axes[1,1].set_title("Radial averaging loses directional information")
    axes[1,1].legend(fontsize=8)
    fig.savefig(project / "lesson_27.png",dpi=150)
    print("Saved arrays and settings in:", output)
    plt.show()


if __name__ == "__main__":
    main()
