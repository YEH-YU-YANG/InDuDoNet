# CBCT 處理與視覺化工具

此專案提供一系列 Python 腳本，用於處理和視覺化錐束電腦斷層掃描 (CBCT) 資料，重點在於金屬偽影減少 (MAR)。

## 專案結構

專案組織如下：

- `cbct/`：包含 CBCT 資料處理和視覺化核心功能的 Python 模組。
- `scripts/`：主要命令列介面 (CLI) 入口點。
- `tests/`：單元測試 (尚未實作)。

## 安裝

需要以下函式庫：

- `pydicom`
- `numpy`
- `nibabel`
- `scipy`
- `Pillow`
- `imageio`

您可以使用 pip 安裝它們：

```bash
pip install pydicom numpy nibabel scipy Pillow imageio
```

## 使用方式

此專案的主要入口點是 `scripts/main.py`。此腳本提供 CLI 功能，用於將 DICOM 檔案轉換為 NIfTI、視覺化 MAR 結果以及比較處理前後的影像。

### 將 DICOM 轉換為 NIfTI

要將一系列病患的 CBCT DICOM 影像轉換為 NIfTI 格式，請使用 `convert` 命令：

```bash
python scripts/main.py convert <patient_id_1> <patient_id_2> ... \
    --base_dir <base_data_dir> \
    --output_dir <output_dir> \
    --spacing <target_spacing>
```

### 視覺化 MAR 結果

要將單個經過 MAR 處理的 NIfTI 體積的軸向切片保存為單獨的 PNG 檔案，請使用 `visualize` 命令：

```bash
python scripts/main.py visualize \
    --mar <mar_nifti_file> \
    --out_dir <output_dir> \
    --target <target_size> \
    --vmin <window_vmin> \
    --vmax <window_vmax> \
    --start <start_slice> \
    --end <end_slice> \
    --every <every_n_slices> \
    --no_hu
```

### 比較 MAR 處理前後

要為每個切片建立並排比較 PNG，顯示原始影像、MAR 處理後的影像和差異圖，請使用 `compare` 命令：

```bash
python scripts/main.py compare \
    --raw_root <raw_nifti_root> \
    --mar_root <mar_nifti_root> \
    --out_root <output_root> \
    --case_id <case_id> \
    --vmin <window_vmin> \
    --vmax <window_vmax> \
    --start <start_slice> \
    --end <end_slice> \
    --every <every_n_slices> \
    --rot90 <rot90> \
    --flipud \
    --fliplr
```

### 檢查 DICOM 檔案

要掃描 DICOM 檔案目錄，按序列分組並列印其中繼資料的詳細摘要，請使用 `inspect` 命令：

```bash
python scripts/main.py inspect \
    --root <dicom_root> \
    --pattern <dicom_dir_pattern> \
    --ext <dicom_file_extension> \
    --pixel_sample <num_pixels_to_sample>
```

### 調試遮罩閾值

要視覺化不同 HU 閾值對 NIfTI 體積特定切片的影響，請使用 `debug` 命令：

```bash
python scripts/main.py debug \
    --nii_path <nifti_file> \
    --out_dir <output_dir> \
    --slice_k <slice_to_visualize> \
    --thrs <thresholds_to_test>
```
