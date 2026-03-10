"""FastAPI wrapper exposing the RadVerify verification pipeline."""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from collections import defaultdict, deque
from importlib import metadata
from pathlib import Path
from typing import Any, Deque, Dict, List

import numpy as np
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Security, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security.api_key import APIKey, APIKeyHeader
from PIL import Image

from modules.database import CaseDatabase
from pipeline import RadVerifyPipeline

try:
    import redis
except Exception:  # pragma: no cover - optional dependency
    redis = None

try:
    from prometheus_client import Counter, Gauge, Histogram
    from prometheus_client import REGISTRY as PROM_REGISTRY
except Exception:  # pragma: no cover - optional dependency
    Counter = None
    Gauge = None
    Histogram = None
    PROM_REGISTRY = None

logger = logging.getLogger("radverify.api")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

MAX_UPLOAD_BYTES = int(os.getenv("RADVERIFY_MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("RADVERIFY_REQUEST_TIMEOUT_SECONDS", "120"))
RATE_LIMIT_REQUESTS = int(os.getenv("RADVERIFY_RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RADVERIFY_RATE_LIMIT_WINDOW_SECONDS", "60"))
MAX_IMAGE_DIMENSION = int(os.getenv("RADVERIFY_MAX_IMAGE_DIMENSION", "8192"))
REDIS_URL = os.getenv("RADVERIFY_REDIS_URL", "")
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/bmp",
    "image/tiff",
    "application/dicom",
    "application/dicom+json",
    "application/octet-stream",
}
API_KEY_ENV = "RADVERIFY_API_KEY"
API_KEY = os.getenv(API_KEY_ENV)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class InMemoryRateLimiter:
    """Simple per-client fixed-window limiter."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        bucket = self._events[key]
        while bucket and (now - bucket[0]) > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            return False
        bucket.append(now)
        return True


class RedisRateLimiter:
    """Redis-backed fixed-window limiter for multi-instance deployments."""

    def __init__(self, redis_url: str, max_requests: int, window_seconds: int):
        if not redis:
            raise RuntimeError("redis package is not installed")
        self.client = redis.Redis.from_url(redis_url, decode_responses=True)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def allow(self, key: str) -> bool:
        redis_key = f"radverify:ratelimit:{key}"
        try:
            current = self.client.incr(redis_key)
            if current == 1:
                self.client.expire(redis_key, self.window_seconds)
            return current <= self.max_requests
        except Exception:
            # Fail open to preserve availability; middleware logs still capture issues.
            return True


class AppMetrics:
    """Tracks lightweight API metrics in memory."""

    def __init__(self):
        self.requests_total = 0
        self.requests_failed = 0
        self.enhancements_by_method: Dict[str, int] = defaultdict(int)
        self.latencies_ms: Deque[float] = deque(maxlen=500)

    def record(self, success: bool, latency_ms: float, enhancement_method: str | None = None):
        self.requests_total += 1
        if not success:
            self.requests_failed += 1
        if enhancement_method:
            self.enhancements_by_method[enhancement_method] += 1
        self.latencies_ms.append(latency_ms)

    def snapshot(self) -> Dict[str, Any]:
        count = len(self.latencies_ms)
        avg_latency = (sum(self.latencies_ms) / count) if count else 0.0
        return {
            "requests_total": self.requests_total,
            "requests_failed": self.requests_failed,
            "error_rate": round(self.requests_failed / self.requests_total, 4) if self.requests_total else 0.0,
            "latency_avg_ms": round(avg_latency, 2),
            "latency_samples": count,
            "enhancements_by_method": dict(self.enhancements_by_method),
        }


class JobStore:
    """In-memory async job tracker for long-running verification requests."""

    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()

    async def create(self, request_id: str) -> str:
        job_id = str(uuid.uuid4())
        async with self.lock:
            self.jobs[job_id] = {
                "job_id": job_id,
                "request_id": request_id,
                "status": "queued",
                "created_at": time.time(),
                "updated_at": time.time(),
                "result": None,
                "error": None,
            }
        return job_id

    async def set_running(self, job_id: str):
        async with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]["status"] = "running"
                self.jobs[job_id]["updated_at"] = time.time()

    async def set_result(self, job_id: str, result: Dict[str, Any]):
        async with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]["status"] = "completed"
                self.jobs[job_id]["updated_at"] = time.time()
                self.jobs[job_id]["result"] = result

    async def set_error(self, job_id: str, error: str):
        async with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]["status"] = "failed"
                self.jobs[job_id]["updated_at"] = time.time()
                self.jobs[job_id]["error"] = error

    async def get(self, job_id: str) -> Dict[str, Any] | None:
        async with self.lock:
            return self.jobs.get(job_id)


def _error(status_code: int, code: str, message: str, *, stage: str | None = None, request_id: str | None = None):
    detail: Dict[str, Any] = {"code": code, "message": message}
    if stage:
        detail["stage"] = stage
    if request_id:
        detail["request_id"] = request_id
    raise HTTPException(status_code=status_code, detail=detail)


async def get_api_key(request: Request, header_key: str = Security(api_key_header)):
    request_id = getattr(request.state, "request_id", None)
    if not API_KEY:
        _error(503, "security_not_configured", f"{API_KEY_ENV} is not set", request_id=request_id)
    if header_key == API_KEY:
        return header_key
    _error(403, "invalid_api_key", "Could not validate API Key", request_id=request_id)


pipeline = RadVerifyPipeline()
db = CaseDatabase()
STARTUP_STATUS: Dict[str, Any] = {}
METRICS = AppMetrics()
JOBS = JobStore()
RATE_LIMITER: InMemoryRateLimiter | RedisRateLimiter
if REDIS_URL:
    try:
        RATE_LIMITER = RedisRateLimiter(REDIS_URL, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)
    except Exception:
        RATE_LIMITER = InMemoryRateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)
else:
    RATE_LIMITER = InMemoryRateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)

def _metric_or_existing(factory, name: str, description: str, *args, **kwargs):
    """Create Prometheus metric once, or reuse existing on module reload."""
    if not factory or PROM_REGISTRY is None:
        return None
    try:
        return factory(name, description, *args, **kwargs)
    except ValueError:
        return getattr(PROM_REGISTRY, "_names_to_collectors", {}).get(name)


PROM_REQUESTS_TOTAL = _metric_or_existing(Counter, "radverify_requests_total", "Total processed API requests")
PROM_REQUESTS_FAILED = _metric_or_existing(Counter, "radverify_requests_failed", "Total failed API requests")
PROM_LATENCY_MS = _metric_or_existing(
    Histogram,
    "radverify_latency_ms",
    "Request latency in ms",
    buckets=(5, 10, 25, 50, 100, 200, 500, 1000, 3000, 10000),
)
PROM_ERROR_RATE = _metric_or_existing(Gauge, "radverify_error_rate", "Error rate")
PROM_ENHANCEMENT_METHOD = _metric_or_existing(
    Counter,
    "radverify_enhancement_method_total",
    "Count by enhancement method",
    ["method"],
)


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
        import basicsr  # noqa: F401
        import realesrgan  # noqa: F401
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


def _looks_like_dicom(data: bytes) -> bool:
    return len(data) >= 132 and data[128:132] == b"DICM"


def _detect_magic_mime(data: bytes) -> str:
    header = data[:16]
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if header[:2] == b"BM":
        return "image/bmp"
    if header[:4] in (b"II*\x00", b"MM\x00*"):
        return "image/tiff"
    if _looks_like_dicom(data):
        return "application/dicom"
    return "unknown"


def _validate_image_dimensions(data: bytes, request_id: str):
    if _looks_like_dicom(data):
        return
    try:
        with Image.open(io.BytesIO(data)) as img:
            width, height = img.size
    except Exception:
        _error(400, "invalid_image_bytes", "Invalid image content", request_id=request_id)
    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        _error(
            413,
            "image_dimensions_too_large",
            f"Image dimensions exceed max {MAX_IMAGE_DIMENSION}px",
            request_id=request_id,
        )


def _check_upload(scan: UploadFile, data: bytes, request_id: str):
    if not data:
        _error(400, "empty_upload", "Uploaded scan is empty.", request_id=request_id)
    if len(data) > MAX_UPLOAD_BYTES:
        _error(
            413,
            "payload_too_large",
            f"Upload too large. Max bytes: {MAX_UPLOAD_BYTES}",
            request_id=request_id,
        )
    content_type = (scan.content_type or "").lower()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        _error(
            415,
            "unsupported_media_type",
            f"Unsupported content type: {content_type}",
            request_id=request_id,
        )
    magic_type = _detect_magic_mime(data)
    if magic_type == "unknown":
        _error(415, "unsupported_file_signature", "Unknown or unsupported file signature", request_id=request_id)
    _validate_image_dimensions(data, request_id)


def _check_model_compatibility() -> Dict[str, Any]:
    info = {"ok": True, "reason": "ok"}
    try:
        analyzer = pipeline.ai_analyzer
        labels = analyzer.labels or []
        model = analyzer.model
        if getattr(analyzer, "model_type", "") != "custom_trained":
            info["ok"] = True
            info["reason"] = "custom_model_not_loaded"
            return info
        if hasattr(model, "output_shape"):
            output_units = int(model.output_shape[-1])
            info["output_units"] = output_units
            info["labels_count"] = len(labels)
            if labels and output_units != len(labels):
                info["ok"] = False
                info["reason"] = "label_model_mismatch"
        return info
    except Exception as exc:
        return {"ok": False, "reason": f"compatibility_check_failed: {exc}"}


def _sanitize_results_for_response(results: Dict[str, Any], request_id: str, start: float) -> Dict[str, Any]:
    enhanced = results.get("enhanced_image")
    enhanced_path = None
    if enhanced is not None:
        enhanced_path = _save_enhanced_image(enhanced)
        results["enhanced_image_path"] = enhanced_path

    case_data = {
        "patient_id": "API_USER_" + str(int(time.time())),
        "ai_findings": results.get("ai_findings", {}),
        "doctor_findings": results.get("doctor_findings", {}),
        "verification_results": results.get("verification_results", {}),
        "comparison_report": results.get("comparison_report_text", ""),
        "medical_narrative": results.get("medical_narrative", ""),
        "image_path": enhanced_path or f"api_upload_{int(time.time())}.png",
    }
    case_id = db.save_case(case_data)
    results["case_id"] = case_id
    results["request_id"] = request_id
    results["runtime_ms"] = round((time.perf_counter() - start) * 1000.0, 2)

    if "original_image" in results:
        del results["original_image"]
    if "enhanced_image" in results:
        del results["enhanced_image"]
    return results


def _startup_check() -> None:
    optional = _check_optional_dependencies()
    enhancer_check = pipeline.image_enhancer.self_check()
    STARTUP_STATUS.update(
        {
            "optional": optional,
            "enhancer_check": enhancer_check,
            "model_compatibility": _check_model_compatibility(),
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
        logger.warning(json.dumps({"event": "startup_missing_optional", "missing": missing}))
    if not API_KEY:
        logger.error(json.dumps({"event": "startup_security_error", "message": f"{API_KEY_ENV} is not set"}))
    if not STARTUP_STATUS["model_compatibility"].get("ok", True):
        logger.error(json.dumps({"event": "startup_model_compatibility_error", "data": STARTUP_STATUS["model_compatibility"]}))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _startup_check()
    yield


app = FastAPI(
    title="RadVerify API",
    description="Professional API for Pregnancy Ultrasound Verification",
    version="1.3.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    start = time.perf_counter()
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = None
    success = False
    try:
        response = await call_next(request)
        success = response.status_code < 400
        return response
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        enhancement_method = getattr(request.state, "enhancement_method", None)
        METRICS.record(success=success, latency_ms=elapsed_ms, enhancement_method=enhancement_method)
        if PROM_REQUESTS_TOTAL:
            PROM_REQUESTS_TOTAL.inc()
        if not success and PROM_REQUESTS_FAILED:
            PROM_REQUESTS_FAILED.inc()
        if PROM_LATENCY_MS:
            PROM_LATENCY_MS.observe(elapsed_ms)
        snapshot = METRICS.snapshot()
        if PROM_ERROR_RATE:
            PROM_ERROR_RATE.set(snapshot["error_rate"])
        if enhancement_method and PROM_ENHANCEMENT_METHOD:
            PROM_ENHANCEMENT_METHOD.labels(method=enhancement_method).inc()
        log_payload = {
            "event": "http_request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": getattr(response, "status_code", 500),
            "latency_ms": round(elapsed_ms, 2),
            "client": request.client.host if request.client else "unknown",
        }
        logger.info(json.dumps(log_payload))


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None)
    detail = exc.detail
    if isinstance(detail, dict):
        detail.setdefault("request_id", request_id)
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/health/details")
def health_details() -> Dict[str, Any]:
    return {
        "status": "ok",
        "optional": STARTUP_STATUS.get("optional", _check_optional_dependencies()),
        "enhancer_check": STARTUP_STATUS.get("enhancer_check", {}),
        "model_compatibility": STARTUP_STATUS.get("model_compatibility", {}),
        "versions": STARTUP_STATUS.get("versions", {}),
        "security": {"api_key_configured": bool(API_KEY)},
        "ratelimiter": "redis" if isinstance(RATE_LIMITER, RedisRateLimiter) else "memory",
    }


@app.get("/ready")
def ready() -> Dict[str, Any]:
    model_ok = STARTUP_STATUS.get("model_compatibility", {}).get("ok", True)
    enhancer_ok = STARTUP_STATUS.get("enhancer_check", {}).get("ok", True)
    api_key_ok = bool(API_KEY)

    is_ready = bool(model_ok and enhancer_ok and api_key_ok)
    return {
        "status": "ready" if is_ready else "degraded",
        "ready": is_ready,
        "checks": {
            "model_compatibility": model_ok,
            "enhancer": enhancer_ok,
            "api_key_configured": api_key_ok,
        },
    }


@app.get("/metrics")
def metrics(api_key: APIKey = Depends(get_api_key)) -> Dict[str, Any]:
    return METRICS.snapshot()


@app.get("/metrics/prometheus", response_class=PlainTextResponse)
def metrics_prometheus(api_key: APIKey = Depends(get_api_key)) -> str:
    if Counter and Histogram and Gauge:
        from prometheus_client import generate_latest
        return generate_latest().decode("utf-8")
    snapshot = METRICS.snapshot()
    lines = [
        "# HELP radverify_requests_total Total processed API requests",
        "# TYPE radverify_requests_total counter",
        f"radverify_requests_total {snapshot['requests_total']}",
        "# HELP radverify_requests_failed Total failed API requests",
        "# TYPE radverify_requests_failed counter",
        f"radverify_requests_failed {snapshot['requests_failed']}",
        "# HELP radverify_error_rate Ratio of failed requests",
        "# TYPE radverify_error_rate gauge",
        f"radverify_error_rate {snapshot['error_rate']}",
        "# HELP radverify_latency_avg_ms Average request latency in ms (recent window)",
        "# TYPE radverify_latency_avg_ms gauge",
        f"radverify_latency_avg_ms {snapshot['latency_avg_ms']}",
    ]
    for method, count in snapshot["enhancements_by_method"].items():
        lines.extend(
            [
                "# HELP radverify_enhancement_method_total Count by enhancement method",
                "# TYPE radverify_enhancement_method_total counter",
                f'radverify_enhancement_method_total{{method="{method}"}} {count}',
            ]
        )
    return "\n".join(lines) + "\n"


@app.post("/verify", response_model=Dict[str, Any])
async def verify_report(
    request: Request,
    scan: UploadFile = File(..., description="Single medical scan (jpg/png/bmp/tiff/dcm)"),
    report: str = Form(..., description="Radiology report text"),
    enhance: bool = Form(True, description="Apply AI enhancement (slower, may improve quality)"),
    api_key: APIKey = Depends(get_api_key),
) -> Dict[str, Any]:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    client_ip = request.client.host if request.client else "unknown"
    if not RATE_LIMITER.allow(f"{client_ip}:{api_key}"):
        _error(429, "rate_limited", "Too many requests. Please retry later.", request_id=request_id)

    data = await scan.read()
    _check_upload(scan, data, request_id)
    img_io = io.BytesIO(data)
    img_io.name = scan.filename or "uploaded_scan.png"

    start = time.perf_counter()
    try:
        results = await asyncio.wait_for(
            asyncio.to_thread(
                pipeline.process,
                image_file=img_io,
                doctor_report_text=report,
                enhance_image=enhance,
            ),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        _error(504, "pipeline_timeout", "Pipeline timed out", request_id=request_id)
    except Exception as exc:
        _error(500, "pipeline_exception", str(exc), request_id=request_id)

    if not results.get("success"):
        stage = results.get("stage")
        if stage == "input_validation":
            _error(
                400,
                "input_validation_failed",
                "Input validation failed",
                stage=stage,
                request_id=request_id,
            )
        _error(
            500,
            "pipeline_stage_failed",
            f"Pipeline failed at stage: {stage}",
            stage=stage,
            request_id=request_id,
        )

    results = _sanitize_results_for_response(results, request_id, start)

    enhancement_metadata = results.get("enhancement_metadata") or {}
    enhancement_method = enhancement_metadata.get("method")
    request.state.enhancement_method = enhancement_method
    return results


async def _run_verify_job(job_id: str, data: bytes, filename: str, report: str, enhance: bool):
    await JOBS.set_running(job_id)
    try:
        start = time.perf_counter()
        img_io = io.BytesIO(data)
        img_io.name = filename
        results = await asyncio.wait_for(
            asyncio.to_thread(
                pipeline.process,
                image_file=img_io,
                doctor_report_text=report,
                enhance_image=enhance,
            ),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if not results.get("success"):
            stage = results.get("stage")
            await JOBS.set_error(job_id, f"pipeline_stage_failed:{stage}")
            return
        results = _sanitize_results_for_response(results, request_id=job_id, start=start)
        await JOBS.set_result(job_id, results)
    except Exception as exc:
        await JOBS.set_error(job_id, str(exc))


@app.post("/verify-async", response_model=Dict[str, Any])
async def verify_report_async(
    request: Request,
    scan: UploadFile = File(..., description="Single medical scan (jpg/png/bmp/tiff/dcm)"),
    report: str = Form(..., description="Radiology report text"),
    enhance: bool = Form(True, description="Apply AI enhancement"),
    api_key: APIKey = Depends(get_api_key),
) -> Dict[str, Any]:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    client_ip = request.client.host if request.client else "unknown"
    if not RATE_LIMITER.allow(f"{client_ip}:{api_key}"):
        _error(429, "rate_limited", "Too many requests. Please retry later.", request_id=request_id)
    data = await scan.read()
    _check_upload(scan, data, request_id)
    job_id = await JOBS.create(request_id=request_id)
    asyncio.create_task(_run_verify_job(job_id, data, scan.filename or "uploaded_scan.png", report, enhance))
    return {"job_id": job_id, "status": "queued", "request_id": request_id}


@app.get("/verify-async/{job_id}", response_model=Dict[str, Any])
async def get_verify_job(job_id: str, api_key: APIKey = Depends(get_api_key)) -> Dict[str, Any]:
    job = await JOBS.get(job_id)
    if not job:
        _error(404, "job_not_found", "Job not found")
    return job


@app.get("/history", response_model=List[Dict[str, Any]])
async def get_history(limit: int = 10, api_key: APIKey = Depends(get_api_key)):
    return db.get_recent_cases(limit=limit)


@app.get("/case/{case_id}", response_model=Dict[str, Any])
async def get_case_details(case_id: int, api_key: APIKey = Depends(get_api_key)):
    case = db.get_case(case_id)
    if not case:
        _error(404, "case_not_found", "Case not found")
    return case


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
