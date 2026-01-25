"""Logging helpers for RadVerify backend."""

from __future__ import annotations

import logging
from typing import Optional

_LOGGER: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Return a module-level logger configured once."""

    global _LOGGER
    if _LOGGER is None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] radverify:%(name)s - %(message)s",
        )
        _LOGGER = logging.getLogger("radverify")
    return _LOGGER
