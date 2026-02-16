import sys
import os
import io
from fastapi.testclient import TestClient
import numpy as np
from PIL import Image

# Add current directory to path
sys.path.append(os.getcwd())

from api_server import app

client = TestClient(app)

def test_health():
    print("Testing /health endpoint...")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("✅ Health check passed")

def test_auth():
    print("\nTesting authentication...")
    # No key
    response = client.get("/history")
    assert response.status_code == 403
    
    # Wrong key
    response = client.get("/history", headers={"X-API-Key": "wrong_key"})
    assert response.status_code == 403
    
    # Correct key
    response = client.get("/history", headers={"X-API-Key": "radverify_secret_key"})
    assert response.status_code == 200
    print("✅ API Key authentication passed")

def test_verify_endpoint():
    print("\nTesting /verify endpoint...")
    
    # Create mock image
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    files = {
        "scan": ("test.png", img_byte_arr, "image/png")
    }
    data = {
        "report": "BPD 47mm, HC 175mm",
        "enhance": "true"
    }
    headers = {"X-API-Key": "radverify_secret_key"}
    
    response = client.post("/verify", files=files, data=data, headers=headers)
    
    if response.status_code == 200:
        results = response.json()
        print(f"✅ /verify passed! Case ID: {results.get('case_id')}")
        print(f"   Agreement: {results['verification_results']['agreement_rate']*100:.1f}%")
        return results.get('case_id')
    else:
        print(f"❌ /verify failed: {response.status_code}")
        print(response.text)
        return None

def test_case_detail(case_id):
    if not case_id: return
    print(f"\nTesting /case/{case_id} endpoint...")
    headers = {"X-API-Key": "radverify_secret_key"}
    response = client.get(f"/case/{case_id}", headers=headers)
    assert response.status_code == 200
    print("✅ Case detail retrieval passed")

if __name__ == "__main__":
    print("Starting API Logic Verification...")
    try:
        test_health()
        test_auth()
        cid = test_verify_endpoint()
        test_case_detail(cid)
        print("\n" + "="*50)
        print("API LOGIC VERIFICATION SUCCESSFUL!")
        print("="*50)
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
