import io

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image
import pytest

from api_server import app


@pytest.mark.slow
def test_verify_integration_success():
    client = TestClient(app)

    img = Image.new('RGB', (120, 120), color='gray')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    files = {"scan": ("test.png", img_byte_arr, "image/png")}
    data = {
        "report": "BPD 47mm, HC 175mm. Brain normal. Heart normal. Abdomen normal.",
        "enhance": "false",
    }
    headers = {"X-API-Key": "radverify_secret_key"}

    response = client.post("/verify", files=files, data=data, headers=headers)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload.get("success") is True
    assert "verification_results" in payload
