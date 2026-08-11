# Repository agent guidance

## Poster artwork generation

Before starting any GPU-intensive poster artwork generation, ask the operator
whether the candidate should be rendered locally or on a remote worker. Do not
infer the target from a previously used host, an available SSH configuration,
or a running ComfyUI process.

- For a local Apple Metal/MPS render, follow
  `docs/POSTER_WORKFLOW.md` and keep the ComfyUI input/output directories scoped
  to the selected poster asset key.
- For a remote render, follow `docs/POSTER_RENDER_WORKER.md`. Ask for an SSH
  alias and the private runtime, model-cache, job, and repository paths only
  when the operator selects this route. Help probe, bootstrap or transfer the
  disposable runtime, execute and retrieve the immutable render job, and clean
  up the runtime, but leave authentication to the operator's existing SSH
  setup.
- Never commit real hostnames, IP addresses, usernames, SSH aliases,
  machine-specific paths, tokens, or keys. Never print secret material such as
  private keys or access tokens. Do not expose ComfyUI on a public interface;
  the remote worker must bind to loopback and queue the workflow on that host.
- Always bring back `run.json`, `comfyui.log`, and every output image. A
  successful render is not approval: inspect the full poster and all physical
  card crops before any promotion.

This choice applies only to artwork generation. Fetching data, deterministic
localization, slicing, PDF rendering, and release validation do not require a
render worker.
