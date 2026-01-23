import numpy as np
import nibabel as nib
from PIL import Image
from collections import Counter

def get_slope_inter(nii: nib.Nifti1Image):
    """
    Gets the slope and intercept from a NIfTI header.
    """
    slope, inter = nii.header.get_slope_inter()
    if slope is None:
        slope = 1.0
    if inter is None:
        inter = 0.0
    return float(slope), float(inter)


def mar01_to_hu(mar01: np.ndarray) -> np.ndarray:
    """
    Converts a 0-1 normalized MAR image to Hounsfield Units (HU).
    """
    # InDuDoNet clinic preprocess: x = HU/1000*0.192 + 0.192
    # inverse: HU = (x - 0.192)/0.192*1000
    return (mar01 - 0.192) / 0.192 * 1000.0


def window_to_uint8(x: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
    """
    Applies a window to an image and converts it to uint8.
    """
    x = np.clip(x, vmin, vmax)
    x = (x - vmin) / (vmax - vmin + 1e-8)
    return (x * 255.0).astype(np.uint8)


def resize2d(arr2d: np.ndarray, out_hw) -> np.ndarray:
    """
    Resizes a 2D array using Pillow.
    """
    H_out, W_out = out_hw
    im = Image.fromarray(arr2d.astype(np.float32), mode="F")
    resample = getattr(getattr(Image, "Resampling", Image), "BILINEAR")
    im = im.resize((W_out, H_out), resample=resample)
    return np.array(im, dtype=np.float32)

def rot_flip(x: np.ndarray, rot90: int = 0, flipud: bool = False, fliplr: bool = False) -> np.ndarray:
    """
    Rotates and flips an image.
    """
    if rot90:
        x = np.rot90(x, rot90)
    if flipud:
        x = np.flipud(x)
    if fliplr:
        x = np.fliplr(x)
    return x

def safe_get(ds, name, default=None):
    return getattr(ds, name, default)

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
