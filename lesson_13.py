"""Lesson 13: example calibration, not a calibration of PG.tif."""


def main():
    # Invented teaching inputs: do not use these to measure PG.tif.
    scale_bar_nm = 50.0
    scale_bar_pixels = 100.0  # Experiment: change only this to 200.0.
    feature_length_pixels = 20.0
    region_pixel_count = 200

    if scale_bar_nm <= 0 or scale_bar_pixels <= 0:
        raise ValueError("Scale-bar length and pixel span must both be positive.")

    nm_per_pixel = scale_bar_nm / scale_bar_pixels
    feature_length_nm = feature_length_pixels * nm_per_pixel
    # This area conversion assumes equal physical pixel width and height.
    pixel_area_nm2 = nm_per_pixel ** 2
    region_area_nm2 = region_pixel_count * pixel_area_nm2

    print("SYNTHETIC CALIBRATION EXAMPLE ONLY - not PG.tif measurements")
    print("Assumption: square physical pixels")
    print(f"Known scale-bar length: {scale_bar_nm:.2f} nm")
    print(f"Scale-bar span: {scale_bar_pixels:.2f} pixels")
    print(f"Calibration: {nm_per_pixel:.4f} nm/pixel")
    print(f"Example feature length: {feature_length_nm:.2f} nm")
    print(f"Area per pixel: {pixel_area_nm2:.4f} nm^2")
    print(f"Example region area: {region_area_nm2:.2f} nm^2")


if __name__ == "__main__":
    main()
