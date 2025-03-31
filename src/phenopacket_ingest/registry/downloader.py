"""
Phenopacket downloader module.

This module provides functionality for downloading phenopacket data
from GitHub repositories or other sources.
"""

import json
import logging
import os
import re
import ssl
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.request import urlopen

import certifi

from phenopacket_ingest.config import PhenopacketStoreConfig


class VersionResolver:
    """Resolver for semantic versioning."""

    SEMVER_VERSION_PATTERN = re.compile(r"v?(?P<major>\d+)(\.(?P<minor>\d+))?(\.(?P<patch>\d+))?")

    @classmethod
    def find_latest_version(cls, tags: List[Dict[str, Any]]) -> Optional[str]:
        """
        Find the latest version from a list of GitHub tags.

        Args:
            tags: List of tag objects from GitHub API

        Returns:
            Latest version tag or None if no valid tags found

        """
        if not tags:
            return None

        latest_tag = None
        latest_components = None

        for tag in tags:
            tag_name = tag["name"]
            matcher = cls.SEMVER_VERSION_PATTERN.match(tag_name)
            if matcher is not None:
                major = int(matcher.group("major"))
                minor = int(matcher.group("minor")) if matcher.group("minor") is not None else 0
                patch = int(matcher.group("patch")) if matcher.group("patch") is not None else 0
                current = (major, minor, patch)

                if latest_components is None or current > latest_components:
                    latest_components = current
                    latest_tag = tag_name

        return latest_tag


class PhenopacketDownloader:
    """Downloader for phenopacket data."""

    def __init__(self, config: PhenopacketStoreConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize phenopacket downloader.

        Args:
            config: Configuration settings
            logger: Logger for tracking operations

        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

    def download_from_github(self, data_dir: Path) -> Path:
        """
        Download phenopacket release directly from GitHub.

        Args:
            data_dir: Directory to store downloaded phenopackets

        Returns:
            Path to the downloaded ZIP file

        """
        self.logger.info("Downloading phenopacket-store release from GitHub")

        ctx = ssl.create_default_context(cafile=certifi.where())
        tag_api_url = f"https://api.github.com/repos/{self.config.repo_owner}/{self.config.repo_name}/tags"
        self.logger.debug(f"Fetching tags from {tag_api_url}")

        try:
            with urlopen(tag_api_url, timeout=10.0, context=ctx) as fh:
                tags = json.load(fh)

            if len(tags) == 0:
                raise ValueError("No tags could be fetched from GitHub tag API")

            release_tag = self.config.release_tag
            if not release_tag:
                release_tag = VersionResolver.find_latest_version(tags)
                if not release_tag:
                    raise ValueError("Could not determine latest release tag")

            release_url = f"https://github.com/{self.config.repo_owner}/{self.config.repo_name}/releases/download/{release_tag}/all_phenopackets.zip"
            self.logger.info(f"Downloading phenopacket-store from {release_url}")

            zip_file_path = data_dir / f"{release_tag}.zip"
            os.makedirs(os.path.dirname(zip_file_path), exist_ok=True)

            with urlopen(release_url, timeout=self.config.timeout, context=ctx) as response, open(
                zip_file_path, "wb"
            ) as fh:
                fh.write(response.read())

            self.logger.info(f"Downloaded phenopacket-store release {release_tag} to {zip_file_path}")
            return zip_file_path

        except Exception as e:
            self.logger.error(f"Error downloading phenopacket-store: {e}")
            raise
