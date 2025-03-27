"""
Registry module for downloading and managing phenopacket data.
"""
import json
import logging
import os
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional

from phenopacket_ingest.config import PhenopacketStoreConfig
from phenopacket_ingest.registry.downloader import PhenopacketDownloader
from phenopacket_ingest.parser.phenopacket_parser import PhenopacketParser

# Check if ppktstore is available
HAS_PPKTSTORE = False
try:
    from ppktstore.model import PhenopacketStore
    from ppktstore.registry import configure_phenopacket_registry

    HAS_PPKTSTORE = True
except ImportError:
    logging.warning("ppktstore library not available. Using fallback implementations.")


class PhenopacketRegistryService:
    """
    Service for downloading and managing phenopacket data from phenopacket-store.

    This class is responsible for:
    1. Downloading the latest phenopacket-store release
    2. Extracting phenopacket data
    3. Converting it to a JSONL format suitable for transformation
    """

    def __init__(self, data_dir: Optional[Path] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the registry service.

        Args:
            data_dir: Directory to store downloaded phenopackets. If None, uses default.
            logger: Logger for tracking operations
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config = PhenopacketStoreConfig()

        if data_dir is None:
            self.data_dir = Path(self.config.data_dir)
        else:
            self.data_dir = data_dir

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.downloader = PhenopacketDownloader(self.config, self.logger)
        self.parser = PhenopacketParser(self.logger)

        self.registry = None
        if HAS_PPKTSTORE:
            try:
                self.registry = configure_phenopacket_registry(
                    store_dir=self.data_dir
                )
                self.logger.info("Initialized phenopacket registry")
            except Exception as e:
                self.logger.error(f"Error initializing registry: {e}")
                HAS_PPKTSTORE = False
        else:
            self.logger.warning("ppktstore not available. Using fallback implementation.")

    def download_latest_release(self) -> Path:
        """
        Download the latest phenopacket-store release.

        Returns:
            Path to the downloaded ZIP file
        """
        global HAS_PPKTSTORE
        if HAS_PPKTSTORE and self.registry:
            self.logger.info("Downloading latest phenopacket-store release")
            try:
                with self.registry.open_phenopacket_store() as store:
                    # Make sure we have a store name before trying to use it
                    if hasattr(store, 'name') and store.name:
                        self.logger.info(f"Downloaded phenopacket-store release: {store.name}")
                        return self.registry.resolve_registry_path(release=store.name)
                    else:
                        self.logger.warning("Store object has no name attribute or it's empty")
                        return self.downloader.download_from_github(self.data_dir)
            except Exception as e:
                self.logger.error(f"Error downloading with ppktstore: {e}")
                return self.downloader.download_from_github(self.data_dir)
        else:
            return self.downloader.download_from_github(self.data_dir)

    def extract_phenopackets_to_jsonl(self, zip_path: Optional[Path] = None) -> Path:
        """
        Extract phenopacket data from the store and convert to JSONL format for transformation.

        Args:
            zip_path: Path to phenopacket-store ZIP file. If None, uses latest.

        Returns:
            Path to the generated JSONL file
        """
        if zip_path is None:
            zip_path = self.download_latest_release()

        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        jsonl_path = output_dir / "phenopackets.jsonl"

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)

        global HAS_PPKTSTORE
        if HAS_PPKTSTORE:
            try:
                self._extract_with_ppktstore(zip_path, jsonl_path)
            except Exception as e:
                self.logger.error(f"Error extracting with ppktstore: {e}")
                self._extract_directly(zip_path, jsonl_path)
        else:
            self._extract_directly(zip_path, jsonl_path)

        return jsonl_path

    def _extract_with_ppktstore(self, zip_path: Path, jsonl_path: Path) -> None:
        """
        Extract phenopacket data using ppktstore library.

        Args:
            zip_path: Path to phenopacket-store ZIP file
            jsonl_path: Path to output JSONL file
        """
        self.logger.info(f"Extracting phenopacket data from {zip_path} to {jsonl_path}")

        try:
            with zipfile.ZipFile(zip_path) as zf, open(jsonl_path, "w") as f:
                store = PhenopacketStore.from_release_zip(zf)

                for cohort in store.cohorts():
                    cohort_name = getattr(cohort, 'name', 'unknown')
                    self.logger.info(f"Processing cohort: {cohort_name}")

                    for pp_info in cohort.phenopackets:
                        phenopacket = pp_info.phenopacket
                        record_dict = self.parser.phenopacket_to_jsonl_dict(phenopacket, cohort_name)
                        if record_dict:
                            f.write(json.dumps(record_dict) + "\n")
        except Exception as e:
            self.logger.error(f"Error in _extract_with_ppktstore: {e}")
            raise

    def _extract_directly(self, zip_path: Path, jsonl_path: Path) -> None:
        """
        Extract phenopacket data directly from the ZIP file.

        Args:
            zip_path: Path to phenopacket-store ZIP file
            jsonl_path: Path to output JSONL file
        """
        self.logger.info(f"Extracting phenopacket data directly from {zip_path} to {jsonl_path}")

        # Check if phenopackets library is available
        try:
            from phenopackets import Phenopacket as PBPhenopacket
            from google.protobuf.json_format import Parse
        except ImportError:
            self.logger.error("phenopackets library not available, cannot extract data")
            raise ImportError("phenopackets library is required for extraction")

        with zipfile.ZipFile(zip_path) as zf, open(jsonl_path, "w") as f:
            phenopacket_files = [name for name in zf.namelist()
                                 if name.endswith('.json') and not name.startswith('__MACOSX')]

            self.logger.info(f"Found {len(phenopacket_files)} phenopacket files")

            for i, pp_file in enumerate(phenopacket_files):
                if i % 100 == 0:
                    self.logger.info(f"Processing file {i + 1}/{len(phenopacket_files)}")

                # Determine cohort name from file path
                parts = pp_file.split('/')
                cohort_name = parts[0] if len(parts) > 1 else "unknown"

                try:
                    # Read and parse the phenopacket
                    pp_content = zf.read(pp_file).decode('utf-8')
                    phenopacket = Parse(pp_content, PBPhenopacket())

                    # Convert to JSONL record
                    record_dict = self.parser.phenopacket_to_jsonl_dict(phenopacket, cohort_name)
                    if record_dict:
                        f.write(json.dumps(record_dict) + "\n")
                except Exception as e:
                    self.logger.error(f"Error processing {pp_file}: {e}")