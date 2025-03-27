"""
Configuration management for phenopacket-ingest.

This module handles configuration settings from environment variables,
default values, and user overrides.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class PhenopacketStoreConfig:
    """Configuration for phenopacket-store operations."""

    repo_owner: str = "monarch-initiative"
    repo_name: str = "phenopacket-store"

    data_dir: str = "data/phenopackets"
    output_dir: str = "data/phenopackets/output"

    release_tag: Optional[str] = None
    timeout: float = 30.0

    def __post_init__(self):
        """Initialize from environment variables if available."""
        self.repo_owner = os.environ.get("PHENOPACKET_REPO_OWNER", self.repo_owner)
        self.repo_name = os.environ.get("PHENOPACKET_REPO_NAME", self.repo_name)
        self.data_dir = os.environ.get("PHENOPACKET_DATA_DIR", self.data_dir)
        self.output_dir = os.environ.get("PHENOPACKET_OUTPUT_DIR", self.output_dir)
        self.release_tag = os.environ.get("PHENOPACKET_RELEASE_TAG", self.release_tag)
        self.timeout = float(os.environ.get("PHENOPACKET_DOWNLOAD_TIMEOUT", str(self.timeout)))


def get_config() -> PhenopacketStoreConfig:
    """
    Get the current configuration.

    Returns:
        A PhenopacketStoreConfig object with current settings
    """
    return PhenopacketStoreConfig()