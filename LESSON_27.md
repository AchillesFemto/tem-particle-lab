# Lesson 27: Fourier analysis and centre structure factors

This is the fourth of our five larger lessons. Work through four sections: spatial frequencies, the image power spectrum, the centre-position structure factor, and interpretation of reciprocal-space patterns.

## Run

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe lesson_27.py
```

Run Lesson 26 first if its saved positions are absent. No new packages are needed. The script reads the manual centres and their saved crop/calibration settings, saves `lesson_27.png`, and creates `lesson_27_results/` with numerical spectra, radial structure values and a parameter record. Rerunning replaces generated outputs without changing source data.

## A. What is spatial frequency?

An image can be represented as a sum of spatial waves with different spacings and directions. A Fourier transform expresses the image in terms of those waves. It helps describe repeated structure and characteristic length scales that may be difficult to see directly.

Spatial frequency f counts cycles per unit length. Its nonzero magnitude corresponds to wavelength:

```text
wavelength lambda = 1 / |f|
```

Thus f = 0.05 cycles/nm corresponds to 20 nm, while 0.10 cycles/nm corresponds to 10 nm. Higher spatial frequency means shorter spatial wavelength.

In two dimensions, `(fx, fy)` describes the direction as well as the frequency. A sinusoidal variation along x has its wavevector along x; stripes of constant intensity are perpendicular to that direction. The origin is zero frequency, describing the constant component.

Physics often uses angular wavevector q:

```text
q = 2*pi*f  (radians per nm)
lambda = 2*pi / |q|
```

Our plots use **cycles/nm**. Keep this convention explicit to avoid a factor-of-2*pi error when comparing with papers.

## B. Compute the image power spectrum

### Prepare the image for a finite crop

A discrete Fourier transform represents a finite array as if its values repeat. Opposite crop edges can meet discontinuously. That artificial jump can spread power across frequencies, called spectral leakage.

A **Hann window** gradually reduces image contributions toward its edges. It reduces abrupt joins but downweights edge particles, broadens spectral features and changes the measured spectrum. It is not a correction for missing particles or a way to improve microscope resolution.

```python
window = np.outer(np.hanning(rows), np.hanning(columns))
mean = np.sum(image * window) / np.sum(window)
prepared = (image.astype(float) - mean) * window
```

`np.hanning` creates a one-dimensional taper. `np.outer` multiplies the row and column tapers into a two-dimensional window.

The weighted mean removes global brightness before transformation. Using a window-weighted mean makes the prepared array's sum approximately zero, suppressing the image's zero-frequency brightness component. Floating-point conversion allows negative deviations from the mean without unsigned-integer arithmetic problems. These operations produce analysis arrays, not replacements for the source image.

With `use_hann_window = False`, the window becomes all ones and the calculation subtracts the ordinary mean without tapering.

### Transform and calculate power

```python
amplitude = np.fft.fftshift(np.fft.fft2(prepared))
power = np.abs(amplitude) ** 2 / np.sum(window ** 2)
```

`fft2` calculates the two-dimensional discrete Fourier transform. Its output is complex: each value encodes a wave's amplitude and phase. `fftshift` rearranges frequency locations to put zero in the middle for display; it does not filter the image.

`np.abs` gives the magnitude of each complex amplitude. Squaring gives power. Dividing by the window's squared-weight sum states our normalization convention and makes the overall window-energy scaling explicit. It does not make tapered and untapered spectra identical or establish an absolutely calibrated scattering intensity.

Our inputs are published PNG intensities. The image power includes particle contrast, size, shape, background texture and acquisition/export effects as well as positions. It is not automatically a particle structure factor or an electron-diffraction measurement.

### Calibrate frequency axes

```python
fx = np.fft.fftshift(np.fft.fftfreq(columns, d=nm_per_pixel))
fy = np.fft.fftshift(np.fft.fftfreq(rows, d=nm_per_pixel))
```

`fftfreq` labels the transform's sampled frequencies. `d` is the pixel spacing in nanometres, giving frequencies in cycles/nm.

For our approximately 92.49 nm window, adjacent frequency samples are approximately **0.010812 cycles/nm** apart. More pixels over the same field of view do not by themselves reduce this spacing; a larger field supplies finer frequency sampling. Tapering also limits effective spectral resolution.

The pixel-grid Nyquist frequency is approximately **4.325 cycles/nm**, half the sampling frequency. This is a sampling limit, not verified microscope resolution. We display only frequencies up to approximately 0.4 cycles/nm along each axis to focus on nanoparticle-scale organisation. Saved image spectra retain the full frequency range.

## C. Compute a structure factor from positions

To focus on organisation rather than particle appearance, replace each particle by an equal-weight point at its manual centre. No rasterized impulse image is needed: we sum wave contributions directly at the same Fourier-grid frequencies.

```python
for x, y in points:
    phase = -2j * np.pi * (grid_x * x + grid_y * y)
    amplitude += np.exp(phase)
