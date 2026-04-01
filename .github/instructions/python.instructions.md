---
name: python-standards
description: "Use for Python changes in BinderPokedex fetcher, PDF generator, and shared libraries."
applyTo: "**/*.py"
---

# Python conventions for BinderPokedex

- Prefer `pathlib.Path` over manual path string handling.
- Keep fetcher, PDF generation, and shared library responsibilities separated; avoid mixing API access, persistence, and rendering in one module.
- Preserve CLI entry points and argument behavior in `scripts/fetcher/fetch.py`, `scripts/pdf/generate_pdf.py`, and related scripts unless the task explicitly changes them.
- For tests, prefer a shared bootstrap such as `scripts/tests/conftest.py` over repeating `sys.path` manipulation inside each test file.
- Keep new compatibility shims small and explicit when supporting legacy imports or older helper names.
- For font or rendering changes, prefer explicit fallback behavior and assertions over silent best-effort behavior that hides broken output.