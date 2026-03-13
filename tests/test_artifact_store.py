from pathlib import Path

from mcp_dynamic_analysis_server.core.artifact_store import ArtifactStore, generate_run_id


def test_artifact_store_roundtrip(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    run_id = generate_run_id()
    artifacts = store.create_run_dir(run_id)

    payload = {"hello": "world"}
    store.write_json(artifacts.request_path, payload)
    assert store.read_json(artifacts.request_path) == payload

    store.write_text(artifacts.command_path, "echo test")
    assert store.read_text(artifacts.command_path).strip() == "echo test"
