# Remote Apple Silicon poster render worker

The poster generator can submit self-contained ComfyUI jobs to another Apple
Silicon Mac without turning that host into a manually maintained workstation.
The render worker is deliberately native: Docker Desktop runs Linux in a VM
and does not expose the macOS Metal/MPS backend required by this workflow.

## Architecture

1. The repository creates a job directory containing one ComfyUI API workflow,
   its input images, and SHA-256 records for every workflow, input, and model.
2. The directory is copied to an isolated render root over SSH or `rsync`.
3. The remote worker validates every hash, the pinned ComfyUI commit, and the
   available model files before starting ComfyUI.
4. ComfyUI listens on remote loopback only. The worker requires the startup log
   to report `Device: mps`, queues the workflow, and stops ComfyUI afterwards.
   Before queueing, it also verifies that the server reports this job's exact
   input directory; a different ComfyUI process already using the port is
   rejected instead of receiving the workflow.
5. `run.json`, `comfyui.log`, and the generated images are copied back for
   visual review. Nothing is promoted automatically.

The job is the interface. Prompt text may be embedded in the API workflow, and
all scene data or reference images consumed by `LoadImage` travel under the
job's `input/` directory. Models stay cached on the render host and are named
and hash-pinned by each job rather than copied for every run.

`Device: mps` proves that ComfyUI selected Metal as its primary accelerator;
it does not prove that every auxiliary model used MPS. For example, a text
encoder may run once on CPU while the diffusion model samples on MPS. Keep and
review `comfyui.log` whenever per-stage device placement matters.

## Agent/operator handshake

Before any GPU process starts, the operator chooses **local** or **remote**
generation. An artwork-generating agent must ask for that choice and must not
reuse a host from conversation history or machine state without confirmation.
If local is selected, return to the local launcher in
[Poster Workflow](POSTER_WORKFLOW.md).

If remote is selected, the agent may help with the steps in this guide after
the operator supplies an existing SSH config alias and the two remote paths.
The agent must not request, inspect, transmit, or persist passwords, access
tokens, private keys, real hostnames, IP addresses, or usernames. SSH
authentication remains outside the repository and render job.

## Bind a worker without persisting host details

Keep connection values only in the current shell or the operator's private SSH
configuration. The placeholders below are deliberately not real endpoints:

```bash
export BINDER_RENDER_SSH="SSH_CONFIG_ALIAS"
export BINDER_RENDER_ROOT="/absolute/path/to/BinderPokedex-render"
export BINDER_RENDER_REPO="/absolute/path/to/BinderPokedex-checkout"
```

Probe the selected host before transferring a job:

```bash
ssh "$BINDER_RENDER_SSH" 'uname -s; uname -m'
ssh "$BINDER_RENDER_SSH" \
  "git -C '$BINDER_RENDER_REPO' status --short --branch"
```

The expected platform is `Darwin` on `arm64`; the remote checkout should be on
the intended commit or feature branch. This probe does not grant permission to
install software, download models, or start a render. Confirm those separately
when needed.

Do not add these values to `.env`, Git configuration, manifests, run metadata,
or documentation. Do not expose port 8188 publicly and do not point the normal
local runner's `--server` option at a public remote URL. `render_job.py run`
starts loopback-only ComfyUI and queues the workflow on the worker, which also
keeps job-local input-path validation intact.

## Bootstrap one Apple Silicon host

Clone this repository on the render host, check out the desired feature branch,
then run:

```bash
scripts/poster_assets/bootstrap_macos_renderer.sh \
  /absolute/path/to/BinderPokedex-render
```

The command pins ComfyUI, creates an isolated Python 3.11 virtual environment,
installs its requirements, applies the repository's version-checked Apple-MPS
quantization and text-encoder compatibility patch, and verifies native MPS
availability. It does not install models or change global Python packages.

Gated Hugging Face models require a one-time login performed by the host owner:

```bash
/absolute/path/to/BinderPokedex-render/venv/bin/hf auth login
```

Never put a Hugging Face token in the repository, workflow, job manifest, or
chat. Download approved model files into the corresponding directory below
`ComfyUI/models/`, then record their SHA-256 values in the job.

## Prepare a job locally

The command refuses to overwrite an existing job directory:

```bash
python scripts/poster_assets/render_job.py prepare \
  --workflow path/to/workflow_api.json \
  --job-dir tmp/render-jobs/exgen2-normal-kontext-bf16 \
  --input path/to/scene.png=scene.png \
  --model diffusion_models/flux1-kontext-dev.safetensors=SHA256 \
  --model text_encoders/clip_l.safetensors=SHA256 \
  --model text_encoders/t5xxl_fp16.safetensors=SHA256 \
  --model vae/ae.safetensors=SHA256
```

Every `LoadImage` filename in the workflow must match the destination name on
the right side of an `--input SOURCE=DESTINATION` argument.

## Transfer and run

Choose a local job name and transfer the immutable directory to the worker:

```bash
export JOB_NAME="reviewed-job-name"
export LOCAL_JOB_DIR="tmp/render-jobs/$JOB_NAME"

rsync -a "$LOCAL_JOB_DIR/" \
  "$BINDER_RENDER_SSH:$BINDER_RENDER_ROOT/jobs/$JOB_NAME/"
```

Open an SSH session and run the job with the already bootstrapped worker. The
paths remain runtime values and are not copied into tracked project files:

```bash
ssh "$BINDER_RENDER_SSH"
```

On the render host:

```bash
/absolute/path/to/BinderPokedex-render/venv/bin/python \
  /absolute/path/to/repo/scripts/poster_assets/render_job.py run \
  --job-dir /absolute/path/to/BinderPokedex-render/jobs/JOB_NAME \
  --comfyui-root /absolute/path/to/BinderPokedex-render/ComfyUI \
  --python /absolute/path/to/BinderPokedex-render/venv/bin/python \
  --models-root /absolute/path/to/BinderPokedex-render/ComfyUI/models
```

Copy the completed job back and review `run.json`, `comfyui.log`, the whole
poster, and every physical card crop. A successful remote process is evidence
of reproducibility, not visual approval.

After leaving the SSH session, retrieve the entire completed job:

```bash
rsync -a \
  "$BINDER_RENDER_SSH:$BINDER_RENDER_ROOT/jobs/$JOB_NAME/" \
  "$LOCAL_JOB_DIR/"
```

Keep the returned job ignored until review. Promotion still happens through the
normal local review and promotion gate; a remote worker never promotes assets.
