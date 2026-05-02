"""Upstream source version fetcher for phenopacket-ingest.

phenopacket-store publishes via GitHub releases. Use the GitHub API to
get the latest release tag.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kozahub_metadata_schema import (
    now_iso,
    urls_from_download_yaml,
    version_from_github_release,
)


INGEST_DIR = Path(__file__).resolve().parents[1]
DOWNLOAD_YAML = INGEST_DIR / "download.yaml"


def get_source_versions() -> list[dict[str, Any]]:
    ver, method = version_from_github_release("monarch-initiative/phenopacket-store")
    return [
        {
            "id": "infores:phenopacket-store",
            "name": "Phenopacket Store",
            "urls": urls_from_download_yaml(DOWNLOAD_YAML),
            "version": ver,
            "version_method": method,
            "retrieved_at": now_iso(),
        }
    ]
