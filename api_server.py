"""FastAPI wrapper exposing the RadVerify verification pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends, Security
from fastapi.security.api_key import APIKeyHeader, APIKey
from fastapi.middleware.cors import CORSMiddleware
import io
import os
import time

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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/verify", response_model=Dict[str, Any])
async def verify_report(
    scan: UploadFile = File(..., description="Single medical scan (jpg/png)"),
    report: str = Form(..., description="Radiology report text"),
    enhance: bool = Form(True, description="Whether to apply AI enhancement"),
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
            raise HTTPException(status_code=500, detail=f"Pipeline failed at stage: {results['stage']}")

        # Save to database
        case_data = {
            'patient_id': 'API_USER_' + str(int(time.time())),
            'ai_findings': results.get('ai_findings', {}),
            'doctor_findings': results.get('doctor_findings', {}),
            'verification_results': results.get('verification_results', {}),
            'comparison_report': results.get('comparison_report_text', ''),
            'medical_narrative': results.get('medical_narrative', ''),
            'image_path': f"api_upload_{int(time.time())}.png"
        }
        case_id = db.save_case(case_data)
        results['case_id'] = case_id

        # Clean up response for API: Remove large image arrays
        if 'original_image' in results: del results['original_image']
        if 'enhanced_image' in results: del results['enhanced_image']
        
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
