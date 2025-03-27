"""
Phenopacket Ingest - A system for processing phenopacket data to knowledge graphs.

This package provides tools for:
1. Downloading phenopacket data from repositories
2. Parsing phenopacket protocol buffer files
3. Converting to JSONL format
4. Transforming to Biolink model entities
"""

__version__ = "0.1.0"

# Import main classes for easier access

from phenopacket_ingest.registry.registry_service import PhenopacketRegistryService
from phenopacket_ingest.parser.phenopacket_parser import PhenopacketParser
from phenopacket_ingest.parser.phenopacket_extractor import PhenopacketExtractor
from phenopacket_ingest.transformer.phenopacket_transformer import PhenopacketTransformer

__all__ = [
    "PhenopacketRegistryService",
    "PhenopacketParser",
    "PhenopacketExtractor",
    "PhenopacketTransformer",
]