import pytest
import numpy as np
import cv2
from modules.ai_analyzer import AIAnalyzer

@pytest.fixture
def analyzer():
    return AIAnalyzer()

def test_analyzer_initialization(analyzer):
    assert analyzer.model_name == "efficientnet-b0"
    assert analyzer.model is not None

def test_detect_structures(analyzer):
    # Create a dummy image (224x224x3)
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    # Add a "blob" to trigger detection
    cv2.circle(img, (112, 112), 50, (255, 255, 255), -1)
    
    findings = analyzer.detect_structures(img)
    assert isinstance(findings, dict)
    assert 'brain' in findings
    assert 'skull' in findings['brain']
    assert 'confidence' in findings['brain']['skull']

def test_measure_biometry(analyzer):
    # Create a dummy head-like ellipse
    img = np.zeros((512, 512, 1), dtype=np.uint8)
    cv2.ellipse(img, (256, 256), (100, 80), 0, 0, 360, 255, -1)
    
    measurements = analyzer.measure_biometry(img)
    assert 'BPD' in measurements
    assert 'HC' in measurements
    assert measurements['BPD']['value'] > 0
    assert measurements['HC']['value'] > 0
    assert measurements['BPD']['method'] == 'cv_ellipse'

def test_assess_image_quality(analyzer):
    # Good quality image
    img_good = np.random.randint(0, 255, (512, 512, 1), dtype=np.uint8)
    quality_good = analyzer.assess_image_quality(img_good)
    
    # Poor quality image (blur)
    img_poor = np.zeros((512, 512, 1), dtype=np.uint8)
    quality_poor = analyzer.assess_image_quality(img_poor)
    
    assert isinstance(quality_good, str)
    assert quality_poor == 'poor'

def test_gestational_age_estimate(analyzer):
    biometry = {
        'BPD': {'value': 48.0},
        'FL': {'value': 32.0}
    }
    ga = analyzer.estimate_gestational_age(biometry)
    assert ga['weeks'] == 20
    assert ga['days'] >= 0
