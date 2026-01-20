## InDuDoNet/test_clinic.py

推論: 從有偽影的影像，推論成去除偽影的影像

Input: 
- data_path : 推論前的 `.nni.gz` 檔案路徑，e.g.，`"InDuDoNet/ours/test"`


Output:
- save_path : 推論後的 `.nni.gz` 檔案路徑，e.g.，`"InDuDoNet/results/CLINIC_metal_640*640*0.25" `

Others:
- model_dir : 模型權重路徑，e.g.，`"InDuDoNet/pretrained_model/InDuDoNet_latest.pt"`

```
python test_clinic.py \
	--model_dir "pretrained_model/InDuDoNet_latest.pt" \
	--data_path "ours/test" \
	--save_path "results/CLINIC_metal_640*640*0.25"
```



## InDuDoNet/ours/cbct_to_nifit.py
輸出 : data_resample/
```
python cbct_to_nifit.py
```

## InDuDoNet/ours/python debug_mask.py
輸出 : threshold_debug/
```
python debug_mask.py 
```

## InDuDoNet/ours/view_before_after.py

將推論前、推論後的結果視覺化

Input: 
- raw_root : 推論前的 `.nni.gz` 位置，e.g.，`"InDuDoNet/ours/data_640*640*0.25"`
- mar_root : 推論後的 `.nni.gz` 位置，e.g.，`"InDuDoNet/results/CLINIC_metal_640*640*0.25/X_mar"`

Output:
- out_root : 推論前後的 `.nni.gz` 視覺化成為 `.png`，e.g.，`"InDuDoNet/ours/visualize/640*640*0.25/"`

Parameter:
- case_id : 指定病人的 `id`
- vmin、vmax : `HU` 顯示範圍
- every : 1=顯示每張切片

```
python view_before_after.py \
  --raw_root "data_640*640*0.25" \
  --mar_root "../results/CLINIC_metal_640*640*0.25/X_mar" \
  --out_root "visualize/640*640*0.25/" \
  --case_id 57969132 \
  --vmin -1000 --vmax 4500 \
  --every 1
```

## InDuDoNet/ours/save_mar_png.py

Input: 
- mar : 推論後的 `.nni.gz` 位置，e.g.，`"InDuDoNet/results/CLINIC_metal_640*640*0.25/X_mar/57969132_cbct.nii.gz"`


Output:
- out_dir : 推論後的 `.nni.gz` 視覺化成為 `.png` 的存放位置，e.g.，`"InDuDoNet/ours/visualize/640x640x0.25/57969132" `

Parameter:
- target : `.png` 的長寬
- vmin、vmax : `HU` 顯示範圍
- every : 1=顯示每張切片
- no_hu : 不轉成 `HU`，輸出值在 `0~1`

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