"""Tests for phenopacket registry module."""
import os
import pytest
from pathlib import Path
import tempfile
import zipfile
import json
import sys

# Mock the flags before importing
import phenopacket_ingest.registry
setattr(phenopacket_ingest.registry, 'HAS_PPKTSTORE', False)
setattr(phenopacket_ingest.registry, 'HAS_PHENOPACKETS', False)

from phenopacket_ingest.registry import PhenopacketRegistryService


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_phenopacket_zip(temp_dir):
    """Create a mock phenopacket store zip file for testing."""
    phenopacket_json = {
        "id": "test-phenopacket",
        "subject": {
            "id": "test-subject"
        },
        "phenotypicFeatures": [
            {
                "type": {
                    "id": "HP:0001250",
                    "label": "Seizure"
                }
            }
        ],
        "interpretations": [
            {
                "id": "test-interpretation",
                "diagnosis": {
                    "disease": {
                        "id": "MONDO:0005737",
                        "label": "Epilepsy"
                    },
                    "genomicInterpretations": [
                        {
                            "gene": {
                                "symbol": "SCN1A",
                                "value_id": "HGNC:10585"
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    cohort_dir = temp_dir / "TEST"
    cohort_dir.mkdir()
    
    pp_path = cohort_dir / "test_phenopacket.json"
    with open(pp_path, "w") as f:
        json.dump(phenopacket_json, f)
    
    zip_path = temp_dir / "test_phenopackets.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(pp_path, arcname=str(pp_path.relative_to(temp_dir)))
    
    return zip_path


def test_extract_phenopackets(temp_dir, mock_phenopacket_zip, monkeypatch):
    """Test extracting phenopackets to JSONL."""
    import phenopacket_ingest.registry
    monkeypatch.setattr(phenopacket_ingest.registry, "HAS_PHENOPACKETS", True)
    def mock_download(*args, **kwargs):
        return mock_phenopacket_zip
    
    def mock_extract_directly(self, zip_path, jsonl_path):
        """Mock implementation that just writes a test record."""
        os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)
        with open(jsonl_path, "w") as f:
            test_record = {
                "phenopacket_id": "test-phenopacket",
                "subject_id": "test-subject",
                "gene_symbol": "SCN1A",
                "gene_id": "HGNC:10585",
                "disease_id": "MONDO:0005737",
                "disease_label": "Epilepsy",
                "hpo_ids": ["HP:0001250"],
                "observed_phenotypes": [{"id": "HP:0001250", "label": "Seizure"}],
                "cohort": "TEST"
            }
            f.write(json.dumps(test_record) + "\n")

    registry = PhenopacketRegistryService(data_dir=temp_dir)
    monkeypatch.setattr(registry, "download_latest_release", mock_download)
    monkeypatch.setattr(registry, "_extract_directly", mock_extract_directly)
    
    jsonl_path = registry.extract_phenopackets_to_jsonl()
    print("\n\n")
    print(jsonl_path)
    print("\n\n")

    assert jsonl_path.exists()
    
    with open(jsonl_path, "r") as f:
        lines = f.readlines()
        assert len(lines) > 0
        
        record = json.loads(lines[0])
        assert record["gene_symbol"] == "SCN1A"
        assert record["gene_id"] == "HGNC:10585"
        assert record["disease_id"] == "MONDO:0005737"
        assert record["disease_label"] == "Epilepsy"
        assert "HP:0001250" in record["hpo_ids"]