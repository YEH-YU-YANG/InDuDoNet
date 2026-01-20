import os
import numpy as np
import nibabel as nib
import imageio.v2 as imageio

# 改成你的某個 nii / nii.gz
NII_PATH = "data_origin/28643177.nii.gz"
SLICE_K = 204  # 先隨便給，等下可改成你想看的那張
THRS = [1500, 2000, 2500, 3000, 4000]
OUT_DIR = "threshold_debug"
os.makedirs(OUT_DIR, exist_ok=True)

vol = nib.load(NII_PATH).get_fdata().astype(np.float32)  # (H,W,S) or (H,W,S,1)
if vol.ndim == 4:
    vol = vol[..., 0]

# 如果你不知道要看哪一張，可以先找「>2500 最多」的 slice
counts = (vol > 2500).reshape(-1, vol.shape[-1]).sum(axis=0)
auto_k = int(np.argmax(counts))
print("auto SLICE_K =", auto_k, "count =", int(counts[auto_k]))

k = SLICE_K if SLICE_K > 0 else auto_k
img = vol[..., k]

# 視覺化用的 0-255
img_disp = np.clip(img, -1000, 3000)
img_u8 = ((img_disp - img_disp.min()) / (img_disp.max() - img_disp.min() + 1e-8) * 255).astype(np.uint8)
imageio.imwrite(os.path.join(OUT_DIR, f"slice{k}_img.png"), img_u8)

for thr in THRS:
    m = (img > thr).astype(np.uint8)
    overlay = img_u8.copy()
    overlay[m > 0] = 255
    imageio.imwrite(os.path.join(OUT_DIR, f"slice{k}_M_thr{thr}.png"), m * 255)
    imageio.imwrite(os.path.join(OUT_DIR, f"slice{k}_overlay_thr{thr}.png"), overlay)

print("Saved to:", OUT_DIR)
