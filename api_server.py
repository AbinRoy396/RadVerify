"""FastAPI wrapper exposing the RadVerify verification pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
from importlib import metadata

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends, Security
from fastapi.security.api_key import APIKeyHeader, APIKey
from fastapi.middleware.cors import CORSMiddleware
import io
import os
import time
from pathlib import Path

import numpy as np
from PIL import Image

from pipeline import RadVerifyPipeline
from modules.database import CaseDatabase

# API Key Security
API_KEY = "radverify_secret_key"  # In production, use environment variables
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def get_api_key(header_key: str = Security(api_key_header)):
    if header_key == API_KEY:
        return header_key
    raise HTTPException(status_code=403, detail="Could not validate API Key")


# Initialization
app = FastAPI(
    title="RadVerify API", 
    description="Professional API for Pregnancy Ultrasound Verification",
    version="1.2.0"
)

# Initialize Core Services
pipeline = RadVerifyPipeline()
db = CaseDatabase()
STARTUP_STATUS: Dict[str, Any] = {}


def _get_version(pkg_name: str) -> str:
    try:
        return metadata.version(pkg_name)
    except Exception:
        return "unknown"


def _check_optional_dependencies() -> Dict[str, Any]:
    status: Dict[str, Any] = {
        "tensorflow": False,
        "spacy": False,
        "spacy_model": False,
        "realesrgan": False,
    }

    try:
        import tensorflow  # noqa: F401
        status["tensorflow"] = True
    except Exception:
        pass

    try:
        import spacy  # noqa: F401
        status["spacy"] = True
        try:
            import spacy as _spacy
            _spacy.load("en_core_web_sm")
            status["spacy_model"] = True
        except Exception:
            pass
    except Exception:
        pass

    try:
        import realesrgan  # noqa: F401
        import basicsr  # noqa: F401
        status["realesrgan"] = True
    except Exception:
        pass

    return status


def _save_enhanced_image(image: np.ndarray, output_dir: str = "logs") -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    out_path = Path(output_dir) / f"enhanced_{ts}.png"
    img = image
    if img.dtype != np.uint8:
        img = np.clip(img, 0, 255)
        if img.max() <= 1.0:
            img = (img * 255).astype(np.uint8)
        else:
            img = img.astype(np.uint8)
    Image.fromarray(img).save(out_path)
    return str(out_path)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_check() -> None:
    optional = _check_optional_dependencies()
    STARTUP_STATUS.update(
        {
            "optional": optional,
            "versions": {
                "fastapi": _get_version("fastapi"),
                "uvicorn": _get_version("uvicorn"),
                "numpy": _get_version("numpy"),
                "opencv-python": _get_version("opencv-python"),
                "tensorflow": _get_version("tensorflow"),
                "spacy": _get_version("spacy"),
                "pydicom": _get_version("pydicom"),
            },
        }
    )

    missing = [k for k, v in optional.items() if not v]
    if missing:
        print(f"WARN: Optional dependencies missing: {', '.join(missing)}")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.get("/health/details")
def health_details() -> Dict[str, Any]:
    return {
        "status": "ok",
        "optional": STARTUP_STATUS.get("optional", _check_optional_dependencies()),
        "versions": STARTUP_STATUS.get("versions", {}),
    }

@app.post("/verify", response_model=Dict[str, Any])
async def verify_report(
    scan: UploadFile = File(..., description="Single medical scan (jpg/png/bmp/tiff/dcm)"),
    report: str = Form(..., description="Radiology report text"),
    enhance: bool = Form(True, description="Apply AI enhancement (slower, may improve quality)"),
    api_key: APIKey = Depends(get_api_key)
) -> Dict[str, Any]:
    """Runs the full 9-stage verification pipeline on a scan and report."""
    data = await scan.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded scan is empty.")

    # Convert to file-like object for the pipeline
    img_io = io.BytesIO(data)
    img_io.name = scan.filename or "uploaded_scan.png"

    try:
        results = pipeline.process(
            image_file=img_io,
            doctor_report_text=report,
            enhance_image=enhance
        )
        
        if not results['success']:
            if results.get("stage") == "input_validation":
                raise HTTPException(
                    status_code=400,
                    detail={
                        "stage": results.get("stage"),
                        "errors": results.get("errors", []),
                    },
                )
            raise HTTPException(status_code=500, detail=f"Pipeline failed at stage: {results['stage']}")

        # Save enhanced image and remove large arrays from response
        enhanced = results.get("enhanced_image")
        enhanced_path = None
        if enhanced is not None:
            enhanced_path = _save_enhanced_image(enhanced)
            results["enhanced_image_path"] = enhanced_path

        # Save to database
        case_data = {
            'patient_id': 'API_USER_' + str(int(time.time())),
            'ai_findings': results.get('ai_findings', {}),
            'doctor_findings': results.get('doctor_findings', {}),
            'verification_results': results.get('verification_results', {}),
            'comparison_report': results.get('comparison_report_text', ''),
            'medical_narrative': results.get('medical_narrative', ''),
            'image_path': enhanced_path or f"api_upload_{int(time.time())}.png"
        }
        case_id = db.save_case(case_data)
        results['case_id'] = case_id
        if 'original_image' in results:
            del results['original_image']
        if 'enhanced_image' in results:
            del results['enhanced_image']
        
        return results

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/history", response_model=List[Dict[str, Any]])
async def get_history(limit: int = 10, api_key: APIKey = Depends(get_api_key)):
    """Retrieve recent verification cases."""
    return db.get_recent_cases(limit=limit)

@app.get("/case/{case_id}", response_model=Dict[str, Any])
async def get_case_details(case_id: int, api_key: APIKey = Depends(get_api_key)):
    """Retrieve detailed results for a specific case."""
    case = db.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
