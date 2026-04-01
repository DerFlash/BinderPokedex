# BinderPokedex workspace instructions

- Treat this repository as a Python project with two main runtime areas: `scripts/fetcher` for data acquisition and transformation, and `scripts/pdf` for PDF generation.
- Preserve the existing data-driven architecture: scope definitions live in `config/scopes`, generated data lives under `data/output`, and rendering logic stays in `scripts/pdf/lib`.
- Do not modify large generated artifacts such as `output/`, `data/output/`, or `data/pokemon_images_cache/` unless the task explicitly requires regeneration.
- Prefer root-cause fixes over ad hoc patches. If tests fail because of import structure drift, fix shared bootstrap or compatibility layers instead of copying `sys.path` hacks into many files.
- Keep changes minimal and localized. Avoid broad refactors across fetcher, PDF rendering, and docs unless the task needs cross-cutting work.
- When changing fetcher or PDF behavior, validate with the smallest relevant scope and language first before attempting broad runs.
- Preserve multilingual behavior and CJK support. Font handling should fail clearly or fall back intentionally, never silently corrupt output.
- When user-facing behavior changes and there is an obvious paired document, update the matching documentation as part of the change.