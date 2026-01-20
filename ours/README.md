## test_clinic.py
```
python test_clinic.py   --model_dir pretrained_model/InDuDoNet_latest.pt   --data_path ours/test   --save_path "results/CLINIC_metal_640*640*0.25"
輸出: InDuDoNet/results/CLINIC_metal
```

## ours/cbct_to_nifit.py
```
python cbct_to_nifit.py
輸出: data_resample/
```

##   ours/python debug_mask.py
```
python debug_mask.py 
輸出: threshold_debug/
```

## ours/view_before_after.py

將推論前、推論後的結果視覺化
Input: `ours/data_640*640*0.25`、``

```
python view_before_after.py \
  --raw_root "data_640*640*0.25" \
  --mar_root "../results/CLINIC_metal_640*640*0.25/X_mar" \
  --out_root "visualize/640*640*0.25/" \
  --case_id 57969132 \
  --vmin -1000 --vmax 4500 \
  --every 1
```

## ours/save_mar_png.py

以 HU 視覺輸出
```
python save_mar_png.py \
  --mar "../results/CLINIC_metal_640*640*0.25/X_mar/57969132_cbct.nii.gz" \
  --out_dir "visualize/640x640x0.25/57969132" \
  --target 640 \
  --vmin -1000 --vmax 4500 \
  --every 1
```

直接用 0~1 顯示（不轉 HU）
```
python save_mar_png.py \
  --mar "../results/CLINIC_metal_640*640*0.25/X_mar/57969132_cbct.nii.gz" \
  --out_dir "visualize/640x640/57969132_cbct_norm" \
  --target 640 \
  --no_hu \
  --vmin 0 --vmax 1 \
  --every 1
```