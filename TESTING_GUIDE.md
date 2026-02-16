# 🧪 RadVerify Testing Guide

Since you have already downloaded and organized your dataset, you have everything you need to test the system!

## 1. Where to find Test Images
Use the images inside the **`test`** folder. These were not used during training, so they are the best for checking AI accuracy.

Path: `c:\Users\abinr\RadVerify\data\Data\test\`
- **`normal/`**: Use these for healthy scan tests.
- **`benign/`**: Use these for scans with minor findings.
- **`malignant/`**: Use these for scans with significant findings.

---

## 2. Sample Report "Cheat Sheet"
To test the **Mismatch Detection**, paste these sample reports into the dashboard when you upload an image.

### Case A: Normal Verification (Success)
*Use with an image from `data/Data/test/normal/`*
```text
PREGNANCY ULTRASOUND REPORT
Patient ID: TEST-001
The fetus is in stable condition.
Structural analysis shows normal development.
No abnormalities detected in the scanned view.
Final Impression: Normal pregnancy ultrasound.
```

### Case B: Mismatch Test (Forced Error)
*Use with an image from `data/Data/test/malignant/`* (This will trigger a mismatch because the report says "Normal" but the AI sees "Malignant")
```text
PREGNANCY ULTRASOUND REPORT
Patient ID: TEST-ERR
Scan looks completely normal.
No masses or abnormalities observed.
Conclusion: Normal scan.
```

### Case C: Structured Biometry Test
*Use with any clear image*
```text
ULTRASOUND FINDINGS
BPD: 47.0 mm
HC: 175.0 mm
AC: 151.0 mm
FL: 31.0 mm
All measurements within normal range for 20 weeks.
```

---

## 3. How to Run the Test
1. Make sure the app is running: `.venv_ml\Scripts\python.exe -m streamlit run app.py`
2. Open **[http://localhost:8501](http://localhost:8501)**
3. **Upload an image** from one of the `test/` subfolders.
4. **Paste a report** from the cheat sheet above.
5. Click **"Run Full Verification"**.
6. Check the **"AI Findings"** and **"Comparison Report"** tabs!
