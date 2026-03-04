import importlib
import io
import json
import os
import time
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
import pytest


def _client():
    os.environ["RADVERIFY_API_KEY"] = "hardening_test_key"
    api_server = importlib.import_module("api_server")
    api_server = importlib.reload(api_server)
    return TestClient(api_server.app)


@pytest.mark.slow
def test_golden_verify_shape():
    client = _client()
    img = Image.new("RGB", (128, 128), color="gray")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    response = client.post(
        "/verify",
        files={"scan": ("golden.png", buf, "image/png")},
        data={"report": "Sample fetal ultrasound report text for pipeline verification. Normal anatomy reported.", "enhance": "true"},
        headers={"X-API-Key": "hardening_test_key"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    expected = json.loads(Path("tests/golden_verify_expected.json").read_text(encoding="utf-8"))
    assert payload.get("success") == expected["expected_success"]
    assert payload.get("stage") == expected["expected_stage"]
    for key in expected["required_top_keys"]:
        assert key in payload


@pytest.mark.slow
def test_verify_async_flow():
    client = _client()
    img = Image.new("RGB", (120, 120), color="gray")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    start = client.post(
        "/verify-async",
        files={"scan": ("async.png", buf, "image/png")},
        data={"report": "Sample fetal ultrasound report text for pipeline verification. Normal anatomy reported.", "enhance": "false"},
        headers={"X-API-Key": "hardening_test_key"},
    )
    assert start.status_code == 200, start.text
    job_id = start.json()["job_id"]
    for _ in range(300):
        status = client.get(f"/verify-async/{job_id}", headers={"X-API-Key": "hardening_test_key"})
        assert status.status_code == 200
        state = status.json()["status"]
        if state in {"completed", "failed"}:
            break
        time.sleep(0.1)
    final = client.get(f"/verify-async/{job_id}", headers={"X-API-Key": "hardening_test_key"}).json()
    assert final["status"] in {"running", "completed", "failed"}
    if final["status"] == "completed":
        assert final["result"]["success"] is True


def test_rejects_invalid_file_signature():
    client = _client()
    bad_bytes = io.BytesIO(b"not-a-real-image")
    response = client.post(
        "/verify",
        files={"scan": ("bad.png", bad_bytes, "image/png")},
        data={"report": "Sample fetal ultrasound report text for pipeline verification. Normal anatomy reported.", "enhance": "false"},
        headers={"X-API-Key": "hardening_test_key"},
    )
    assert response.status_code == 415
    detail = response.json()["detail"]
    assert detail["code"] == "unsupported_file_signature"
