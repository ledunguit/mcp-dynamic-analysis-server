from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..config import load_settings
from ..core.artifact_store import ArtifactStore
from ..core.exceptions import ArtifactNotFound
from ..tools.get_raw_artifact import ARTIFACT_MAP


@dataclass(frozen=True)
class ResourceItem:
    uri: str
    name: str
    description: str
    mime_type: str


RESOURCE_SCHEME = "artifact"


def list_resources(limit: int = 50) -> List[Dict[str, str]]:
    settings = load_settings()
    store = ArtifactStore(settings.runs_dir)
    runs = store.list_runs()[-limit:]
    resources: List[ResourceItem] = []

    for run_id in runs:
        for artifact_type in ARTIFACT_MAP.keys():
            uri = f"{RESOURCE_SCHEME}://{run_id}/{artifact_type}"
            resources.append(
                ResourceItem(
                    uri=uri,
                    name=f"{run_id}:{artifact_type}",
                    description=f"Artifact {artifact_type} for run {run_id}",
                    mime_type="text/plain",
                )
            )

    return [
        {
            "uri": item.uri,
            "name": item.name,
            "description": item.description,
            "mimeType": item.mime_type,
        }
        for item in resources
    ]


def read_resource(uri: str) -> Dict[str, str]:
    if not uri.startswith(f"{RESOURCE_SCHEME}://"):
        raise ArtifactNotFound(f"Unsupported resource URI: {uri}")

    _, remainder = uri.split("//", 1)
    if "/" not in remainder:
        raise ArtifactNotFound(f"Invalid resource URI: {uri}")

    run_id, artifact_type = remainder.split("/", 1)

    settings = load_settings()
    store = ArtifactStore(settings.runs_dir)
    filename = ARTIFACT_MAP.get(artifact_type)
    if not filename:
        raise ArtifactNotFound(f"Unknown artifact type: {artifact_type}")

    path = settings.runs_dir / run_id / filename
    content = store.read_text(path, max_bytes=settings.max_artifact_preview_bytes)

    return {
        "uri": uri,
        "mimeType": "text/plain",
        "text": content,
    }
