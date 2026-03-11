"""
Request Pre-processor for AI Security Sentinel
Converts raw HTTP request objects into numerical feature vectors for the Isolation Forest model.
"""

import numpy as np
import time
from datetime import datetime
from typing import Any

# Common legitimate user agents (partial match list)
COMMON_USER_AGENTS = [
    "mozilla", "chrome", "safari", "firefox", "edge",
    "opera", "curl", "python-requests", "axios", "wget"
]


def extract_features(request: dict[str, Any]) -> np.ndarray:
    """
    Convert a raw HTTP request JSON object into a NumPy feature array.

    Expected request fields (all optional with safe defaults):
        - timestamp       (float)  : Unix timestamp of the request
        - payload_size    (int)    : Content-Length or body size in bytes
        - user_agent      (str)    : User-Agent header string
        - request_rate    (float)  : Requests/second from this IP (pre-computed by caller)

    Returns:
        np.ndarray of shape (4,) with dtype float32:
            [request_rate, payload_size, is_common_user_agent, time_of_day]
    """
    start = time.perf_counter()

    # 1. request_rate — requests per second from this IP (caller-supplied)
    request_rate = float(request.get("request_rate", 1.0))

    # 2. payload_size — body/content size in bytes
    payload_size = float(request.get("payload_size", 0))

    # 3. is_common_user_agent — 1.0 if recognised browser/tool, else 0.0
    ua = str(request.get("user_agent", "")).lower()
    is_common_user_agent = 1.0 if any(agent in ua for agent in COMMON_USER_AGENTS) else 0.0

    # 4. time_of_day — hour of day (0–23) derived from timestamp or current time
    ts = request.get("timestamp", None)
    if ts is not None:
        hour = datetime.fromtimestamp(float(ts)).hour
    else:
        hour = datetime.now().hour
    time_of_day = float(hour)

    features = np.array(
        [request_rate, payload_size, is_common_user_agent, time_of_day],
        dtype=np.float32
    )

    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 10, f"Pre-processor exceeded 10ms SLA: {elapsed_ms:.2f}ms"

    return features


def batch_extract(requests: list[dict[str, Any]]) -> np.ndarray:
    """Vectorise a list of request dicts into a 2-D feature matrix (N x 4)."""
    return np.stack([extract_features(r) for r in requests])
