#!/bin/bash

# ================= 設定區域 =================
# [CPU 優化] 使用最大核心數
N_WORKERS=$(nproc 2>/dev/null || echo 8)

# 路徑設定
RAW_DIR="data_640*640*0.25"
MAR_DIR="../results/CLINIC_metal_640*640*0.25/X_mar"
OUT_BASE="visualize/640x640x0.25/comparisons"

# 參數
VMIN=-1000
VMAX=4500
EVERY=1

# ================= 準備工作 =================
mkdir -p "$OUT_BASE"

run_compare_task() {
    filepath="$1"
    filename=$(basename "$filepath")
    case_id="${filename%_cbct.nii.gz}"
    
    mar_path="${MAR_DIR}/${filename}"
    if [ ! -f "$mar_path" ]; then
        return
    fi

    echo "Visualizing: $case_id"
    
    # [CPU 優化] 限制執行緒數
    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python view_before_after.py \
        --raw_root "$RAW_DIR" \
        --mar_root "$MAR_DIR" \
        --out_root "$OUT_BASE" \
        --case_id "$case_id" \
        --vmin "$VMIN" \
        --vmax "$VMAX" \
        --every "$EVERY"
}

export -f run_compare_task
export RAW_DIR MAR_DIR OUT_BASE VMIN VMAX EVERY

echo "=== Before/After Comparison ==="
echo "Total Cores/Workers: $N_WORKERS"
echo "Output: $OUT_BASE"

find "$RAW_DIR" -name "*_cbct.nii.gz" -print0 | xargs -0 -P "$N_WORKERS" -I {} bash -c 'run_compare_task "$@"' _ {}

echo "=== Complete ==="