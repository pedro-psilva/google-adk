#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

import uvicorn


def main() -> None:
    uvicorn.run("profile_backend.interfaces.http.api:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
