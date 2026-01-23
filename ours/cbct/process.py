import os
import pydicom
import numpy as np
import nibabel as nib
from scipy.ndimage import zoom
from typing import List

def find_dicom_files(patient_dir: str) -> List[str]:
    """Find all DICOM files in a patient's directory."""
    if not os.path.exists(patient_dir):
        return []
    
    files = [os.path.join(patient_dir, f) for f in os.listdir(patient_dir) if f.lower().endswith(".dcm")]
    
    def sort_key(f):
        d = pydicom.dcmread(f, stop_before_pixels=True)
        return getattr(d, "InstanceNumber", 0)
    
    return sorted(files, key=sort_key)

def get_dicom_volume(files: List[str]) -> np.ndarray:
    """Create a 3D volume from a list of DICOM files."""
    first = pydicom.dcmread(files[0])
    H, W = first.pixel_array.shape
    num_slices = len(files)
    
    slope = float(getattr(first, "RescaleSlope", 1.0))
    intercept = float(getattr(first, "RescaleIntercept", 0.0))
    volume = np.zeros((H, W, num_slices), dtype=np.float32)
    
    for i, f in enumerate(files):
        d = pydicom.dcmread(f)
        img = d.pixel_array.astype(np.float32)
        img = img * slope + intercept
        volume[..., i] = img
        
    return volume

def resample_volume(volume: np.ndarray, original_spacing: List[float], target_spacing: float) -> np.ndarray:
    """Resample a volume to a target isotropic spacing."""
    zoom_factors = [s / target_spacing for s in original_spacing]
    return zoom(volume, zoom_factors, order=1)

def save_nifti(volume: np.ndarray, target_spacing: float, output_path: str):
    """Save a volume as a NIfTI file."""
    affine = np.diag([target_spacing, target_spacing, target_spacing, 1.0])
    img_nii = nib.Nifti1Image(volume, affine)
    nib.save(img_nii, output_path)

def process_patient(patient_id: str, base_data_dir: str, output_dir: str, target_spacing: float):
    """Process a single patient's CBCT data."""
    patient_dir = os.path.join(base_data_dir, patient_id, "cbct")
    files = find_dicom_files(patient_dir)
    
    if not files:
        print(f"{patient_id}：無DICOM檔案，跳過")
        return
        
    first = pydicom.dcmread(files[0])
    original_spacing = [
        float(first.PixelSpacing[0]),
        float(first.PixelSpacing[1]),
        float(getattr(first, "SliceThickness", 0.2))
    ]
    
    volume = get_dicom_volume(files)
    print(f"{patient_id} 原始：{volume.shape} x {original_spacing[0]:.3f}x{original_spacing[1]:.3f}x{original_spacing[2]:.3f}mm")
    
    volume_resampled = resample_volume(volume, original_spacing, target_spacing)
    new_H, new_W, new_Z = volume_resampled.shape
    print(f"  重採樣後：{new_H}x{new_W}x{new_Z} x {target_spacing}mm")
    
    output_path = os.path.join(output_dir, f"{patient_id}_cbct.nii.gz")
    save_nifti(volume_resampled, target_spacing, output_path)
    print(f"  → {output_path}")

def convert_cbct_to_nifti(patients: List[str], base_data_dir: str, output_dir: str, target_spacing: float):
    """Convert a list of patient CBCT DICOM series into NIfTI format."""
    os.makedirs(output_dir, exist_ok=True)
    print(f"開始處理 {len(patients)} 個病人：{patients}")
    print(f"轉換 + 重採樣到 {target_spacing}mm 進行中...\n")
    
    for patient_id in patients:
        process_patient(patient_id, base_data_dir, output_dir, target_spacing)
        
    print(f"\n完成！重採樣檔案在：{output_dir}")