structure = np.abs(amplitude) ** 2 / len(points)
```

Each position contributes a complex wave term. At some frequencies the contributions align and reinforce one another; at others they partly cancel. `2j` means twice the imaginary unit in Python, not a particle index. `np.exp` evaluates the complex exponential. The amplitude array accumulates contributions from all points, then squared magnitude divided by N gives the dimensionless equal-weight finite-sample structure factor.

In notation:

```text
S(f) = |sum_j exp(-2*pi*i*f dot r_j)|² / N
```

This is a two-dimensional position statistic. It assigns equal weight to all centres, ignoring differences in scattering strength or particle size. We do not compute atomic form factors or a crystallographic unit-cell structure factor.

At f = 0, every exponential equals one. Therefore amplitude is N and **S(0) = N = 19**. We save that raw value, but hide the one zero-frequency display pixel and omit it from radial averaging so it does not dominate interpretation. This is not an estimate of an infinite-system low-q limit or a compressibility measurement.

Translating every point by the same displacement changes Fourier phase but leaves S unchanged. Relative positions drive the pattern. Changing or missing individual positions can alter it.

### Finite-window baseline

A finite rectangular window itself contributes a Fourier signature. For independent uniform positions with fixed count, the exact expectation here is:

```text
E[S(fx,fy)] = 1 + (N-1) [sinc(fx*width) sinc(fy*height)]²
```

NumPy's sinc convention is `sin(pi*x)/(pi*x)`, with value one at zero. Our sampled frequencies are integer multiples of 1/width and 1/height, so the window term vanishes at nonzero Fourier-grid modes and the expected baseline is one. At arbitrary off-grid frequencies, the finite-window contribution need not vanish.

This is a model expectation, not a confidence interval. A finite sample of 19 points can produce strong speckle and peaks under random organisation. No significance claim follows from a bright spot alone.

## D. Read the figure and connect to real-space statistics

1. Top left: the real-space crop and manual centres from Lesson 26.
2. Top right: image Fourier power on a log10 display. Low frequencies lie near the centre. The log display makes weaker features visible; it does not change saved power values.
3. Bottom left: the equal-weight centre structure factor, with its zero-frequency point hidden. The colour bar is dimensionless and capped at eight for display; higher values remain saved.
4. Bottom right: averages of S over circular frequency annuli, compared with the uniform finite-window expectation. Radial averaging reduces directional information.

The image and centre spectra are expected to differ: particle outlines and contrast affect the image but are absent from the point calculation. In an ideal linear image of identical particle profiles placed at centres, Fourier power contains both the single-profile spectrum and the centre arrangement spectrum. Real TEM contrast, unequal profiles, overlapping projections, windowing and background complicate that simple relationship.

Lesson 26 described real-space pair separations. A structure factor also contains pair information: expanding the squared sum produces terms depending on position differences. In a homogeneous ensemble and suitable large-window limit, it is related to the Fourier transform of the excess pair correlation `g(r)-1`, plus the self term. Our small finite-window g(r) and S(f) are not interchangeable numerical transforms, and we do not invert one truncated noisy curve to obtain the other.

A reciprocal-space feature can suggest a length scale through 1/|f|, but it is not automatically a nearest-neighbour distance or a lattice constant. Window artefacts, profile sizes and finite-sample interference can produce features. Do not label this nanoparticle image as an atomic lattice or infer a quantum phase. Atomic-spacing analysis needs suitable high-resolution data, calibrated axes and a model linking the observed contrast to that lattice.

## Important code details

| Code | Purpose |
| --- | --- |
| csv/json/hashlib/Path imports | Read positions and save tables, structured settings and reproducibility fingerprints. |
| NumPy, Matplotlib, Pillow imports | Provide Fourier/array operations, plotting and original PNG reading. |
| image_power_spectrum(...) | Returns physically labelled frequency axes and the prepared image's power. |
| Shape/finite/positive-spacing checks | Reject inputs unsuitable for the stated calculation. |
| Conditional window expression | Uses a separable Hann taper or an all-ones array according to the experiment parameter. |
| rows, columns = image.shape | Read image dimensions in NumPy order. |
| np.sum and window ** 2 | Calculate the weighted mean and normalization denominator. |
| image.astype(float) | Permit signed deviations and floating-point calculations. |
| position_structure_factor(...) | Computes the direct equal-weight sum on a two-dimensional frequency grid. |
| points.shape[1] != 2 and len(points) | Require finite x/y position pairs and at least one centre. |
| np.meshgrid(fx,fy) | Form arrays of horizontal and vertical frequencies at every grid position. |
| np.zeros(...,dtype=complex) | Create an initially zero complex amplitude array. |
| for x,y in points | Unpack each centre's physical coordinates. |
| amplitude += ... | Add that centre's phase contribution at every frequency. |
| radial_average(...) | Average values in specified frequency annuli while excluding zero. |
| np.hypot(grid_x,grid_y) | Compute frequency-vector magnitudes. |
| zip(edges[:-1],edges[1:]) | Visit inner/outer boundaries for each radial bin. |
| selected Boolean comparisons | Include values inside the annulus, excluding its outer endpoint and the zero mode. |
| np.any(selected), np.nan | Report an empty frequency bin as undefined rather than zero. |
| main(), use_hann_window = True | Set the run and its single experiment parameter. |
| max_frequency = 0.4 | Set the display and radial-analysis range in cycles/nm. |
| File-existence check | Explain that Lesson 26 must supply saved reference positions. |
| json.loads, csv.DictReader | Load saved settings and named position columns. |
| float(...) | Convert CSV numeric text into physical coordinate values. |
| Saved crop and scale, Image.open and NumPy slice | Read the image window corresponding to the saved positions. |
| np.abs(fx/fy) <= max_frequency | Select the central frequency range without recomputing a smaller image transform. |
| np.ix_(keep_y,keep_x) | Select all row/column combinations of retained frequency indices. |
| np.sinc(...) | Compute the finite rectangular-window expectation. |
| np.linspace(0,max_frequency,21) | Create 20 radial bins of width 0.02 cycles/nm. |
| output.mkdir(exist_ok=True) | Create the results directory if needed. |
| np.savez_compressed | Save full numerical image power, centre spectra, axes and position inputs. |
| csv.writer and writerows(zip(...)) | Save each radial annulus with its mode count, mean and baseline. |
| Metadata dictionary, json.dumps, write_text | Record conventions, units, normalization and assumptions. |
| SHA256 of the position CSV | Identify the exact position input; it does not establish scientific correctness. |
| np.flatnonzero(... == 0)[0] | Locate the zero-frequency row/column. |
| print and numeric formatting | Report key dimensions and conventions. |
| plt.subplots(2,2,layout="constrained") | Arrange four comparison panels. |
| imshow and scatter on the TEM crop | Display original intensities and manual centres on nanometre axes. |
| Half-bin frequency extents | Place spectral display pixel centres at their actual frequency values. |
| np.log10(np.maximum(power,1e-12)) | Avoid log(0) while compressing power's range for display only. |
| vmin=0,vmax=7 in the log display | Use a fixed display range for comparing window settings; smaller or larger values use end colours. |
| structure.copy(), setting one pixel to np.nan | Hide S(0) only in a display copy; raw arrays retain it. |
| origin="lower" | Display signed frequency axes with positive fy upward. The underlying y coordinates follow image rows downward. |
| Colour bars, extend="max" | Explain units and indicate possible structure values above the colour limit. |
| Midpoints, plot and legend | Display radial annulus averages and the model expectation. Opposite frequency modes are not independent statistical samples. |
| fig.savefig, plt.show and main guard | Save the figure, request a window, and allow helper function imports. |

## Scientific limits

Published PNG intensities are not independently verified detector-linear signals. Mean removal, windowing and normalization are explicitly analytical choices. The image FFT cannot be read as calibrated diffraction intensity without an appropriate imaging/scattering model.

The centre calculation inherits annotation uncertainty, finite-field sampling and the scale-bar assumptions. Radial means lose directionality and have no uncertainty estimate in this lesson. A bright feature or peak cannot establish long-range order from one field of 19 points.

Finite-image Fourier modes are sampled grid values, not evidence that the physical sample has periodic boundary conditions. Increasing display resolution or adding zero padding cannot create new physical resolution. Larger representative fields and suitable high-resolution images are needed for more demanding materials questions.

## Your one experiment

Change only `use_hann_window = True` to `False`. Before running, predict:

1. Will crop-edge contributions be downweighted as strongly?
2. Can the image power spectrum change even though the source image is unchanged?
3. Will the centre-position structure factor change when positions and frequency grid are fixed?

Run and compare the two spectral panels. Windowing can reduce edge leakage while also broadening and reweighting specimen features. Do not equate the smoother-looking result with a more accurate physical interpretation. Current generated files are overwritten; save a copy first if you want both.

References: NumPy [Fourier-transform conventions](https://numpy.org/doc/2.2/reference/routines.fft.html), [fft2](https://numpy.org/doc/2.2/reference/generated/numpy.fft.fft2.html) and [fftfreq](https://numpy.org/doc/2.2/reference/generated/numpy.fft.fftfreq.html); the [freud direct structure-factor introduction](https://freud.readthedocs.io/en/v3.2.0/gettingstarted/examples/module_intros/diffraction.StaticStructureFactor.html) provides the general position-sum definition. We implement the two-dimensional sum directly in NumPy, without installing freud. Source attribution: [TEM sample README](data/public_tem/README.md).
