"""Shared pytest bootstrap for repository-local imports."""

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
PDF_LIB = REPO_ROOT / "scripts" / "pdf" / "lib"
FETCHER_ROOT = REPO_ROOT / "scripts" / "fetcher"

for import_root in (REPO_ROOT, PDF_LIB, FETCHER_ROOT):
    import_root_str = str(import_root)
    if import_root_str not in sys.path:
        sys.path.insert(0, import_root_str)