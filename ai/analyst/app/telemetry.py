from __future__ import annotations

import time
import uuid
from typing import Callable

from fastapi import Request
from starlette.responses import Response


def get_or_create_trace_id(request: Request) -> str:
    supplied = request.headers.get("X-Trace-ID")
    return supplied.strip() if supplied and supplied.strip() else str(uuid.uuid4())


def request_timing(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)
