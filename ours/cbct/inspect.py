import argparse
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
import pydicom

from .utils import safe_get, to_float_list, summarize_unique

def read_header(dcm_path: Path):
    # Only read header (not pixels), much faster
    return pydicom.dcmread(str(dcm_path), stop_before_pixels=True, force=True)

def read_full(dcm_path: Path):
    # Used only when pixel statistics are needed
    return pydicom.dcmread(str(dcm_path), force=True)

def series_sort_key(ds):
    # Sort by ImagePositionPatient (more reliable), then fall back to InstanceNumber
    ipp = safe_get(ds, "ImagePositionPatient", None)
    if ipp is not None and len(ipp) >= 3:
        try:
            return float(ipp[2])
        except Exception:
            pass
    inst = safe_get(ds, "InstanceNumber", None)
    try:
        return float(inst)
    except Exception:
        return 0.0

def inspect_series(files, pixel_sample=0):
    # Read headers
    headers = []
    for f in files:
        try:
            headers.append(read_header(f))
        except Exception as e:
            print(f"  [WARN] Failed to read header: {f} -> {e}")

    if not headers:
        return

    # Basic series information
    modality = [safe_get(ds, "Modality") for ds in headers]
    sop = [safe_get(ds, "SOPClassUID") for ds in headers]
    study = [safe_get(ds, "StudyInstanceUID") for ds in headers]
    series = [safe_get(ds, "SeriesInstanceUID") for ds in headers]
    series_desc = [safe_get(ds, "SeriesDescription") for ds in headers]
    series_num = [safe_get(ds, "SeriesNumber") for ds in headers]

    rows = [safe_get(ds, "Rows") for ds in headers]
    cols = [safe_get(ds, "Columns") for ds in headers]
    pxsp = [safe_get(ds, "PixelSpacing") for ds in headers]
    thick = [safe_get(ds, "SliceThickness") for ds in headers]
    sbs = [safe_get(ds, "SpacingBetweenSlices") for ds in headers]
    iop = [safe_get(ds, "ImageOrientationPatient") for ds in headers]

    slope = [safe_get(ds, "RescaleSlope") for ds in headers]
    intercept = [safe_get(ds, "RescaleIntercept") for ds in headers]

    bits = [safe_get(ds, "BitsAllocated") for ds in headers]
    bits_stored = [safe_get(ds, "BitsStored") for ds in headers]
    signed = [safe_get(ds, "PixelRepresentation") for ds in headers]  # 0 unsigned, 1 signed

    manu = [safe_get(ds, "Manufacturer") for ds in headers]
    model = [safe_get(ds, "ManufacturerModelName") for ds in headers]
    kernel = [safe_get(ds, "ConvolutionKernel") for ds in headers]
    kvp = [safe_get(ds, "KVP") for ds in headers]

    # Sorting check
    headers_sorted = sorted(headers, key=series_sort_key)
    z_list = []
    for ds in headers_sorted:
        ipp1 = safe_get(ds, "ImagePositionPatient", None)
        if ipp1 is not None and len(ipp1) >= 3:
            try:
                z_list.append(float(ipp1[2]))
            except Exception:
                pass

    order_info = "Unknown"
    if len(z_list) >= 2:
        diffs = np.diff(np.array(z_list, dtype=np.float64))
        nonzero = diffs[np.abs(diffs) > 1e-6]
        if nonzero.size == 0:
            order_info = "Likely all at the same location (IPP z has no change)"
        else:
            inc = np.all(nonzero > 0)
            dec = np.all(nonzero < 0)
            step_med = float(np.median(np.abs(nonzero)))
            order_info = f"IPP z {'increasing' if inc else ('decreasing' if dec else 'not monotonic')}, |dz| median={step_med:.4f}"
    else:
        # Fallback to InstanceNumber
        insts = [safe_get(ds, "InstanceNumber", None) for ds in headers_sorted]
        if any(v is not None for v in insts):
            order_info = "Using InstanceNumber for sorting (IPP insufficient)"
        else:
            order_info = "No IPP / InstanceNumber, sorting is unreliable"

    # Output
    print("  SeriesInstanceUID:", summarize_unique(series, max_show=1))
    print("  StudyInstanceUID :", summarize_unique(study, max_show=1))
    print("  SeriesNumber     :", summarize_unique(series_num, max_show=3))
    print("  SeriesDescription:", summarize_unique(series_desc, max_show=3))
    print("  Modality         :", summarize_unique(modality, max_show=3))
    print("  SOPClassUID      :", summarize_unique(sop, max_show=2))
    print("  Manufacturer     :", summarize_unique(manu, max_show=3))
    print("  ModelName        :", summarize_unique(model, max_show=3))
    print("  ConvolutionKernel:", summarize_unique(kernel, max_show=3))
    print("  KVP              :", summarize_unique(kvp, max_show=3))
    print("  Slices (file count):", len(headers))
    print("  Rows x Cols      :", summarize_unique(rows, max_show=3), "x", summarize_unique(cols, max_show=3))
    print("  PixelSpacing     :", summarize_unique([to_float_list(x) for x in pxsp], max_show=3))
    print("  SliceThickness   :", summarize_unique(thick, max_show=3))
    print("  SpacingBetween   :", summarize_unique(sbs, max_show=3))
    print("  ImageOrientation :", summarize_unique([to_float_list(x) for x in iop], max_show=2))
    print("  BitsAllocated    :", summarize_unique(bits, max_show=3),
          "| BitsStored:", summarize_unique(bits_stored, max_show=3),
          "| PixelRepr(0u/1s):", summarize_unique(signed, max_show=3))
    print("  RescaleSlope     :", summarize_unique(slope, max_show=3))
    print("  RescaleIntercept :", summarize_unique(intercept, max_show=3))
    print("  Sorting check    :", order_info)

    # Optional pixel sampling statistics
    if pixel_sample and files:
        n = len(files)
        k = min(pixel_sample, n)
        # Uniformly sample k slices
        idxs = np.linspace(0, n - 1, k, dtype=int)
        sampled_files = [files[i] for i in idxs]

        vals = []
        slope0 = None
        inter0 = None

        for f in sampled_files:
            try:
                ds = read_full(f)
                arr = ds.pixel_array.astype(np.float32)

                # Apply rescale if present
                s = safe_get(ds, "RescaleSlope", None)
                itc = safe_get(ds, "RescaleIntercept", None)
                if s is not None and itc is not None:
                    s = float(s)
                    itc = float(itc)
                    arr = arr * s + itc
                    if slope0 is None:
                        slope0, inter0 = s, itc

                vals.append(arr.reshape(-1))
            except Exception as e:
                print(f"  [WARN] Failed to read pixels: {f} -> {e}")

        if vals:
            v = np.concatenate(vals, axis=0)
            p01, p50, p99 = np.percentile(v, [1, 50, 99])
            vmin, vmax = float(np.min(v)), float(np.max(v))
            mean, std = float(np.mean(v)), float(np.std(v))

            print("  --- Pixel Sampling Statistics ---")
            if slope0 is not None:
                print(f"  (Rescale applied: slope={slope0}, intercept={inter0}; may approximate HU for CT, but not necessarily true HU for CBCT)")
            else:
                print("  (No rescale found; below are raw grayscale values)")
            print(f"  min={vmin:.3f}, p1={p01:.3f}, median={p50:.3f}, p99={p99:.3f}, max={vmax:.3f}, mean={mean:.3f}, std={std:.3f}")

            # For reference with InDuDoNet preprocessing "2500 HU" concept
            # If data is true HU, 2500 is usually high; if CBCT grayscale is different, this threshold may not apply
            thr = 2500.0
            frac = float(np.mean(v > thr))
            print(f"  Fraction >2500 (for reference): {frac*100:.4f}%")
        else:
            print("  [WARN] Could not get any pixel data for statistics")

