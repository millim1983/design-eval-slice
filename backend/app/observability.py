from __future__ import annotations

"""Lightweight observability helpers.

This module initializes an optional Langfuse client using environment
variables and exposes a ``span`` context manager for tracing and timing
operations.  If configuration or environment variables are missing, the
functions degrade to no-ops that simply log timings locally.
"""

import logging
import os
import time
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)


class NoOpTracer:
    """Fallback tracer that only records debug logs."""

    @contextmanager
    def span(self, name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = (time.perf_counter() - start) * 1000
            logger.debug("%s took %.2fms", name, duration)


class LangfuseTracer:
    """Wrapper around the Langfuse client providing a ``span`` method."""

    def __init__(self, client: Any) -> None:
        self.client = client

    @contextmanager
    def span(self, name: str):
        trace = self.client.trace(name=name)
        start = time.perf_counter()
        try:
            with trace:
                yield trace
        finally:
            duration = (time.perf_counter() - start) * 1000
            try:
                trace.log({"duration_ms": duration})
            except Exception:  # pragma: no cover - optional logging
                logger.debug("Failed to log span '%s'", name)


_tracer: Any = NoOpTracer()


def init_observability(config: Any) -> None:
    """Initialize the global tracer based on configuration and env vars."""

    global _tracer
    if not getattr(config, "enabled", False):
        logger.info("Observability disabled by config")
        return
    try:
        from langfuse import Langfuse  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.warning("Langfuse import failed: %s", exc)
        return
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST")
    if not public_key or not secret_key:
        logger.warning("Langfuse credentials missing; observability disabled")
        return
    client = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    _tracer = LangfuseTracer(client)
    logger.info("Observability enabled")


def span(name: str):
    """Public helper returning a tracing context manager."""

    return _tracer.span(name)
