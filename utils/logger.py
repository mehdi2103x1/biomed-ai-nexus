"""
utils.logger
============
Project-wide logging helper.

A single rotating file handler (``logs/app.log``) plus a console handler are
configured once. Every module obtains its logger through :func:`get_logger`
so that all components share the same format and destination.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

import sys

try:
    from config import LOG_DIR
except ModuleNotFoundError:  # pragma: no cover - allows running from sub-dirs
    from pathlib import Path
    LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_configured = False


def _configure_root() -> None:
    """Attach handlers to the root logger exactly once (idempotent)."""
    global _configured
    if _configured:
        return

    root = logging.getLogger("biomed")
    root.setLevel(logging.INFO)
    root.propagate = False

    formatter = logging.Formatter(_LOG_FORMAT)

    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(stream_handler)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced child logger (e.g. ``biomed.preprocessing``)."""
    _configure_root()
    return logging.getLogger(f"biomed.{name}")
