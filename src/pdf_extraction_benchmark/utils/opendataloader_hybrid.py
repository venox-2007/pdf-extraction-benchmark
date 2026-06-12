"""Helper for managing the optional OpenDataLoader hybrid (Docling/OCR) server."""

from __future__ import annotations

import subprocess
import time
import urllib.request
from urllib.error import URLError

from pdf_extraction_benchmark.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5002
DEFAULT_OCR_ENGINE = "rapidocr"
HEALTH_CHECK_TIMEOUT_SECONDS = 120
HEALTH_CHECK_INTERVAL_SECONDS = 1.0

_server_process: subprocess.Popen | None = None


def _is_server_healthy(url: str) -> bool:
    """Check whether the hybrid server's `/health` endpoint responds OK."""
    try:
        with urllib.request.urlopen(f"{url}/health", timeout=2) as response:
            return response.status == 200
    except (URLError, OSError):
        return False


def ensure_hybrid_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    ocr_engine: str = DEFAULT_OCR_ENGINE,
) -> str:
    """Ensure the OpenDataLoader hybrid (Docling/OCR) server is running.

    Returns the server's base URL. If the server is not already reachable,
    starts it as a background process and waits for it to report healthy.
    """
    global _server_process
    url = f"http://{host}:{port}"

    if _is_server_healthy(url):
        return url

    if _server_process is None or _server_process.poll() is not None:
        logger.info("Starting OpenDataLoader hybrid server on %s ...", url)
        _server_process = subprocess.Popen(  # noqa: S603,S607
            [
                "opendataloader-pdf-hybrid",
                "--host",
                host,
                "--port",
                str(port),
                "--ocr-engine",
                ocr_engine,
                "--log-level",
                "warning",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    deadline = time.monotonic() + HEALTH_CHECK_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if _is_server_healthy(url):
            logger.info("OpenDataLoader hybrid server ready at %s", url)
            return url
        time.sleep(HEALTH_CHECK_INTERVAL_SECONDS)

    raise RuntimeError(
        f"OpenDataLoader hybrid server did not become healthy at {url} "
        f"within {HEALTH_CHECK_TIMEOUT_SECONDS}s"
    )
