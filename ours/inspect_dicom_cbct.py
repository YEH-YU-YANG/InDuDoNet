import argparse
import os
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
import pydicom


def safe_get(ds, name, default=None):
    return getattr(ds, name, default)


def read_header(dcm_path: Path):
    # 只讀 header（不讀像素），速度快很多
    return pydicom.dcmread(str(dcm_path), stop_before_pixels=True, force=True)


def read_full(dcm_path: Path):
    # 需要像素統計時才用
    return pydicom.dcmread(str(dcm_path), force=True)


def to_float_list(x):
    if x is None:
        return None
    try:
        return [float(v) for v in x]
    except Exception:
        return None


def summarize_unique(values, max_show=6):
    c = Counter([str(v) for v in values if v is not None])
    if not c:
        return "None"
    items = c.most_common(max_show)
    s = ", ".join([f"{k} (n={n})" for k, n in items])
    if len(c) > max_show:
        s += f", ... (+{len(c)-max_show} more)"
    return s


def series_sort_key(ds):
    # 用 ImagePositionPatient 排序（較可靠），不行再用 InstanceNumber
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
    # 讀 headers
    headers = []
    for f in files:
        try:
            headers.append(read_header(f))
        except Exception as e:
            print(f"  [WARN] 讀取 header 失敗: {f} -> {e}")

    if not headers:
        return

    # 基本集合資訊
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
    ipp = [safe_get(ds, "ImagePositionPatient") for ds in headers]

    slope = [safe_get(ds, "RescaleSlope") for ds in headers]
    intercept = [safe_get(ds, "RescaleIntercept") for ds in headers]

    bits = [safe_get(ds, "BitsAllocated") for ds in headers]
    bits_stored = [safe_get(ds, "BitsStored") for ds in headers]
    signed = [safe_get(ds, "PixelRepresentation") for ds in headers]  # 0 unsigned, 1 signed

    manu = [safe_get(ds, "Manufacturer") for ds in headers]
    model = [safe_get(ds, "ManufacturerModelName") for ds in headers]
    kernel = [safe_get(ds, "ConvolutionKernel") for ds in headers]
    kvp = [safe_get(ds, "KVP") for ds in headers]

    # 排序檢查
    headers_sorted = sorted(headers, key=series_sort_key)
    z_list = []
    for ds in headers_sorted:
        ipp1 = safe_get(ds, "ImagePositionPatient", None)
        if ipp1 is not None and len(ipp1) >= 3:
            try:
                z_list.append(float(ipp1[2]))
            except Exception:
                pass

    order_info = "未知"
    if len(z_list) >= 2:
        diffs = np.diff(np.array(z_list, dtype=np.float64))
        nonzero = diffs[np.abs(diffs) > 1e-6]
        if nonzero.size == 0:
            order_info = "疑似全部同一位置（IPP z 無變化）"
        else:
            inc = np.all(nonzero > 0)
            dec = np.all(nonzero < 0)
            step_med = float(np.median(np.abs(nonzero)))
            order_info = f"IPP z {'遞增' if inc else ('遞減' if dec else '不單調')}，|dz| 中位數={step_med:.4f}"
    else:
        # 退而求其次看 InstanceNumber
        insts = [safe_get(ds, "InstanceNumber", None) for ds in headers_sorted]
        if any(v is not None for v in insts):
            order_info = "使用 InstanceNumber 排序（IPP 不足）"
        else:
            order_info = "無 IPP / InstanceNumber，排序不可靠"

    # 輸出
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
    print("  Slices (檔案數)   :", len(headers))
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
    print("  排序檢查          :", order_info)

    # 像素抽樣統計（可選）
    if pixel_sample and files:
        n = len(files)
        k = min(pixel_sample, n)
        # 均勻抽樣 k 張
        idxs = np.linspace(0, n - 1, k, dtype=int)
        sampled = [files[i] for i in idxs]

        vals = []
        slope0 = None
        inter0 = None

        for f in sampled:
            try:
                ds = read_full(f)
                arr = ds.pixel_array.astype(np.float32)

                # 套 rescale（若存在）
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
                print(f"  [WARN] 讀取像素失敗: {f} -> {e}")

        if vals:
            v = np.concatenate(vals, axis=0)
            p01, p50, p99 = np.percentile(v, [1, 50, 99])
            vmin, vmax = float(np.min(v)), float(np.max(v))
            mean, std = float(np.mean(v)), float(np.std(v))

            print("  --- 像素抽樣統計 ---")
            if slope0 is not None:
                print(f"  (已套用 rescale: slope={slope0}, intercept={inter0}；若是 CT 可能近似 HU，但 CBCT 未必是真 HU)")
            else:
                print("  (未發現 rescale；以下為原始灰階)")
            print(f"  min={vmin:.3f}, p1={p01:.3f}, median={p50:.3f}, p99={p99:.3f}, max={vmax:.3f}, mean={mean:.3f}, std={std:.3f}")

            # 針對 InDuDoNet 前處理的「2500 HU」概念給你參考
            # 若資料真是 HU，2500 通常很高；若 CBCT 灰階不同，這門檻可能不適用
            thr = 2500.0
            frac = float(np.mean(v > thr))
            print(f"  >2500 的比例（參考用）: {frac*100:.4f}%")
        else:
            print("  [WARN] 無法取得任何像素資料做統計")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, required=True,
                    help="包含多個病人資料夾的根目錄，例如 /data/root")
    ap.add_argument("--pattern", type=str, default="cbct",
                    help="病人資料夾下的子資料夾名稱，預設 cbct")
    ap.add_argument("--ext", type=str, default=".dcm",
                    help="副檔名，預設 .dcm（若你沒有副檔名可改成空字串）")
    ap.add_argument("--pixel_sample", type=int, default=0,
                    help="每個 series 抽樣讀取像素的張數（0 表示不讀像素）")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        raise SystemExit(f"root 不存在或不是資料夾: {root}")

    # 掃描所有病人
    patients = sorted([p for p in root.iterdir() if p.is_dir()])
    if not patients:
        raise SystemExit("root 底下沒有任何子資料夾（病人資料夾）")

    for p in patients:
        cbct_dir = p / args.pattern
        if not cbct_dir.is_dir():
            continue

        # 收集 dcm
        if args.ext:
            files = sorted(cbct_dir.rglob(f"*{args.ext}"))
        else:
            files = sorted([x for x in cbct_dir.rglob("*") if x.is_file()])

        if not files:
            print(f"\n[Patient] {p.name} -> 找不到 DICOM 檔案 in {cbct_dir}")
            continue

        # 依 SeriesInstanceUID 分組
        groups = defaultdict(list)
        for f in files:
            try:
                ds = read_header(f)
                uid = safe_get(ds, "SeriesInstanceUID", "NO_UID")
                groups[str(uid)].append(f)
            except Exception as e:
                print(f"[WARN] 讀取 header 失敗: {f} -> {e}")

        print(f"\n[Patient] {p.name}  (series 數={len(groups)})")
        for uid, flist in groups.items():
            print(f"\n [Series] UID={uid}  (檔案數={len(flist)})")
            inspect_series(sorted(flist), pixel_sample=args.pixel_sample)


if __name__ == "__main__":
    main()
