from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_project_file(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_artwork_agents_must_ask_for_local_or_remote_rendering():
    guidance = read_project_file("AGENTS.md")

    assert (
        "whether the candidate should be rendered locally or on a remote worker"
        in guidance
    )
    assert "docs/POSTER_RENDER_WORKER.md" in guidance
    assert "Do not expose ComfyUI on a public interface" in guidance


def test_remote_worker_guide_is_discoverable_from_normal_documentation():
    readme = read_project_file("README.md")
    workflow = read_project_file("docs/POSTER_WORKFLOW.md")

    assert "docs/POSTER_RENDER_WORKER.md" in readme
    assert "Choose the render target before GPU work" in workflow
    assert "[Remote Poster Render Worker](POSTER_RENDER_WORKER.md)" in workflow


def test_v9_history_records_remote_generation_without_an_endpoint():
    changelog = read_project_file("CHANGELOG.md")
    v9 = changelog.split("## [9.0.0]", 1)[1].split("## [8.4.0]", 1)[0]

    assert "isolated remote Apple" in v9
    assert "hostname, network address, credentials" in v9
