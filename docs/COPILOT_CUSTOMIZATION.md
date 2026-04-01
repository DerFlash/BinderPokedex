# Copilot Customization Guide

This repository now includes workspace-shared Copilot customizations for VS Code.

## Included files

- `.github/copilot-instructions.md`: always-on repository guidance
- `.github/instructions/python.instructions.md`: Python-specific rules
- `.github/instructions/tests.instructions.md`: pytest and test-maintenance guidance
- `.github/agents/binder-maintainer.agent.md`: a repo-focused maintenance agent
- `.github/skills/scope-pipeline/`: a reusable skill for scope and pipeline work

## Recommended usage

- Use the default agent for narrow, file-local work.
- Switch to the `binder-maintainer` agent for repo-wide maintenance, cross-module fixes, or scope-to-PDF tasks.
- Invoke `/scope-pipeline` when adding a scope, debugging a scope, or tracing how a scope moves from config through fetcher output into PDF generation.

## Why these customizations exist

- The repository has a clear split between fetcher, data storage, and PDF rendering, and the agent should preserve that split.
- Large generated outputs and image caches should usually not be edited directly.
- Scope-related work often spans configuration, generated JSON structure, and rendering expectations, so a reusable skill keeps that workflow consistent.
- Test maintenance benefits from shared import bootstrap and explicit platform-specific expectations.

## Notes

- Open `Chat: Open Chat Customizations` in VS Code to inspect the loaded customizations.
- Use the Chat diagnostics view if a customization does not seem to apply.