"""
Quick test to verify RadVerify backend works
"""

print("Testing RadVerify Backend...")
print()

# Test 1: Import modules
print("1. Testing imports...")
try:
    from modules.input_handler import InputHandler
    from modules.image_enhancer import ImageEnhancer
    from modules.ai_analyzer import AIAnalyzer
    from modules.report_generator import ReportGenerator
    from modules.nlp_parser import NLPParser
    from modules.verification_engine import VerificationEngine
    from pipeline import RadVerifyPipeline
    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)

# Test 2: Create mock data
print("\n2. Creating mock data...")
import numpy as np
from PIL import Image
import io

# Mock image
img_array = np.random.randint(50, 200, (600, 800, 3), dtype=np.uint8)
pil_img = Image.fromarray(img_array)
img_bytes = io.BytesIO()
pil_img.save(img_bytes, format='PNG')
img_bytes.seek(0)
img_bytes.name = 'test.png'

# Mock report
report_text = """
ULTRASOUND REPORT
BPD: 47.0 mm
HC: 175.0 mm
FL: 31.5 mm
Brain: Normal
Heart: Four-chamber view normal
"""

print("✅ Mock data created")

# Test 3: Test pipeline
print("\n3. Testing complete pipeline...")
try:
    pipeline = RadVerifyPipeline()
    results = pipeline.process(img_bytes, report_text, enhance_image=True)
    
    if results['success']:
        print("✅ Pipeline executed successfully!")
        print(f"\n   Agreement Rate: {results['verification_results']['agreement_rate'] * 100:.1f}%")
        print(f"   Risk Level: {results['verification_results']['risk_level']}")
        print(f"   Stage: {results['stage']}")
    else:
        print(f"❌ Pipeline failed: {results['errors']}")
        
except Exception as e:
    print(f"❌ Pipeline test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("TEST COMPLETE!")
print("="*50)
