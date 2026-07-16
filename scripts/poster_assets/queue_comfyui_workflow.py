#!/usr/bin/env python3
"""Queue a ComfyUI API workflow and wait for its output."""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path
from uuid import uuid4


def request_json(url: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def queue_workflow(
    workflow_path: Path,
    server: str = "http://127.0.0.1:8188",
    timeout: int = 3600,
) -> list[dict[str, object]]:
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    queued = request_json(
        f"{server.rstrip('/')}/prompt",
        {"prompt": workflow, "client_id": str(uuid4())},
    )
    prompt_id = str(queued["prompt_id"])
    print(f"queued {prompt_id}", flush=True)

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        history = request_json(f"{server.rstrip('/')}/history/{prompt_id}")
        item = history.get(prompt_id)
        if item:
            status = item.get("status", {})
            if status.get("status_str") == "error":
                print(json.dumps(item, indent=2, sort_keys=True))
                raise RuntimeError(f"ComfyUI workflow failed: {json.dumps(item, sort_keys=True)}")
            outputs = []
            for output in item.get("outputs", {}).values():
                outputs.extend(output.get("images", []))
            print(json.dumps({"prompt_id": prompt_id, "outputs": outputs}, indent=2, sort_keys=True))
            return outputs
        time.sleep(2)
    raise TimeoutError(f"Timed out waiting for {prompt_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", type=Path, required=True)
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--timeout", type=int, default=3600)
    args = parser.parse_args()
    queue_workflow(args.workflow, args.server, args.timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
