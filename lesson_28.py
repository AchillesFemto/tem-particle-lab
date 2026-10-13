"""Lesson 28: alignment check, one-particle tracking, and motion measurements."""

import csv
import hashlib
import json
from pathlib import Path

import imageio.v2 as iio
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage
from skimage.feature import match_template
from skimage.registration import phase_cross_correlation


def decode_grayscale(movie):
    """Yield float grayscale arrays; video RGB is an exported display representation."""
    reader = iio.get_reader(movie, format="FFMPEG")
    try:
        for frame in reader:
            yield frame.astype(float).mean(axis=2)
    finally:
        reader.close()


def follow_template(frames, initial=(177, 274), half_width=25,
                    search_radius=8, sigma=1.5, min_score=0.5):
    """Track one fixed appearance template; stop instead of bridging suspect matches."""
    frames = iter(frames)
    first = next(frames)
    smoothed = ndimage.gaussian_filter(first, sigma)
    row, column = initial
    template = smoothed[row-half_width:row+half_width+1,
                        column-half_width:column+half_width+1].copy()
    expected_shape = (2*half_width+1, 2*half_width+1)
    if template.shape != expected_shape or np.std(template) == 0:
        raise ValueError("Initial template must be an in-bounds, nonconstant patch.")
    records = [{"frame": 0, "row_px": row, "column_px": column, "score": 1.0}]
    last = first
    stopped = "end_of_movie"
    for index, frame in enumerate(frames, start=1):
        # A larger search allows larger motion but more competing matches.
        r0, c0 = row-half_width-search_radius, column-half_width-search_radius
        r1, c1 = row+half_width+search_radius+1, column+half_width+search_radius+1
        if r0 < 35 or c0 < 30 or r1 > 440 or c1 > 470:
            stopped = f"frame_{index}: search area reaches excluded border/annotation zone"
            break
        smoothed = ndimage.gaussian_filter(frame, sigma)
        response = match_template(smoothed[r0:r1, c0:c1], template)
        peak_row, peak_column = np.unravel_index(response.argmax(), response.shape)
        score = float(response[peak_row, peak_column])
        on_limit = peak_row in (0,response.shape[0]-1) or peak_column in (0,response.shape[1]-1)
        if score < min_score or on_limit:
            stopped = f"frame_{index}: weak match ({score:.3f}) or peak at search limit ({on_limit})"
            break
        row, column = r0+peak_row+half_width, c0+peak_column+half_width
        records.append({"frame": index, "row_px": row, "column_px": column, "score": score})
        last = frame
    return records, first, last, stopped


def time_averaged_msd(positions_nm, frame_interval, max_lag=10):
    """Return mean squared displacements and sample counts for one contiguous track."""
    rows = []
    for lag in range(1,min(max_lag,len(positions_nm)-1)+1):
        difference = positions_nm[lag:] - positions_nm[:-lag]
        squared = np.sum(difference**2,axis=1)
        rows.append({"lag_frames":lag,"lag_seconds":lag*frame_interval,
                     "msd_nm2":float(squared.mean()),"displacement_pairs":len(squared)})
    return rows


