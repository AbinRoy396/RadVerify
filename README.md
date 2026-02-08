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

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Download NLP models**:
```bash
python -m spacy download en_core_web_sm
python -m nltk.downloader punkt stopwords
```

## 🚀 Usage

### Run the Dashboard

```bash
streamlit run app.py
```

### Run Model Training (Optional)

If you want to fine-tune the model on your own dataset:
1. Place data in `data/Data/train` (folders: benign, malignant, normal)
2. Run training script:
```bash
python train_model.py
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

## 🔮 Future Roadmap
- **Phase 7**: Production Deployment (Docker, REST API)
- **Phase 8**: Clinical Validation (Uncertainty Quantification)
- **Phase 9**: Advanced Analytics (Longitudinal Trends)

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
