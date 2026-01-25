"""Structured tracing helpers for RadVerify pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .logging_utils import get_logger


@dataclass
class TraceEntry:
    stage: str
    message: str


class TraceRecorder:
    """Collects ordered trace entries while mirroring them to the logger."""

    def __init__(self, stage_prefix: str = "RadVerify", logger=None):
        self.stage_prefix = stage_prefix
        self.logger = logger or get_logger()
        self._entries: List[TraceEntry] = []

    def add(self, stage: str, message: str) -> None:
        entry = TraceEntry(stage=stage, message=message)
        self._entries.append(entry)
        self.logger.info("%s | %s: %s", self.stage_prefix, stage, message)

    def extend(self, stage: str, messages: Iterable[str]) -> None:
        for message in messages:
            self.add(stage, message)

    def as_strings(self) -> List[str]:
        return [f"{entry.stage}: {entry.message}" for entry in self._entries]

    def latest(self) -> Optional[TraceEntry]:
        return self._entries[-1] if self._entries else None
