import argparse
from pathlib import Path

import numpy as np
import nibabel as nib
from PIL import Image

from .utils import get_slope_inter, mar01_to_hu, window_to_uint8, resize2d, rot_flip

def key_from_path(p: Path) -> str:
    """把 xxx.nii 或 xxx.nii.gz 轉成 key=xxx"""
    name = p.name
    if name.endswith(".nii.gz"):
        return name[:-7]
    if name.endswith(".nii"):
        return name[:-4]
    return p.stem

def find_nii_by_key(root: Path, key: str) -> Path:
    """在 root 下找 key.nii.gz 或 key.nii；找不到就 raise。"""
    cand1 = root / f"{key}.nii.gz"
    cand2 = root / f"{key}.nii"
    if cand1.exists():
        return cand1
    if cand2.exists():
        return cand2

    # 退而求其次：用 glob 模糊找（有些檔名可能多 suffix）
    hits = sorted(root.glob(f"{key}*.nii*"))
    if hits:
        return hits[0]

    raise FileNotFoundError(f"找不到病例 {key} 的 NIfTI：在 {root} 下找不到 {key}.nii.gz / {key}.nii")

def list_nii(root: Path):
    return sorted(list(root.glob("*.nii")) + list(root.glob("*.nii.gz")))

def make_triptych(before_u8, after_u8, diff_u8, gap=8):
    H, W = before_u8.shape
    out = Image.new("L", (W * 3 + gap * 2, H), color=0)
    out.paste(Image.fromarray(before_u8), (0, 0))
    out.paste(Image.fromarray(after_u8), (W + gap, 0))
    out.paste(Image.fromarray(diff_u8), (2 * W + 2 * gap, 0))
    return out

