"""Simple latency benchmark for /verify endpoint."""

from __future__ import annotations

import argparse
import io
import os
import statistics
import sys
import time
from pathlib import Path
from typing import List

from fastapi.testclient import TestClient
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

api_server = None


def _p95(values: List[float]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = min(len(values) - 1, int(round(0.95 * (len(values) - 1))))
    return float(values[idx])


def run_benchmark(iterations: int, enhance: bool, report: str) -> dict:
    global api_server
    if api_server is None:
        os.environ.setdefault("RADVERIFY_API_KEY", "benchmark_secret_key")
        import api_server as _api_server
        api_server = _api_server
    client = TestClient(api_server.app)
    latencies_ms: List[float] = []

    for _ in range(iterations):
        img = Image.new("RGB", (256, 256), color="gray")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        start = time.perf_counter()
        response = client.post(
            "/verify",
            files={"scan": ("bench.png", buf, "image/png")},
            data={"report": report, "enhance": str(enhance).lower()},
            headers={"X-API-Key": "benchmark_secret_key"},
        )
        elapsed = (time.perf_counter() - start) * 1000.0
        if response.status_code != 200:
            raise RuntimeError(f"Request failed: {response.status_code} - {response.text}")
        latencies_ms.append(elapsed)

    result = {
        "iterations": iterations,
        "enhance": enhance,
        "p50_ms": round(statistics.median(latencies_ms), 2),
        "p95_ms": round(_p95(latencies_ms), 2),
        "avg_ms": round(statistics.mean(latencies_ms), 2),
    }
    print(
        f"iterations={result['iterations']} enhance={result['enhance']} "
        f"p50_ms={result['p50_ms']:.2f} p95_ms={result['p95_ms']:.2f} avg_ms={result['avg_ms']:.2f}"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark /verify latency.")
    parser.add_argument("--iterations", type=int, default=15)
    parser.add_argument("--report", type=str, default="Sample fetal ultrasound report text for pipeline verification. Normal anatomy reported.")
    parser.add_argument("--max-p50-no-enhance-ms", type=float, default=None)
    parser.add_argument("--max-p50-enhance-ms", type=float, default=None)
    args = parser.parse_args()

    no_enhance = run_benchmark(args.iterations, enhance=False, report=args.report)
    enhance = run_benchmark(args.iterations, enhance=True, report=args.report)

    if args.max_p50_no_enhance_ms is not None and no_enhance["p50_ms"] > args.max_p50_no_enhance_ms:
        raise SystemExit(
            f"FAIL: no-enhance p50 {no_enhance['p50_ms']}ms > {args.max_p50_no_enhance_ms}ms"
        )
    if args.max_p50_enhance_ms is not None and enhance["p50_ms"] > args.max_p50_enhance_ms:
        raise SystemExit(
            f"FAIL: enhance p50 {enhance['p50_ms']}ms > {args.max_p50_enhance_ms}ms"
        )


if __name__ == "__main__":
    main()
