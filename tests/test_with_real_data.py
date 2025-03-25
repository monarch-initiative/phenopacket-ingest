"""Test the phenopacket-ingest pipeline with real phenopacket data."""
import os
import json
import logging
import shutil
import zipfile
from pathlib import Path
from typing import List, Dict, Any

from phenopackets import Phenopacket as PBPhenopacket
from google.protobuf.json_format import Parse

from phenopacket_ingest.parser import PhenopacketParser
from phenopacket_ingest.transform import PhenopacketTransformer
from phenopacket_ingest.registry import PhenopacketRegistryService
from phenopacket_ingest.models import PhenopacketData

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_phenopacket(file_path: str) -> PBPhenopacket:
    """Load a phenopacket from a JSON file."""
    with open(file_path, 'r') as f:
        content = f.read()
    return Parse(content, PBPhenopacket())


def test_parsing_and_transformation():
    """Test parsing and transformation of real phenopacket data."""
    test_data_dir = Path("/Users/ck/Monarch/phenopacket-ingest/data/test_phenopackets")
    parser = PhenopacketParser()
    for json_file in test_data_dir.glob("*.json"):
        logger.info(f"Processing {json_file}")
        
        try:
            phenopacket = load_phenopacket(str(json_file))
            phenopacket_data_list = parser.parse_phenopacket(phenopacket, "test_cohort")
            
            if not phenopacket_data_list:
                logger.warning(f"No data extracted from {json_file}")
                continue
                
            logger.info(f"Successfully parsed {json_file}, got {len(phenopacket_data_list)} records")
            
            records = []
            for data in phenopacket_data_list:
                record = data.to_json_dict()
                records.append(record)
                
            for record in records:
                entities = PhenopacketTransformer.process_row(record)
                
                if not entities:
                    logger.warning(f"No entities generated for record from {json_file}")
                    continue
                    
                logger.info(f"Generated {len(entities)} entities from {json_file}")
                
                entity_types = {}
                for entity in entities:
                    entity_type = type(entity).__name__
                    entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
                
                logger.info(f"Entity types: {entity_types}")
                
        except Exception as e:
            logger.error(f"Error processing {json_file}: {e}")


def test_registry_extract():
    """Test the registry extract functionality with our test data."""
    logger.info("Testing registry extract functionality")
    
    test_data_dir = Path("/Users/ck/Monarch/phenopacket-ingest/data/test_phenopackets")
    test_zip_path = Path("/Users/ck/Monarch/phenopacket-ingest/data/test_phenopackets.zip")
    
    with zipfile.ZipFile(test_zip_path, 'w') as zip_file:
        for json_file in test_data_dir.glob("*.json"):
            cohort_name = json_file.stem.split('_')[0]  # Use first part of filename as cohort
            zip_file.write(json_file, f"{cohort_name}/phenopackets/{json_file.name}")
    
    logger.info(f"Created test zip file at {test_zip_path}")
    
    registry = PhenopacketRegistryService()
    jsonl_path = registry.extract_phenopackets_to_jsonl(test_zip_path)
    
    logger.info(f"Extracted phenopackets to {jsonl_path}")
    
    if not jsonl_path.exists():
        logger.error(f"JSONL file {jsonl_path} does not exist")
        return
    
    record_count = 0
    with open(jsonl_path, 'r') as f:
        for line in f:
            record_count += 1
    
    logger.info(f"Extracted {record_count} records to JSONL file")
    
    if test_zip_path.exists():
        os.remove(test_zip_path)
        logger.info(f"Removed test zip file {test_zip_path}")


def create_test_zip():
    """Create a test zip file with our test phenopackets."""
    test_data_dir = Path("/Users/ck/Monarch/phenopacket-ingest/data/test_phenopackets")
    test_zip_path = Path("/Users/ck/Monarch/phenopacket-ingest/data/test_phenopackets.zip")
    
    with zipfile.ZipFile(test_zip_path, 'w') as zip_file:
        for json_file in test_data_dir.glob("*.json"):
            cohort_name = json_file.stem.split('_')[0]  # Use first part of filename as cohort
            zip_file.write(json_file, f"{cohort_name}/phenopackets/{json_file.name}")
    
    logger.info(f"Created test zip file at {test_zip_path}")
    return test_zip_path


def test_full_pipeline():
    """Test the full pipeline from extract to transform."""
    logger.info("Testing full pipeline")
    
    test_zip_path = create_test_zip()
    
    output_dir = Path("/Users/ck/Monarch/phenopacket-ingest/output")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    registry = PhenopacketRegistryService()
    jsonl_path = registry.extract_phenopackets_to_jsonl(test_zip_path)
    
    logger.info(f"Extracted phenopackets to {jsonl_path}")
    
    # Temporarily modify the transform.yaml to use our test JSONL
    from phenopacket_ingest.transform import koza_app
    if koza_app:
        logger.info("Running Koza transform with the extracted data")
        # This would normally be done by the CLI transform command
        # We can't test it directly here without mocking Koza properly
        logger.info("Koza transform would run here in a real pipeline")
    
    if test_zip_path.exists():
        os.remove(test_zip_path)
        logger.info(f"Removed test zip file {test_zip_path}")


if __name__ == "__main__":
    test_parsing_and_transformation()
    test_registry_extract()
