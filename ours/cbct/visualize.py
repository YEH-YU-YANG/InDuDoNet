import os
import argparse
from pathlib import Path
import numpy as np
import nibabel as nib
from PIL import Image
from .utils import get_slope_inter, mar01_to_hu, window_to_uint8, resize2d

def save_slice(slice_3d: np.ndarray, target_hw: tuple, no_hu: bool, vmin: float, vmax: float, output_path: Path):
    """
    Saves a single slice as a PNG file.
    """
    slice_2d = resize2d(slice_3d, target_hw)
    if no_hu:
        display = slice_2d
    else:
        display = mar01_to_hu(slice_2d)

    u8_slice = window_to_uint8(display, vmin, vmax)
    Image.fromarray(u8_slice, mode="L").save(output_path)

def save_mar_png(mar_path: Path, out_dir: Path, target: int, vmin: float, vmax: float, start: int, end: int, every: int, no_hu: bool):
    """
    Saves axial slices of a single MAR-processed NIfTI volume as individual PNG files.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    mar_nii = nib.load(str(mar_path))
    mar_slope, mar_inter = get_slope_inter(mar_nii)
    mar_proxy = mar_nii.dataobj

    if mar_proxy.ndim == 4:
        mar_proxy = mar_proxy[..., 0]

    Hm, Wm, Sm = mar_proxy.shape
    S = Sm
    start = max(0, start)
    end = (S - 1) if end < 0 else min(S - 1, end)
    target_hw = (target, target)

    print(f"mar={mar_path.name} shape=({Hm},{Wm},{Sm})")
    print(f"Export slices [{start}..{end}] every {every} -> {out_dir} as {target}x{target}")

    for i in range(start, end + 1, every):
        mar2d = np.asarray(mar_proxy[:, :, i]).astype(np.float32) * mar_slope + mar_inter
        output_path = out_dir / f"{i:04d}.png"
        save_slice(mar2d, target_hw, no_hu, vmin, vmax, output_path)

        if i == start or ((i - start) // every) % 50 == 0:
            print("saved", output_path.name)

    print("Done.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mar", required=True, help="推論輸出 NIfTI（results/.../X_mar/xxx.nii或.nii.gz）")
    ap.add_argument("--out_dir", required=True, help="輸出 PNG 資料夾")
    ap.add_argument("--target", type=int, default=640, help="目標尺寸（預設 640，輸出 target×target）")
    ap.add_argument("--vmin", type=float, default=-1000, help="window vmin（HU）")
    ap.add_argument("--vmax", type=float, default=4500, help="window vmax（HU）")
    ap.add_argument("--start", type=int, default=0, help="起始 slice index（0-based）")
    ap.add_argument("--end", type=int, default=-1, help="結束 slice index（含），-1 表示到最後")
    ap.add_argument("--every", type=int, default=1, help="每隔幾張存一張（1=全存）")
    ap.add_argument("--no_hu", action="store_true",
                    help="不要把 0~1 反推回 HU，直接以 0~1 做 window（此時 vmin/vmax 建議設 0~1）")
    args = ap.parse_args()

    save_mar_png(Path(args.mar), Path(args.out_dir), args.target, args.vmin, args.vmax, args.start, args.end, args.every, args.no_hu)

if __name__ == "__main__":
    main()