def main():
    search_radius = 8  # Experiment: change only this to 16.
    initial = (177,274)  # Manually inspected patch centre in the FIRST movie frame.
    half_width = 25
    sigma = 1.5
    min_score = 0.5
    nm_per_pixel = 5.0/71.0  # This movie's bar, not the earlier image calibration.
    acquisition_fps = 7.5  # Source acquisition rate, consistent with printed timestamps.
    frame_interval = 1/acquisition_fps
    project = Path(__file__).resolve().parent
    movie = project / "data/public_tem_series/kang_2021/sciadv.abi5419_movie_s1.mp4"
    records, first, last, stopped = follow_template(decode_grayscale(movie), initial,
                    half_width, search_radius, sigma, min_score)
    if len(records)<2:
        raise ValueError("No usable motion sequence; inspect the template and matching settings.")

    # CONTROLLED synthetic alignment check; this is not an experimental drift measurement.
    reference = first[50:420,50:470]
    imposed = np.array([3.,-5.])
    shifted = ndimage.shift(reference,imposed,order=0,mode="constant",cval=float(reference.mean()))
    recovered, registration_error, _ = phase_cross_correlation(reference,shifted,
                                    upsample_factor=10,normalization=None)
    alignment_residual = recovered+imposed
    positions = np.array([[r["column_px"],r["row_px"]] for r in records])*nm_per_pixel
    elapsed = np.array([r["frame"] for r in records])*frame_interval
    displacement = np.linalg.norm(positions-positions[0],axis=1)
    for i,r in enumerate(records):
        r.update({"elapsed_seconds":float(elapsed[i]),"x_nm":positions[i,0],"y_nm":positions[i,1],
                  "displacement_from_start_nm":displacement[i],"status":"unvalidated_template_location"})
    msd = time_averaged_msd(positions,frame_interval)
    output = project / "lesson_28_results"
    output.mkdir(exist_ok=True)
    for name,rows in [("track.csv",records),("msd.csv",msd)]:
        with (output/name).open("w",newline="",encoding="utf-8") as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
            writer.writeheader();writer.writerows(rows)
    summary={"movie":str(movie.relative_to(project)),"source_movie_already_drift_corrected":True,
             "additional_experimental_registration_applied":False,
             "initial_patch_centre_row_column_px":list(initial),"template_half_width_px":half_width,
             "search_radius_px":search_radius,"gaussian_sigma_px":sigma,"minimum_match_score":min_score,
             "tracking_method":"Fixed initial template; integer-pixel normalized correlation peak; stop on weak/edge match",
             "tracked_frames":len(records),"stop_reason":stopped,
             "acquisition_fps":acquisition_fps,"encoded_playback_fps":15.0,
             "time_basis":"Elapsed frame index / 7.5; first frame is elapsed zero, not absolute movie timestamp",
             "nm_per_pixel":nm_per_pixel,"scale_basis":"Published 5 nm bar, first frame row 472, columns [32,103); raster width 71",
             "scale_assumptions":"Correct rendered bar and isotropic pixels; not independent instrument calibration",
             "synthetic_alignment_imposed_row_column_px":imposed.tolist(),
             "synthetic_alignment_recovered_correction_px":recovered.tolist(),
             "synthetic_alignment_residual_px":alignment_residual.tolist(),
             "synthetic_registration_error":float(registration_error),
             "minimum_observed_match_score":min(r["score"] for r in records[1:]),
             "net_displacement_nm":float(displacement[-1]),
             "movie_sha256":hashlib.sha256(movie.read_bytes()).hexdigest(),
             "status":"Illustrative one-particle template track; no validated identity, uncertainty or diffusion fit"}
    (output/"parameters.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print("Synthetic shift imposed (row,column):",imposed)
    print("Recovered correction:",recovered,"; residual:",alignment_residual)
    print("Experimental movie is already drift-corrected; no additional alignment applied.")
    print("Tracked frames:",len(records),"; stop:",stopped)
    print(f"Illustrative net displacement: {displacement[-1]:.3f} nm over {elapsed[-1]:.2f} s")
    print(f"Minimum match score: {summary['minimum_observed_match_score']:.3f}")
    print("MSD is a one-track description, not a fitted or validated diffusion coefficient.")

    fig,axes=plt.subplots(2,2,figsize=(12,10),layout="constrained")
    axes[0,0].imshow(first,cmap="gray",vmin=0,vmax=255,interpolation="nearest")
    axes[0,0].plot([r["column_px"] for r in records],[r["row_px"] for r in records],color="lime",linewidth=1)
    axes[0,0].scatter([initial[1]],[initial[0]],facecolors="none",edgecolors="red",s=80)
    axes[0,0].set_title("Initial frame and proposed trajectory (green)")
    axes[0,1].imshow(last,cmap="gray",vmin=0,vmax=255,interpolation="nearest")
    end=records[-1]
    axes[0,1].scatter(end["column_px"],end["row_px"],facecolors="none",edgecolors="red",s=100)
    axes[0,1].set_title(f"Last accepted frame {end['frame']}; inspect identity")
    for ax in axes[0]:
        ax.set_xlim(initial[1]-85,initial[1]+85)
        ax.set_ylim(initial[0]+85,initial[0]-85)
        ax.set_xlabel("Column in movie frame (pixels)")
        ax.set_ylabel("Row in movie frame (pixels)")
    axes[1,0].plot(elapsed,displacement,label="Distance from initial template location")
    axes[1,0].set_xlabel("Elapsed experimental time (s)")
    axes[1,0].set_ylabel("Displacement magnitude (nm)")
    axes[1,0].set_title("Image motion; residual drift/identity errors remain possible")
    axes[1,1].plot([r["lag_seconds"] for r in msd],[r["msd_nm2"] for r in msd],"o-")
    axes[1,1].set_xlabel("Time lag (s)")
    axes[1,1].set_ylabel("Time-averaged squared displacement (nm^2)")
    axes[1,1].set_title("One-track MSD: descriptive, no diffusion fit")
    fig.savefig(project/"lesson_28.png",dpi=150)
    # Match scores are saved for inspection; high correlation is not calibrated confidence.
    print("Saved motion results in:",output)
    plt.show()


if __name__=="__main__":
    main()
