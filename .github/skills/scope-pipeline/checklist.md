# Scope Pipeline Checklist

Use this checklist when changing a scope or debugging the pipeline.

- Find the relevant file in `config/scopes/`.
- Confirm expected target output file in `data/output/`.
- Inspect fetcher steps referenced by the scope.
- Check whether the PDF generator consumes `cards`, `sections`, metadata, or language-specific fields.
- Prefer shared schema fixes over per-scope exceptions.
- Validate with one scope and one language first.
- Update docs if the workflow, flags, or expected output changed.