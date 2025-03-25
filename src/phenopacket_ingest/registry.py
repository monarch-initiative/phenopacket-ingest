"""
Registry module for downloading and managing phenopacket data.
"""
import json
import logging
import os
import re
import ssl
import typing
import zipfile
from pathlib import Path
from urllib.request import urlopen
import certifi
import sys

HAS_PHENOPACKETS = False
HAS_PPKTSTORE = False

try:
    from phenopackets import Phenopacket as PBPhenopacket
    from google.protobuf.json_format import Parse
    HAS_PHENOPACKETS = True
except ImportError:
    logging.warning("phenopackets library not available. Functionality will be limited.")

try:
    from ppktstore.model import PhenopacketStore
    from ppktstore.registry import configure_phenopacket_registry
    HAS_PPKTSTORE = True
except ImportError:
    logging.warning("ppktstore library not available. Using fallback implementations.")

from phenopacket_ingest.config import PhenopacketStoreConfig
from phenopacket_ingest.parser import parser  # Import our parser


SEMVER_VERSION_PT = re.compile(
    r"v?(?P<major>\d+)(\.(?P<minor>\d+))?(\.(?P<patch>\d+))?"
)


class PhenopacketRegistryService:
    """
    Service for downloading and managing phenopacket data from phenopacket-store.
    
    This class is responsible for:
    1. Downloading the latest phenopacket-store release
    2. Extracting phenopacket data
    3. Converting it to a JSONL format suitable for Koza transformation
    """
    
    def __init__(self, data_dir: Path = None):
        """
        Initialize the registry service.
        
        Args:
            data_dir: Directory to store downloaded phenopackets. If None, uses default.
        """
        self.logger = logging.getLogger(__name__)
        self.config = PhenopacketStoreConfig()
        
        if data_dir is None:
            self.data_dir = Path(self.config.data_dir)
        else:
            self.data_dir = data_dir
            
        self.data_dir.mkdir(parents=True, exist_ok=True)

        global HAS_PPKTSTORE
        if HAS_PPKTSTORE:
            try:
                self.registry = configure_phenopacket_registry(
                    store_dir=self.data_dir
                )
                self.logger.info("Initialized phenopacket registry")
            except Exception as e:
                self.logger.error(f"Error initializing registry: {e}")
                self.registry = None
                HAS_PPKTSTORE = False
        else:
            self.logger.warning("ppktstore not available. Using fallback implementation.")
            self.registry = None
    
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
                        return self._fallback_download_latest_release()
            except Exception as e:
                self.logger.error(f"Error downloading with ppktstore: {e}")
                return self._fallback_download_latest_release()
        else:
            return self._fallback_download_latest_release()
    
    def _fallback_download_latest_release(self) -> Path:
        """
        Fallback implementation for downloading phenopacket-store if ppktstore is not available.
        
        Returns:
            Path to the downloaded ZIP file
        """
        self.logger.info("Using fallback download implementation")
        ctx = ssl.create_default_context(cafile=certifi.where())
        
        tag_api_url = f"https://api.github.com/repos/{self.config.repo_owner}/{self.config.repo_name}/tags"
        self.logger.debug(f"Fetching tags from {tag_api_url}")
        
        try:
            with urlopen(tag_api_url, timeout=10.0, context=ctx) as fh:
                tags = json.load(fh)
            
            if len(tags) == 0:
                raise ValueError("No tags could be fetched from GitHub tag API")
            
            latest_tag = None
            latest_components = None
            
            for tag in tags:
                tag_name = tag["name"]
                matcher = SEMVER_VERSION_PT.match(tag_name)
                if matcher is not None:
                    major = int(matcher.group("major"))
                    minor = int(matcher.group("minor")) if matcher.group("minor") is not None else 0
                    patch = int(matcher.group("patch")) if matcher.group("patch") is not None else 0
                    current = (major, minor, patch)
                    
                    if latest_components is None or current > latest_components:
                        latest_components = current
                        latest_tag = tag_name
                else:
                    self.logger.warning(f'Skipping release tag {tag_name} that does not match semantic versioning')
            
            if latest_tag is None:
                raise ValueError("Could not determine latest release tag")
            
            release_tag = self.config.release_tag or latest_tag
            
            release_url = f"https://github.com/{self.config.repo_owner}/{self.config.repo_name}/releases/download/{release_tag}/all_phenopackets.zip"
            self.logger.info(f"Downloading phenopacket-store from {release_url}")
            
            zip_file_path = self.data_dir / f"{release_tag}.zip"
            os.makedirs(os.path.dirname(zip_file_path), exist_ok=True)
            
            with urlopen(release_url, timeout=30.0, context=ctx) as response, open(zip_file_path, "wb") as fh:
                fh.write(response.read())
            
            self.logger.info(f"Downloaded phenopacket-store release {release_tag} to {zip_file_path}")
            return zip_file_path
            
        except Exception as e:
            self.logger.error(f"Error downloading phenopacket-store: {e}")
            raise
    
    def extract_phenopackets_to_jsonl(self, zip_path: Path = None) -> Path:
        """
        Extract phenopacket data from the store and convert to JSONL format for transformation.
        
        Args:
            zip_path: Path to phenopacket-store ZIP file. If None, uses latest.
            
        Returns:
            Path to the generated JSONL file
        """
        if zip_path is None:
            zip_path = self.download_latest_release()


        jsonl_path = Path(self.config.output_dir) / "phenopacket_genes.jsonl"
        
        global HAS_PPKTSTORE, HAS_PHENOPACKETS
        if HAS_PPKTSTORE and HAS_PHENOPACKETS:
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
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)
        
        try:
            with zipfile.ZipFile(zip_path) as zf, open(jsonl_path, "w") as f:
                store = PhenopacketStore.from_release_zip(zf)
                
                for cohort in store.cohorts():
                    # Check for cohort name before using it
                    cohort_name = getattr(cohort, 'name', 'unknown')
                    self.logger.info(f"Processing cohort: {cohort_name}")
                    
                    for pp_info in cohort.phenopackets:
                        phenopacket = pp_info.phenopacket
                        self._process_phenopacket(phenopacket, f, cohort_name)
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
        
        global HAS_PHENOPACKETS
        if not HAS_PHENOPACKETS:
            self.logger.error("phenopackets library not available, cannot extract data")
            raise ImportError("phenopackets library is required for extraction")
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)
        
        with zipfile.ZipFile(zip_path) as zf, open(jsonl_path, "w") as f:
            phenopacket_files = [name for name in zf.namelist()
                               if name.endswith('.json') and not name.startswith('__MACOSX')]
            
            for pp_file in phenopacket_files:
                self.logger.debug(f"Processing phenopacket: {pp_file}")
                
                parts = pp_file.split('/')
                if len(parts) > 1:
                    cohort_name = parts[0]
                else:
                    cohort_name = "unknown"
                
                try:
                    pp_content = zf.read(pp_file).decode('utf-8')
                    phenopacket = Parse(pp_content, PBPhenopacket())
                    self._process_phenopacket(phenopacket, f, cohort_name)
                except Exception as e:
                    self.logger.error(f"Error processing {pp_file}: {e}")
    
    def _process_phenopacket(self, phenopacket: 'PBPhenopacket', output_file: typing.TextIO, cohort_name: str) -> None:
        """
        Process a single phenopacket and write gene-disease-phenotype associations to JSONL.
        
        Args:
            phenopacket: The phenopacket to process
            output_file: The output file to write to
            cohort_name: The name of the cohort
        """
        try:
            phenopacket_data_list = parser.parse_phenopacket(phenopacket, cohort_name)
            if phenopacket_data_list is not None:
                for data in phenopacket_data_list:
                    record_dict = data.to_json_dict()
                    output_file.write(json.dumps(record_dict) + "\n")
        except Exception as e:
            self.logger.error(f"Error processing phenopacket {phenopacket.id}: {e}")


class PhenopacketTransformer:
    """Class for transforming phenopacket data into a format suitable for Koza."""
    
    @staticmethod
    def prepare_for_transform() -> Path:
        """
        Prepare phenopacket data for transformation.
        
        Returns:
            Path to the JSONL file ready for Koza transformation
        """
        registry = PhenopacketRegistryService()
        return registry.extract_phenopackets_to_jsonl()