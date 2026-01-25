# RadVerify - AI-Based Radiology Report Verification System

An AI-powered system for verifying pregnancy ultrasound reports by comparing AI-generated findings with radiologist reports to detect mismatches, omissions, and inconsistencies.

## 🎯 Overview

RadVerify is a **verification and quality assurance tool** designed to:
- Enhance ultrasound scan quality using AI super-resolution
- Generate comprehensive AI-based pregnancy ultrasound reports
- Parse and analyze doctor's written reports
- Compare findings to identify discrepancies
- Provide detailed comparison reports with recommendations

**⚠️ IMPORTANT**: This is NOT a diagnostic tool. It assists in quality assurance and does not replace medical professionals.

## 🏗️ System Architecture

```
Input (Scan + Doctor's Report)
    ↓
Image Enhancement (ESRGAN/OpenCV)
    ↓
AI Analysis (EfficientNet + OpenCV)
    ↓
AI Report Generation (Jinja2 Templates)
    ↓
NLP Report Parsing (spaCy)
    ↓
Verification Engine (Comparison Logic)
    ↓
Comparison Report (Side-by-Side Analysis)
    ↓
Final Results (Text/JSON/Markdown)
```

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or navigate to the project directory**:
```bash
cd RadVerify
```

2. **Create virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
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

### Basic Usage

```python
from pipeline import verify_report
from PIL import Image

# Load ultrasound image
image_file = open('path/to/ultrasound.jpg', 'rb')

# Doctor's report text
doctor_report = """
PREGNANCY ULTRASOUND REPORT
Gestational Age: 20 weeks 2 days
BPD: 47.0 mm
HC: 175.0 mm
FL: 31.5 mm
Brain: Normal
Heart: Four-chamber view normal
...
"""

# Run verification
results = verify_report(
    image_file=image_file,
    doctor_report_text=doctor_report,
    enhance_image=True
)

# Check results
if results['success']:
    print(results['comparison_report_text'])
    print(f"\nAgreement Rate: {results['verification_results']['agreement_rate'] * 100:.1f}%")
else:
    print("Errors:", results['errors'])
```

### Using the Pipeline Class

```python
from pipeline import RadVerifyPipeline

# Initialize pipeline
pipeline = RadVerifyPipeline(config_path='config/config.yaml')

# Process inputs
results = pipeline.process(
    image_file=image_file,
    doctor_report_text=doctor_report,
    enhance_image=True
)

# Access different components
ai_report = results['ai_report_text']
comparison = results['comparison_report_text']
verification = results['verification_results']
```

## 📋 Modules

### Backend Modules

| Module | Purpose |
|--------|---------|
| `input_handler.py` | Validates and loads image/report inputs |
| `image_enhancer.py` | AI-based image super-resolution (ESRGAN/OpenCV) |
| `image_processor.py` | Image preprocessing for AI models |
| `ai_analyzer.py` | Fetal structure detection and biometry |
| `report_generator.py` | AI report generation from findings |
| `nlp_parser.py` | Doctor's report text parsing |
| `verification_engine.py` | Comparison logic and verification |
| `comparison_report.py` | Final comparison report generation |
| `result_generator.py` | Results formatting and explanations |

### Main Pipeline

- `pipeline.py`: Orchestrates the complete 9-stage workflow

## ⚙️ Configuration

Edit `config/config.yaml` to customize:

- Image processing settings (size, enhancement method)
- AI model parameters (confidence thresholds)
- NLP keywords (negation, uncertainty)
- Verification tolerances (measurement differences)
- Report formatting options

## 📊 Output Formats

### 1. AI-Generated Report
Comprehensive pregnancy ultrasound report with:
- Fetal biometry (BPD, HC, AC, FL)
- Anatomical structures (brain, heart, spine, organs, limbs)
- Gestational age estimation
- Image quality assessment

### 2. Comparison Report
Side-by-side analysis showing:
- ✅ Agreements (matching findings)
- ⚠️ Omissions (AI detected, doctor didn't mention)
- ❌ Mismatches (contradictory findings)
- ⚠️ Overstatements (doctor mentioned, AI didn't detect)
- Statistical summary and risk level

### 3. Verification Results
- Agreement rate (0-100%)
- Risk level (low/medium/high)
- Detailed discrepancy counts
- Recommendations

## 🔬 Technical Details

### AI Models
- **Structure Detection**: EfficientNet-B0 (placeholder - uses rule-based fallback)
- **Image Enhancement**: OpenCV-based super-resolution with CLAHE
- **Biometry**: Computer vision measurements using OpenCV
- **NLP**: spaCy for text parsing and analysis

### Measurement Tolerances
- BPD: ±2.0 mm
- HC: ±5.0 mm
- AC: ±5.0 mm
- FL: ±2.0 mm

## 🚧 Current Limitations

1. **AI Models**: Using placeholder/rule-based implementations. Production requires:
   - Pre-trained medical imaging models
   - Validated biometric measurement algorithms
   - Real-ESRGAN for image enhancement

2. **Scope**: Focused on 20-week pregnancy ultrasound anatomy scans

3. **Data**: No persistent storage - all processing is in-memory

4. **Validation**: Requires clinical validation before medical use

## 🔮 Future Enhancements

- Real pre-trained medical imaging models
- Multi-scan and longitudinal analysis
- LLM-based report generation
- Multilingual support
- Database integration for audit logs
- REST API for integration

## ⚖️ Medical Disclaimer

**THIS SOFTWARE IS FOR RESEARCH AND EDUCATIONAL PURPOSES ONLY**

- Not FDA approved or clinically validated
- Does not provide medical diagnosis or advice
- Not a replacement for qualified medical professionals
- All findings must be reviewed by licensed radiologists/obstetricians
- No patient data is stored or transmitted

## 📄 License

[Add your license here]

## 👥 Contributors

RadVerify Team

## 📞 Support

For issues or questions, please contact [your contact information]

---

**Version**: 0.1.0  
**Last Updated**: 2026-01-25
