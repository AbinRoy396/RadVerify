# Full-Structure Labeling Workflow

This workflow gets you from raw images to a structure-labeled dataset that matches `AIAnalyzer.FETAL_STRUCTURES`.

## 1. Folder Template (Already Created)
Location: `data/structure_dataset/`

Structure:
- `train/` (per-class folders)
- `validation/` (per-class folders)
- `test/` (per-class folders)

Class folders are named `{category}_{structure}` (e.g., `brain_skull`, `heart_four_chamber_view`).

## 2. Decide Your Labeling Source
Pick one:
- **Existing labeled dataset**: Map its labels to these folder names.
- **Manual labeling**: Use a tool (Label Studio / CVAT) to assign each image to a class.
- **Semi-automatic**: Train a small model on a labeled subset, auto-label the rest, then review.

## 3. Label Mapping File
Use `data/structure_dataset/labels_map_template.csv`.
Format:
```
image_path,label
path/to/image1.png,brain_skull
```

You can generate this CSV from your labeling tool and then sort images into folders.

## 4. Sorting Images Into Folders
Once you have a CSV, place files into:
- `data/structure_dataset/train/<label>/`
- `data/structure_dataset/validation/<label>/`
- `data/structure_dataset/test/<label>/`

Recommended split: 80/10/10.

## 5. Training
Point `train_model.py` at this dataset by updating:
```
DATASET_PATH = "data/structure_dataset"
```
Then run:
```
.\.venv_ml\Scripts\python.exe train_model.py
```
This will output:
- `models/best_model.h5`
- `models/labels.json`

## 6. Verify Mapping
After training, confirm:
```
.\.venv_ml\Scripts\python.exe -c "import json; print(len(json.load(open('models/labels.json'))))"
```
Should match the number of structure folders (22).

## Notes
- If you add or remove structures, regenerate the dataset template.
- Keep label names consistent across folders, CSV, and `labels.json`.
