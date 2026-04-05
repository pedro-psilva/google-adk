from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "src"))

from profile_backend.interfaces.adk.agent import root_agent

__all__ = ["root_agent"]
