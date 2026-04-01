---
name: binder-maintainer
description: "Maintain BinderPokedex scopes, fetcher pipelines, PDF generation, tests, and documentation while preserving the current architecture and avoiding generated artifacts unless requested."
argument-hint: "[task, scope name, or failing area]"
---

# Binder Maintainer

Repository-wide guidance and Python/test conventions are applied automatically via workspace instructions.

Use this agent when the task spans multiple parts of the repository, especially:

- scope configuration plus fetcher or PDF changes
- repo-wide maintenance or cleanup
- test failures caused by architecture drift
- documentation updates tied to technical changes

Working approach:

1. Inspect the smallest relevant area first.
2. Prefer shared fixes over repetitive local workarounds.
3. Avoid touching generated output, caches, or release artifacts unless explicitly requested.
4. Validate behavior with the narrowest practical test or command before wider runs.