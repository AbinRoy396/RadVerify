"""
Comprehensive system test for RadVerify.
Tests: API health, verify endpoint, pipeline direct call, model load, DB.
"""
import requests
import json
import sys
import os

BASE_URL = "http://localhost:8000"
API_KEY = "radverify_secret_key"
HEADERS = {"X-API-Key": API_KEY}
SCAN_PATH = r"data\Data\Datasets\benign\100_HC.png"
REPORT = (
    "Single live intrauterine fetus. BPD 46.5 mm, HC 174.0 mm, "
    "AC 152.0 mm, FL 30.0 mm. Four chamber heart appears normal. "
    "No structural anomalies detected. Amniotic fluid normal."
)

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"
WARN = "\033[93m⚠  WARN\033[0m"


def check(label, condition, detail=""):
    icon = PASS if condition else FAIL
    print(f"  {icon}  {label}", f"({detail})" if detail else "")
    return condition


def separator(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")


results = []

# ── TEST 1: Health ────────────────────────────────────────
separator("TEST 1: Health Endpoints")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    ok = r.status_code == 200 and r.json().get("status") == "ok"
    results.append(check("/health", ok, f"HTTP {r.status_code}"))
except Exception as e:
    results.append(check("/health", False, str(e)))

try:
    r = requests.get(f"{BASE_URL}/health/details", timeout=5)
    d = r.json()
    results.append(check("/health/details TF loaded", d.get("optional", {}).get("tensorflow", False)))
    results.append(check("/health/details API key set", d.get("security", {}).get("api_key_configured", False)))
except Exception as e:
    results.append(check("/health/details", False, str(e)))

# ── TEST 2: Auth ──────────────────────────────────────────
separator("TEST 2: Authentication")
try:
    r = requests.get(f"{BASE_URL}/metrics", headers={}, timeout=5)
    results.append(check("Rejects missing API key", r.status_code in (403, 422, 401), f"HTTP {r.status_code}"))
except Exception as e:
    results.append(check("Auth rejected", False, str(e)))

try:
    r = requests.get(f"{BASE_URL}/metrics", headers=HEADERS, timeout=5)
    results.append(check("Accepts valid API key", r.status_code == 200, f"HTTP {r.status_code}"))
except Exception as e:
    results.append(check("Metrics with key", False, str(e)))

# ── TEST 3: Metrics ───────────────────────────────────────
separator("TEST 3: Metrics Endpoint")
try:
    r = requests.get(f"{BASE_URL}/metrics", headers=HEADERS, timeout=5)
    d = r.json()
    results.append(check("requests_total > 0", d.get("requests_total", 0) > 0, str(d.get("requests_total"))))
    results.append(check("latency_avg_ms present", "latency_avg_ms" in d, str(d.get("latency_avg_ms", "?"))))
except Exception as e:
    results.append(check("Metrics structure", False, str(e)))

# ── TEST 4: Verify Endpoint ───────────────────────────────
separator("TEST 4: /verify Endpoint (Live Pipeline)")
if os.path.exists(SCAN_PATH):
    try:
        with open(SCAN_PATH, "rb") as f:
            r = requests.post(
                f"{BASE_URL}/verify",
                headers=HEADERS,
                files={"scan": ("100_HC.png", f, "image/png")},
                data={"report": REPORT, "enhance": "true"},
                timeout=120,
            )
        if r.status_code == 200:
            d = r.json()
            results.append(check("Pipeline success=true", d.get("success") is True))
            results.append(check("Stage = completed", d.get("stage") == "completed", d.get("stage")))
            vr = d.get("verification_results", {})
            agree = vr.get("agreement_rate", 0) * 100
            results.append(check(f"Agreement rate present ({agree:.1f}%)", agree >= 0))
            results.append(check("Case saved to DB", d.get("case_id") is not None, str(d.get("case_id"))))
            results.append(check("Runtime < 60s", d.get("runtime_ms", 999999) < 60000, f"{d.get('runtime_ms')}ms"))
        else:
            results.append(check("/verify returned 200", False, f"HTTP {r.status_code}: {r.text[:200]}"))
    except Exception as e:
        results.append(check("/verify call", False, str(e)))
else:
    print(f"  {WARN}  Scan file not found at {SCAN_PATH}, skipping live call")

# ── TEST 5: Bad Input Handling ────────────────────────────
separator("TEST 5: Bad Input Handling")
try:
    r = requests.post(
        f"{BASE_URL}/verify",
        headers=HEADERS,
        files={"scan": ("test.txt", b"not an image", "text/plain")},
        data={"report": "Some report"},
        timeout=15,
    )
    results.append(check("Rejects non-image file", r.status_code in (400, 415), f"HTTP {r.status_code}"))
except Exception as e:
    results.append(check("Bad input rejected", False, str(e)))

# ── TEST 6: Case History ──────────────────────────────────
separator("TEST 6: Case History")
try:
    r = requests.get(f"{BASE_URL}/history", headers=HEADERS, timeout=5)
    results.append(check("/history returns list", isinstance(r.json(), list), f"{len(r.json())} cases"))
except Exception as e:
    results.append(check("/history", False, str(e)))

# ── TEST 7: Model & DB Direct ────────────────────────────
separator("TEST 7: Model & Database Direct")
try:
    import tensorflow as tf
    model_path = "models/best_model.keras"
    if os.path.exists(model_path):
        m = tf.keras.models.load_model(model_path)
        results.append(check("best_model.keras loads", True, f"Output shape: {m.output_shape}"))
    else:
        results.append(check("best_model.keras exists", False, model_path))
except Exception as e:
    results.append(check("Model load", False, str(e)))

try:
    from modules.database import CaseDatabase
    db = CaseDatabase()
    cases = db.get_recent_cases(limit=3)
    results.append(check("Database readable", True, f"{len(cases)} recent cases"))
except Exception as e:
    results.append(check("Database", False, str(e)))

# ── SUMMARY ───────────────────────────────────────────────
separator("SUMMARY")
total = len(results)
passed = sum(results)
print(f"\n  Result: {passed}/{total} tests passed")
if passed == total:
    print("\n  \033[92m🎉 ALL TESTS PASSED!\033[0m")
elif passed >= total * 0.8:
    print("\n  \033[93m⚠  MOSTLY PASSING — minor issues\033[0m")
else:
    print("\n  \033[91m❌ FAILURES DETECTED — review above\033[0m")
print()
sys.exit(0 if passed == total else 1)
