from modules.verification_engine import VerificationEngine


def test_measurement_discrepancies_are_counted():
    engine = VerificationEngine()
    ai_findings = {
        "biometry": {
            "BPD": {"value": 45.0},
            "HC": {"value": 170.0},
            "AC": {"value": 150.0},
            "FL": {"value": 30.0},
        },
        "structures_detected": {},
    }
    doctor_findings = {
        "measurements": {
            "BPD": {"mentioned": False, "value": None},
            "HC": {"mentioned": False, "value": None},
            "AC": {"mentioned": False, "value": None},
            "FL": {"mentioned": False, "value": None},
        },
        "structures": {},
    }

    result = engine.verify(ai_findings, doctor_findings)
    assert result["discrepancy_counts"]["omissions"] == 4
    assert result["discrepancy_counts"]["mismatches"] == 0
    assert result["discrepancy_counts"]["overstatements"] == 0
