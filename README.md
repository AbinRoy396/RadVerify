# RadVerify - AI-Based Radiology Report Verification System

An AI-powered system for verifying pregnancy ultrasound reports by comparing AI-generated findings with radiologist reports to detect mismatches, omissions, and inconsistencies.

## 🎯 Overview

RadVerify is a **verification and quality assurance tool** designed to:
- Be a "Second Pair of Eyes" for radiologists
- Generate comprehensive AI-based pregnancy ultrasound reports
- Parse and analyze doctor's written reports
- Compare findings to identify discrepancies
- Provide detailed comparison reports with recommendations

**⚠️ IMPORTANT**: This is NOT a diagnostic tool. It assists in quality assurance and does not replace medical professionals.

## 🌟 Key Features

### 🧠 Advanced AI Core
- **Fetal Structure Detection**: Fine-tuned **EfficientNet-B0** model trained on ~2,000 fetal ultrasound images (75% accuracy).
- **Semantic Segmentation**: Pixel-level masking for Head, Abdomen, and Femur.
- **Biometry Measurement**: Computer Vision algorithms for BPD, HC, AC, and FL measurements.
- **Visual Explainability**: Color-coded overlays showing exactly what the AI detected.

### 📝 Intelligent Reporting
- **LLM Narrative Synthesis**: Generates natural language medical reports using **Google Gemini** (or smart template fallback).
- **Auto-Calibration**: Automatically detects scale bars to calculate pixel-to-mm ratio.
- **DICOM Support**: Native support for medical imaging files (`.dcm`) with proper windowing.

### 🛡️ Clinical Workflow
- **Case History Database**: SQLite-based storage for all verification cases.
- **Discrepancy Detection**: Flags mismatches between AI findings and doctor's report.
- **Interactive Dashboard**: Streamlit-based UI for real-time analysis and review.

## 🏗️ System Architecture

```mermaid
graph TD
    A[Input: Scan + Report] --> B[Image Enhancement (ESRGAN)]
    B --> C{AI Core}
    C -->|Classification| D[EfficientNet-B0]
    C -->|Segmentation| E[U-Net / CV Masks]
    C -->|Measurement| F[Biometry Algorithms]
    
    A --> G[NLP Parser (spaCy)]
    
    D & E & F --> H[AI Findings JSON]
    H --> I[LLM Report Synthesizer]
    
    G & H --> J[Verification Engine]
    J --> K[Comparison Report]
    K --> L[Streamlit Dashboard]
    L --> M[SQLite Database]
```

## 📦 Installation

### Prerequisites
- Python 3.10 - 3.12 (TensorFlow compatibility)
- pip package manager

### Setup

1. **Clone the repository**:
```bash
git clone https://github.com/AbinRoy396/RadVerify.git
cd RadVerify
```

2. **Create virtual environment** (Recommended for TensorFlow):
```bash
python -m venv .venv_ml
source .venv_ml/bin/activate  # On Windows: .venv_ml\Scripts\activate
```

3. **Install core dependencies**:
```bash
.\.venv_ml\Scripts\python.exe -m pip install -r requirements.txt
```

4. **Install optional ML dependencies** (recommended for full capability):
```bash
.\.venv_ml\Scripts\python.exe -m pip install -r requirements-ml.txt
```

5. **Download NLP models**:
```bash
.\.venv_ml\Scripts\python.exe -m pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
.\.venv_ml\Scripts\python.exe -m nltk.downloader punkt stopwords
```

### Optional: Real-ESRGAN Enhancement

If you want AI super-resolution (instead of OpenCV fallback), install the ML extras:
```bash
.\.venv_ml\Scripts\python.exe -m pip install -r requirements-ml.txt
```
This may take a while because it can pull large dependencies (e.g., PyTorch).

## 🚀 Usage

### Run the Dashboard

```bash
# Start the Dashboard
streamlit run app.py

# Start the API Server
uvicorn api_server:app --reload
```

## 🐳 Docker Deployment

The entire system (Dashboard + API) can be deployed using Docker:

```bash
# Build and start all services
docker-compose up --build
```
- **Dashboard**: http://localhost:8501
- **API Server**: http://localhost:8000

## 📡 REST API Usage

RadVerify provides a professional REST API for integration.

**Auth Header**: `X-API-Key: radverify_secret_key`

### 1. Verify Report
`POST /verify`
- **scan**: Image file (multipart/form-data). Supported: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.dcm`
- **report**: Findings text (string)
- **enhance**: Boolean (optional, default true). If `true`, runs enhancement (slower, may improve quality).

```bash
curl -X POST "http://localhost:8000/verify" \
     -H "X-API-Key: radverify_secret_key" \
     -F "scan=@ultrasound.jpg" \
     -F "report=BPD 47mm, HC 175mm"
```

### 2. View History
`GET /history?limit=10`
```bash
curl -H "X-API-Key: radverify_secret_key" "http://localhost:8000/history"
```

### 3. Get Case Details
`GET /case/{id}`
```bash
curl -H "X-API-Key: radverify_secret_key" "http://localhost:8000/case/1"
```

## 🔬 Technical Details

### AI Models & Training
- **Backbone**: EfficientNet-B0 (Pre-trained on ImageNet, Fine-tuned on Medical Data)
- **Dataset**: Kaggle Ultrasound Fetus Dataset (1,926 images)
- **Classes**: Benign, Malignant, Normal
- **Training**: 20 Epochs, Adam Optimizer, Categorical Crossentropy

### Measurement Tolerances
- BPD: ±2.0 mm
- HC: ±5.0 mm
- AC: ±5.0 mm
- FL: ±2.0 mm

## 🔮 Roadmap
- [x] **Phase 7**: Production Deployment (Docker, REST API Ready)
- [ ] **Phase 8**: Clinical Validation (Large-scale datasets)
- [ ] **Phase 9**: Advanced Analytics (Longitudinal Trends)

## ⚖️ Medical Disclaimer

**THIS SOFTWARE IS FOR RESEARCH AND EDUCATIONAL PURPOSES ONLY**
- Not FDA approved or clinically validated
- Not a replacement for qualified medical professionals
- No patient data is stored or transmitted outside the local machine

## 👥 Contributors
**Abin Roy** - Lead Developer

---
**Version**: 1.2.0 - Advanced AI Model  
**Last Updated**: Feb 2026
