"""Simple telemetry capture for RadVerify."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_TELEMETRY_PATH = Path("logs/telemetry.log")


@dataclass
class TelemetryEvent:
    event_type: str
    payload: Dict[str, Any]
    timestamp: str


class TelemetryClient:
    def __init__(self, filepath: Path | str = DEFAULT_TELEMETRY_PATH):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def record_event(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        event = TelemetryEvent(
            event_type=event_type,
            payload=payload or {},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        with self.filepath.open("a", encoding="utf-8") as handle:
            json.dump(event.__dict__, handle)
            handle.write("\n")


_CLIENT: Optional[TelemetryClient] = None


def get_telemetry_client() -> TelemetryClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = TelemetryClient()
    return _CLIENT
