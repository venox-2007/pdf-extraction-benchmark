"""Package entrypoint — launches the Streamlit UI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Launch the Streamlit benchmarking UI."""
    app = Path(__file__).resolve().parents[0] / "ui" / "app.py"
    sys.exit(subprocess.call(["streamlit", "run", str(app)]))


if __name__ == "__main__":
    main()
