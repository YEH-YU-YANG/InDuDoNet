import os
import numpy as np
import nibabel as nib
import imageio.v2 as imageio
from pathlib import Path

def debug_mask(nii_path: Path, out_dir: Path, slice_k: int, thrs: list):
    """
    Visualizes the effect of different HU thresholds on a specific slice of a NIfTI volume.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    vol = nib.load(nii_path).get_fdata().astype(np.float32)
    if vol.ndim == 4:
        vol = vol[..., 0]

    # If slice_k is not specified, find the slice with the most pixels > 2500
    if slice_k < 0:
        counts = (vol > 2500).reshape(-1, vol.shape[-1]).sum(axis=0)
        slice_k = int(np.argmax(counts))
        print("auto SLICE_K =", slice_k, "count =", int(counts[slice_k]))

    img = vol[..., slice_k]

    # Visualization to 0-255
    img_disp = np.clip(img, -1000, 3000)
    img_u8 = ((img_disp - img_disp.min()) / (img_disp.max() - img_disp.min() + 1e-8) * 255).astype(np.uint8)
    imageio.imwrite(out_dir / f"slice{slice_k}_img.png", img_u8)

    for thr in thrs:
        m = (img > thr).astype(np.uint8)
        overlay = img_u8.copy()
        overlay[m > 0] = 255
        imageio.imwrite(out_dir / f"slice{slice_k}_M_thr{thr}.png", m * 255)
        imageio.imwrite(out_dir / f"slice{slice_k}_overlay_thr{thr}.png", overlay)

    print("Saved to:", out_dir)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--nii_path", type=str, required=True, help="Path to a NIfTI file")
    parser.add_argument("--out_dir", type=str, default="threshold_debug", help="Output directory")
    parser.add_argument("--slice_k", type=int, default=-1, help="Slice to visualize (negative to auto-detect)")
    parser.add_argument("--thrs", type=int, nargs="+", default=[1500, 2000, 2500, 3000, 4000], help="Thresholds to test")
    args = parser.parse_args()

    debug_mask(Path(args.nii_path), Path(args.out_dir), args.slice_k, args.thrs)

if __name__ == "__main__":
    main()