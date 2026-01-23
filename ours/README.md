# CBCT Processing and Visualization Tool

This project provides a suite of Python scripts for processing and visualizing Cone-Beam CT (CBCT) data, with a focus on Metal Artifact Reduction (MAR).

## Project Structure

The project is organized into the following directories:

- `cbct/`: Python module containing the core functionality for processing and visualizing CBCT data.
- `scripts/`: Main CLI entry point.
- `tests/`: Unit tests.

## Installation

The following libraries are required:

- `pydicom`
- `numpy`
- `nibabel`
- `scipy`
- `Pillow`
- `imageio`

You can install them with pip:

```bash
pip install pydicom numpy nibabel scipy Pillow imageio
```

## Usage

The main entry point for this project is `scripts/main.py`. This script provides a CLI for converting DICOM files to NIfTI, visualizing MAR results, and comparing before and after images.

### Convert DICOM to NIfTI

To convert a list of patient CBCT DICOM series into NIfTI format, use the `convert` command:

```bash
python scripts/main.py convert <patient_id_1> <patient_id_2> ... \
    --base_dir <base_data_dir> \
    --output_dir <output_dir> \
    --spacing <target_spacing>
```

### Visualize MAR Results

To save axial slices of a single MAR-processed NIfTI volume as individual PNG files, use the `visualize` command:

```bash
python scripts/main.py visualize \
    --mar <mar_nifti_file> \
    --out_dir <output_dir> \
    --target <target_size> \
    --vmin <window_vmin> \
    --vmax <window_vmax> \
    --start <start_slice> \
    --end <end_slice> \
    --every <every_n_slices> \
    --no_hu
```

### Compare Before and After MAR

To create a side-by-side comparison PNG for each slice, showing the original image, the MAR-processed image, and a difference map, use the `compare` command:

```bash
python scripts/main.py compare \
    --raw_root <raw_nifti_root> \
    --mar_root <mar_nifti_root> \
    --out_root <output_root> \
    --case_id <case_id> \
    --vmin <window_vmin> \
    --vmax <window_vmax> \
    --start <start_slice> \
    --end <end_slice> \
    --every <every_n_slices> \
    --rot90 <rot90> \
    --flipud \
    --fliplr
```

### Inspect DICOM Files

To scan a directory of DICOM files, group them by series, and print a detailed summary of their metadata, use the `inspect` command:

```bash
python scripts/main.py inspect \
    --root <dicom_root> \
    --pattern <dicom_dir_pattern> \
    --ext <dicom_file_extension> \
    --pixel_sample <num_pixels_to_sample>
```

### Debug Mask Thresholds

To visualize the effect of different HU thresholds on a specific slice of a NIfTI volume, use the `debug` command:

```bash
python scripts/main.py debug \
    --nii_path <nifti_file> \
    --out_dir <output_dir> \
    --slice_k <slice_to_visualize> \
    --thrs <thresholds_to_test>
```
