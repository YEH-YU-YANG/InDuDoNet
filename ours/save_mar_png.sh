#!/bin/bash

# ================= 設定區域 =================
# [CPU 優化] 自動偵測核心數，如果沒有 nproc 指令則預設為 8
# 您也可以手動改為固定的數字，例如 N_WORKERS=16
N_WORKERS=$(nproc 2>/dev/null || echo 8)

# 路徑設定
RAW_DIR="data_640*640*0.25"
MAR_DIR="../results/CLINIC_metal_640*640*0.25/X_mar"
OUT_BASE="visualize/640x640x0.25/slices"

# 參數
TARGET=640
VMIN=-1000
VMAX=4500
EVERY=1

# ================= 準備工作 =================
mkdir -p "$OUT_BASE"

# 定義處理函式
run_slice_task() {
    filepath="$1"
    
    filename=$(basename "$filepath")
    case_id="${filename%_cbct.nii.gz}"
    case_out_dir="${OUT_BASE}/${case_id}"
    mar_path="${MAR_DIR}/${filename}"

    if [ ! -f "$mar_path" ]; then
        echo "[SKIP] MAR not found for: $case_id"
        return
    fi

    echo "Processing: $case_id"
    
    # [CPU 優化] 
    # 加入 OMP_NUM_THREADS=1 避免單一 process 搶佔所有核心
    # 加入 MKL_NUM_THREADS=1 (針對 Intel CPU)
    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python save_mar_png.py \
        --mar "$mar_path" \
        --out_dir "$case_out_dir" \
        --target "$TARGET" \
        --vmin "$VMIN" \
        --vmax "$VMAX" \
        --every "$EVERY"
}

export -f run_slice_task
export RAW_DIR MAR_DIR OUT_BASE TARGET VMIN VMAX EVERY

echo "=== Slice Generation ==="
echo "Total Cores/Workers: $N_WORKERS"
echo "Output: $OUT_BASE"

find "$RAW_DIR" -name "*_cbct.nii.gz" -print0 | xargs -0 -P "$N_WORKERS" -I {} bash -c 'run_slice_task "$@"' _ {}
echo "=== Complete ==="