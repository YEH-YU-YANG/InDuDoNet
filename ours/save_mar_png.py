import argparse
from pathlib import Path

import numpy as np
import nibabel as nib
from PIL import Image


def get_slope_inter(nii: nib.Nifti1Image):
    slope, inter = nii.header.get_slope_inter()
    if slope is None:
        slope = 1.0
    if inter is None:
        inter = 0.0
    return float(slope), float(inter)


def mar01_to_hu(mar01: np.ndarray) -> np.ndarray:
    # InDuDoNet clinic preprocess: x = HU/1000*0.192 + 0.192
    # inverse: HU = (x - 0.192)/0.192*1000
    return (mar01 - 0.192) / 0.192 * 1000.0


def window_to_uint8(x: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
    x = np.clip(x, vmin, vmax)
    x = (x - vmin) / (vmax - vmin + 1e-8)
    return (x * 255.0).astype(np.uint8)


def resize2d(arr2d: np.ndarray, out_hw) -> np.ndarray:
    H_out, W_out = out_hw
    im = Image.fromarray(arr2d.astype(np.float32), mode="F")
    resample = getattr(getattr(Image, "Resampling", Image), "BILINEAR")
    im = im.resize((W_out, H_out), resample=resample)
    return np.array(im, dtype=np.float32)


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

    mar_path = Path(args.mar)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    mar_nii = nib.load(str(mar_path))
    mar_slope, mar_inter = get_slope_inter(mar_nii)
    mar_proxy = mar_nii.dataobj

    if mar_proxy.ndim == 4:
        # 如果不小心是 4D，取第一個通道
        mar_proxy = mar_proxy[..., 0]

    Hm, Wm, Sm = mar_proxy.shape
    S = Sm
    start = max(0, args.start)
    end = (S - 1) if args.end < 0 else min(S - 1, args.end)

    target_hw = (args.target, args.target)

    print(f"mar={mar_path.name} shape=({Hm},{Wm},{Sm})")
    print(f"Export slices [{start}..{end}] every {args.every} -> {out_dir} as {args.target}x{args.target}")

    for i in range(start, end + 1, args.every):
        mar2d = np.asarray(mar_proxy[:, :, i]).astype(np.float32) * mar_slope + mar_inter  # 通常仍是 0~1
        mar2d = resize2d(mar2d, target_hw)

        if args.no_hu:
            # 直接把 0~1 做 window（建議 vmin=0,vmax=1）
            disp = mar2d
        else:
            # 反推回近似 HU 再 window（較符合 CT 視覺）
            disp = mar01_to_hu(mar2d)

        u8 = window_to_uint8(disp, args.vmin, args.vmax)
        out_path = out_dir / f"slice_{i:04d}.png"
        Image.fromarray(u8, mode="L").save(out_path)

        if i == start or ((i - start) // args.every) % 50 == 0:
            print("saved", out_path.name)

    print("Done.")


if __name__ == "__main__":
    main()