def inspect_dicom_cbct(root: Path, pattern: str, ext: str, pixel_sample: int):
    """
    Scans a directory of DICOM files, groups them by series, and prints a detailed summary of their metadata.
    """
    if not root.is_dir():
        raise SystemExit(f"Root does not exist or is not a directory: {root}")

    # Scan all patients
    patients = sorted([p for p in root.iterdir() if p.is_dir()])
    if not patients:
        raise SystemExit("No subdirectories (patient folders) found in the root")

    for p in patients:
        cbct_dir = p / pattern
        if not cbct_dir.is_dir():
            continue

        # Collect dcm files
        if ext:
            files = sorted(cbct_dir.rglob(f"*{ext}"))
        else:
            files = sorted([x for x in cbct_dir.rglob("*") if x.is_file()])

        if not files:
            print(f"\n[Patient] {p.name} -> No DICOM files found in {cbct_dir}")
            continue

        # Group by SeriesInstanceUID
        groups = defaultdict(list)
        for f in files:
            try:
                ds = read_header(f)
                uid = safe_get(ds, "SeriesInstanceUID", "NO_UID")
                groups[str(uid)].append(f)
            except Exception as e:
                print(f"[WARN] Failed to read header: {f} -> {e}")

        print(f"\n[Patient] {p.name}  (Series count={len(groups)})")
        for uid, flist in groups.items():
            print(f"\n [Series] UID={uid}  (File count={len(flist)})")
            inspect_series(sorted(flist), pixel_sample=pixel_sample)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, required=True,
                    help="Root directory containing multiple patient folders, e.g., /data/root")
    ap.add_argument("--pattern", type=str, default="cbct",
                    help="Subfolder name under the patient folder, default: cbct")
    ap.add_argument("--ext", type=str, default=".dcm",
                    help="File extension, default: .dcm (can be empty string if no extension)")
    ap.add_argument("--pixel_sample", type=int, default=0,
                    help="Number of images to sample for pixel statistics per series (0 means no pixel reading)")
    args = ap.parse_args()

    inspect_dicom_cbct(Path(args.root), args.pattern, args.ext, args.pixel_sample)

if __name__ == "__main__":
    main()