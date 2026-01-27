# Testing Guide for RadVerify

## 📋 Prerequisites

Before running tests, you need to install dependencies:

```bash
# Install all required packages
pip install -r requirements.txt

# Download NLP models
python -m spacy download en_core_web_sm
python -m nltk.downloader punkt stopwords
```

## 🧪 Running Tests

### Option 1: Quick Test (Recommended First)
```bash
python quick_test.py
```

This runs a simple 3-step test:
1. Import all modules
2. Create mock data
3. Run complete pipeline

**Expected output**: Should show ✅ for each step and final agreement rate.

### Option 2: Comprehensive Test
```bash
python test_backend.py
```

This tests all 13 components:
1. Module imports
2. Mock image creation
3. Mock report creation
4. Input Handler
5. Image Enhancer
6. Image Processor
7. AI Analyzer
8. Report Generator
9. NLP Parser
10. Verification Engine
11. Comparison Report
12. Result Generator
13. Complete Pipeline

**Expected output**: Detailed test results for each module with ✅/❌ indicators.

## 🔍 Manual Testing

### Test Individual Modules

```python
# Test Image Enhancement
from modules.image_enhancer import ImageEnhancer
import numpy as np

img = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
enhancer = ImageEnhancer(method='opencv', scale_factor=2)
result = enhancer.process(img)
print(f"PSNR: {result['comparison_metrics']['psnr']}")
```

```python
# Test NLP Parser
from modules.nlp_parser import NLPParser

report = "BPD: 47.0 mm, HC: 175.0 mm, Brain: Normal"
parser = NLPParser()
parsed = parser.parse_report(report)
print(f"Measurements found: {parsed['measurements']}")
```

```python
# Test Complete Pipeline
from pipeline import RadVerifyPipeline
from PIL import Image
import io

# Create test image
img = Image.new('RGB', (800, 600), color='gray')
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes.seek(0)
img_bytes.name = 'test.png'

# Test report
report = "BPD: 47mm, Brain: Normal, Heart: Normal"

# Run pipeline
pipeline = RadVerifyPipeline()
results = pipeline.process(img_bytes, report, enhance_image=True)

if results['success']:
    print("✅ Success!")
    print(f"Agreement: {results['verification_results']['agreement_rate']}")
else:
    print(f"❌ Failed: {results['errors']}")
```

## 🐛 Troubleshooting

### Issue: Import errors
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: spaCy model not found
**Solution**: Download the model
```bash
python -m spacy download en_core_web_sm
```

### Issue: "Config file not found"
**Solution**: Make sure you're running from the RadVerify directory
```bash
cd C:\Users\abinr\RadVerify
python quick_test.py
```

### Issue: No output from tests
**Solution**: Run with explicit output
```bash
python -u quick_test.py
```

## ✅ Expected Test Results

### Quick Test Success:
```
Testing RadVerify Backend...

1. Testing imports...
✅ All imports successful

2. Creating mock data...
✅ Mock data created

3. Testing complete pipeline...
✅ Pipeline executed successfully!

   Agreement Rate: 85.0%
   Risk Level: low
   Stage: completed

==================================================
TEST COMPLETE!
==================================================
```

### Comprehensive Test Success:
All 13 tests should show ✅ with detailed metrics for each module.

## 📊 What Gets Tested

1. **Module Imports**: All 9 modules load correctly
2. **Input Validation**: Image and report validation works
3. **Image Enhancement**: Super-resolution and quality metrics
4. **Image Processing**: Preprocessing pipeline
5. **AI Analysis**: Structure detection and biometry
6. **Report Generation**: Template-based report creation
7. **NLP Parsing**: Text extraction and analysis
8. **Verification**: Comparison logic and agreement calculation
9. **Comparison Report**: Side-by-side report generation
10. **Results**: Final formatting and packaging
11. **End-to-End Pipeline**: Complete workflow from input to output

## 🎯 Success Criteria

- All module imports work ✅
- Mock data creation succeeds ✅
- Pipeline completes without errors ✅
- Agreement rate is calculated ✅
- Comparison report is generated ✅

## 📝 Notes

- Tests use **mock/simulated data** (not real medical images)
- AI models use **placeholder implementations** (rule-based fallbacks)
- For production, replace with real pre-trained models
- Tests verify **functionality**, not medical accuracy
