"""FastAPI wrapper exposing the RadVerify verification pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from radverify import run_verification


@dataclass
class _InMemoryUpload:
    """Bridges FastAPI uploads to the pipeline's expected interface."""

    name: str
    _buffer: bytes

    def getvalue(self) -> bytes:
        return self._buffer


app = FastAPI(title="RadVerify API", version="0.1.0")
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


@app.post("/verify")
async def verify_report(
    scan: UploadFile = File(..., description="Single medical scan (jpg/png)"),
    report: str = Form(..., description="Radiology report text"),
) -> Dict[str, Any]:
    data = await scan.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded scan is empty.")

    upload = _InMemoryUpload(name=scan.filename or "scan", _buffer=data)

    try:
        bundle, notes = run_verification(upload, report)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail="Verification failed.") from exc

    response = {
        "comparison": bundle.comparison.__dict__,
        "explanation": bundle.explanation,
        "ai_finding": bundle.ai_finding.__dict__,
        "ai_report_snippet": bundle.ai_report_snippet.__dict__,
        "report_findings": bundle.report_findings.__dict__,
        "processing_notes": notes,
    }
    return response


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
