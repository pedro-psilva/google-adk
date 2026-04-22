from __future__ import annotations

from pathlib import Path
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

backend_package_root = Path(__file__).resolve().parents[1] / "backend" / "src" / __name__
backend_package_root_str = str(backend_package_root)
if backend_package_root.exists() and backend_package_root_str not in __path__:
    __path__.insert(0, backend_package_root_str)

from .bundle import load_bundle
from .coverage import analyze_coverage

__all__ = ["analyze_coverage", "load_bundle"]
