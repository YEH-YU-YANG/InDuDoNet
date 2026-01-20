#!/usr/bin/env python3
import os
import pydicom
import numpy as np
import nibabel as nib
from scipy.ndimage import zoom

# 指定病人清單
PATIENTS = [
    # "2188726",
    # "4333498",
    # "18234781",
    # "21800298",
    # "24937292",
    # "28643177",
    # "33208616",
    # "33802992",
    # "35290820",
    # "36719405",
    # "37460134",
    # "40657603",
    # "52730449",
    # "56872376", 
    # "57969132",

    "15235753",
    "49095613",
    "73141798"
]

base_data_dir = "/home/p76144736/yeh/paper_related_project/ToothSegmentation/data/"
output_dir = "./data_resample"  # 改名避免覆蓋
os.makedirs(output_dir, exist_ok=True)

print(f"開始處理 {len(PATIENTS)} 個病人：{PATIENTS}")
print("轉換 + 重採樣到 0.25mm 進行中...\n")

for PATIENT in PATIENTS:
    root = f"{base_data_dir}/{PATIENT}/cbct"
    
    if not os.path.exists(root):
        print(f"{PATIENT}：路徑不存在，跳過")
        continue
    
    files = [os.path.join(root, f) for f in os.listdir(root) if f.lower().endswith(".dcm")]
    if len(files) == 0:
        print(f"{PATIENT}：無DICOM檔案，跳過")
        continue
    
    # 排序
    def sort_key(f):
        d = pydicom.dcmread(f, stop_before_pixels=True)
        return getattr(d, "InstanceNumber", 0)
    
    files = sorted(files, key=sort_key)
    
    # 讀取第一張取得原始 spacing
    first = pydicom.dcmread(files[0])
    orig_sx, orig_sy = map(float, first.PixelSpacing)  # 0.2
    orig_sz = float(getattr(first, "SliceThickness", 0.2))
    
    H, W = first.pixel_array.shape
    num_slices = len(files)
    
    # 建立原始 volume
    slope = float(getattr(first, "RescaleSlope", 1.0))
    intercept = float(getattr(first, "RescaleIntercept", 0.0))
    volume = np.zeros((H, W, num_slices), dtype=np.float32)
    for i, f in enumerate(files):
        d = pydicom.dcmread(f)
        img = d.pixel_array.astype(np.float32)
        img = img * slope + intercept
        volume[..., i] = img
    
    print(f"{PATIENT} 原始：{volume.shape} x {orig_sx:.3f}x{orig_sy:.3f}x{orig_sz:.3f}mm")
    
    # 重採樣到 0.25mm (保持物理尺寸)
    target_spacing = 0.25
    zoom_x = orig_sx / target_spacing  # 0.2/0.25 = 0.8
    zoom_y = orig_sy / target_spacing
    zoom_z = orig_sz / target_spacing
    
    volume_resampled = zoom(volume, (zoom_x, zoom_y, zoom_z), order=1)
    
    # 新尺寸
    new_H, new_W, new_Z = volume_resampled.shape
    print(f"  重採樣後：{new_H}x{new_W}x{new_Z} x 0.25mm")
    
    # 儲存
    affine = np.diag([target_spacing, target_spacing, target_spacing, 1.0])
    out_dir = os.path.join(output_dir)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{PATIENT}_cbct.nii.gz")
    
    img_nii = nib.Nifti1Image(volume_resampled, affine)
    nib.save(img_nii, out_path)
    
    print(f"  → {out_path}")

print(f"\n完成！重採樣檔案在：{output_dir}")