def export_one_case(raw_path: Path, mar_path: Path, out_dir: Path,
                    vmin: float, vmax: float, start: int, end: int, every: int,
                    rot90: int, flipud: bool, fliplr: bool):

    out_dir.mkdir(parents=True, exist_ok=True)

    raw_nii = nib.load(str(raw_path))
    mar_nii = nib.load(str(mar_path))

    raw_slope, raw_inter = get_slope_inter(raw_nii)
    mar_slope, mar_inter = get_slope_inter(mar_nii)

    raw_proxy = raw_nii.dataobj
    mar_proxy = mar_nii.dataobj

    if raw_proxy.ndim != 3 or mar_proxy.ndim != 3:
        raise RuntimeError(f"只支援 3D NIfTI，目前 raw ndim={raw_proxy.ndim}, mar ndim={mar_proxy.ndim}")

    Hr, Wr, Sr = raw_proxy.shape
    Hm, Wm, Sm = mar_proxy.shape

    S = min(Sr, Sm)
    start = max(0, start)
    end = (S - 1) if end < 0 else min(S - 1, end)

    print(f"[Case] raw={raw_path.name} shape={raw_proxy.shape} | mar={mar_path.name} shape={mar_proxy.shape}")
    print(f"       Export slices [{start}..{end}] every {every} -> {out_dir}")

    for i in range(start, end + 1, every):
        raw2d = np.asarray(raw_proxy[:, :, i]).astype(np.float32) * raw_slope + raw_inter
        raw2d = np.maximum(raw2d, -1000.0)

        mar01 = np.asarray(mar_proxy[:, :, i]).astype(np.float32) * mar_slope + mar_inter

        if (Hr, Wr) != (Hm, Wm):
            raw2d = resize2d(raw2d, (Hm, Wm))

        mar_hu = mar01_to_hu(mar01)

        raw2d = rot_flip(raw2d, rot90, flipud, fliplr)
        mar_hu = rot_flip(mar_hu, rot90, flipud, fliplr)

        before_u8 = window_to_uint8(raw2d, vmin, vmax)
        after_u8 = window_to_uint8(mar_hu, vmin, vmax)

        diff = mar_hu - raw2d
        dmin, dmax = np.percentile(diff, [1, 99])
        if float(dmax) - float(dmin) < 1e-6:
            dmin, dmax = float(np.min(diff)), float(np.max(diff))
            if float(dmax) - float(dmin) < 1e-6:
                dmin, dmax = -1.0, 1.0
        diff_u8 = window_to_uint8(diff, float(dmin), float(dmax))

        trip = make_triptych(before_u8, after_u8, diff_u8, gap=8)
        out_path = out_dir / f"{i:04d}.png"
        trip.save(out_path)

        if i == start or ((i - start) // every) % 20 == 0:
            print("  saved", out_path.name)

    print("  Done.")

def view_before_after(raw_root: Path, mar_root: Path, out_root: Path, case_id: str,
                      vmin: float, vmax: float, start: int, end: int, every: int,
                      rot90: int, flipud: bool, fliplr: bool):
    """
    Creates a side-by-side comparison PNG for each slice, showing the original image, 
    the MAR-processed image, and a difference map.
    """
    if not raw_root.is_dir():
        raise FileNotFoundError(f"--raw_root 不存在或不是資料夾：{raw_root}")
    if not mar_root.is_dir():
        raise FileNotFoundError(f"--mar_root 不存在或不是資料夾：{mar_root}")
    out_root.mkdir(parents=True, exist_ok=True)
 
    if case_id:
        key = case_id
        raw_path = find_nii_by_key(raw_root, key)
        mar_path = find_nii_by_key(mar_root, key)
        export_one_case(
            raw_path=raw_path,
            mar_path=mar_path,
            out_dir=out_root / key,
            vmin=vmin, vmax=vmax,
            start=start, end=end, every=every,
            rot90=rot90, flipud=flipud, fliplr=fliplr
        )
        return

    # Batch mode
    raw_files = list_nii(raw_root)
    mar_files = list_nii(mar_root)

    raw_map = {key_from_path(p): p for p in raw_files}
    mar_map = {key_from_path(p): p for p in mar_files}

    keys = sorted(set(raw_map.keys()) & set(mar_map.keys()))
    print(f"raw cases={len(raw_map)}, mar cases={len(mar_map)}, matched={len(keys)}")

    if not keys:
        raise RuntimeError("找不到同名病例。請確認 raw_root 與 mar_root 底下的檔名是否一致（例如 28643177.nii.gz）。")

    for key in keys:
        export_one_case(
            raw_path=raw_map[key],
            mar_path=mar_map[key],
            out_dir=out_root / key,
            vmin=vmin, vmax=vmax,
            start=start, end=end, every=every,
            rot90=rot90, flipud=flipud, fliplr=fliplr
        )

def main():
    ap = argparse.ArgumentParser()

    # New paths
    ap.add_argument("--raw_root", type=str, required=True, help="原始 NIfTI 資料夾（例如 data_origin/）")
    ap.add_argument("--mar_root", type=str, required=True, help="推論輸出 NIfTI 資料夾（例如 ../results/.../X_mar/）")
    ap.add_argument("--out_root", type=str, required=True, help="輸出根資料夾（每位病人會輸出到 out_root/<case_id>/）")

    # Single patient (optional)
    ap.add_argument("--case_id", type=str, default="", help="指定單一病人 ID（檔名不含副檔名，例如 28643177）")

    # Display/output control
    ap.add_argument("--vmin", type=float, default=-1000)
    ap.add_argument("--vmax", type=float, default=4500)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=-1)
    ap.add_argument("--every", type=int, default=1)

    # Visualization orientation (optional)
    ap.add_argument("--rot90", type=int, default=0)
    ap.add_argument("--flipud", action="store_true")
    ap.add_argument("--fliplr", action="store_true")

    args = ap.parse_args()

    view_before_after(
        raw_root=Path(args.raw_root).expanduser().resolve(),
        mar_root=Path(args.mar_root).expanduser().resolve(),
        out_root=Path(args.out_root).expanduser().resolve(),
        case_id=args.case_id,
        vmin=args.vmin, vmax=args.vmax,
        start=args.start, end=args.end, every=args.every,
        rot90=args.rot90, flipud=args.flipud, fliplr=args.fliplr
    )

if __name__ == "__main__":
    main()