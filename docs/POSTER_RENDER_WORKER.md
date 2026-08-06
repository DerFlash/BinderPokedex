# Native macOS poster render worker

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

Copy the immutable job directory to the remote `jobs/` folder with SSH or
`rsync`. On the render host:

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
