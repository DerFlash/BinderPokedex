---
name: test-conventions
description: "Use for pytest files under scripts/tests and for test maintenance tasks."
applyTo: "scripts/tests/**/*.py"
---

# Test conventions for BinderPokedex

- Centralize test import setup in `scripts/tests/conftest.py`; do not duplicate per-file bootstrap unless a test genuinely needs something special.
- Prefer assertions on observable behavior, returned data, and generated files rather than internal implementation details.
- Keep tests deterministic and small; use temporary directories for file IO when possible.
- If a test depends on system fonts or platform-specific assets, make that expectation explicit and let the failure mode be clear.
- When legacy tests rely on old flat module names, prefer a thin compatibility module or shared import setup instead of rewriting many tests at once.