---
name: scope-pipeline
description: "Analyze or modify BinderPokedex scope definitions, fetcher pipeline wiring, and PDF generation handoff. Use when adding a scope, debugging a scope, tracing config-to-output flow, or deciding where a scope-related change belongs."
argument-hint: "[scope name or pipeline problem]"
---

# Scope Pipeline

Use this skill when working on repository tasks that involve scope configuration, data fetching, or PDF generation flow.

## What this skill covers

- `config/scopes/*.yaml` definitions
- fetcher behavior under `scripts/fetcher`
- generated JSON structure under `data/output`
- PDF generation behavior under `scripts/pdf`

## Workflow

1. Identify the scope and its source of truth in `config/scopes`.
2. Trace how the scope is consumed by the fetcher and what shape it produces in `data/output`.
3. Confirm how the PDF generator expects to read that data.
4. Prefer fixing schema mismatches or pipeline boundaries at the shared layer instead of adding one-off exceptions.
5. Validate with the smallest relevant scope and one language before running broader generation.
6. Update tests and documentation if the behavior or workflow changes.

## Repository references

Consult `docs/DATA_FETCHER.md`, `docs/ARCHITECTURE.md`, and `docs/USAGE.md` for pipeline and architecture details. A step-by-step workflow checklist is in `checklist.md` alongside this file.