"""Configuration for phenopacket-ingest."""
import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class PhenopacketStoreConfig:
    """Configuration settings for phenopacket store."""
    
    data_dir: str = os.path.join(os.path.expanduser("~"), ".phenopacket-store")
    """Directory to store downloaded phenopacket files."""
    
    output_dir: str = "data"
    """Directory for processed output files."""
    
    repo_owner: str = "monarch-initiative"
    repo_name: str = "phenopacket-store"
    release_tag: str = None
    
    def __post_init__(self):
        """Ensure directories exist after initialization."""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)