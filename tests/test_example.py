"""
A basic test file that tests core functionality without depending on Koza mock utilities.
"""

import pytest
from unittest.mock import patch, MagicMock

mock_app = MagicMock()
mock_app.get_row.return_value = None  # Default behavior, no rows to process
patch('koza.cli_utils.get_koza_app', return_value=mock_app).start()

from phenopacket_ingest.transform import PhenopacketTransformer


def test_gene_transform():
    """Test the gene transformation function."""
    test_row = {
        "gene_symbol": "SCN1A",
        "gene_id": "HGNC:10585"
    }
    
    gene = PhenopacketTransformer.transform_gene(test_row)
    
    assert gene is not None
    assert gene.id == "HGNC:10585"
    assert gene.symbol == "SCN1A"


def test_disease_transform():
    """Test the disease transformation function."""
    test_row = {
        "disease_id": "MONDO:0005737",
        "disease_label": "Epilepsy"
    }
    
    disease = PhenopacketTransformer.transform_disease(test_row)
    
    assert disease is not None
    assert disease.id == "MONDO:0005737"
    assert disease.name == "Epilepsy"


def test_variant_transform():
    """Test the variant transformation function."""
    test_row = {
        "gene_id": "HGNC:10585",
        "variant_id": "CLINVAR:123456",
        "chromosome": "chr2",
        "position": "165991235",
        "reference": "G",
        "alternate": "A",
        "variant_hgvs": ["NM_001165963.4:c.2447G>A"]
    }
    
    variant = PhenopacketTransformer.transform_variant(test_row)
    
    assert variant is not None
    assert variant.id == "CLINVAR:123456"
    assert variant.has_gene == ["HGNC:10585"]
    assert variant.xref == ["NM_001165963.4:c.2447G>A"]


def test_process_row():
    """Test processing a complete row."""
    test_row = {
        "gene_symbol": "SCN1A",
        "gene_id": "HGNC:10585",
        "phenopacket_id": "test-phenopacket",
        "disease_id": "MONDO:0005737",
        "disease_label": "Epilepsy",
        "observed_phenotypes": [
            {"id": "HP:0001250", "label": "Seizure"},
            {"id": "HP:0002353", "label": "EEG abnormality"}
        ]
    }
    
    entities = PhenopacketTransformer.process_row(test_row)
    
    assert len(entities) > 0
    gene = next((e for e in entities if hasattr(e, 'id') and e.id == "HGNC:10585"), None)
    assert gene is not None
    
    disease = next((e for e in entities if hasattr(e, 'id') and e.id == "MONDO:0005737"), None)
    assert disease is not None
    association = next((e for e in entities if hasattr(e, 'subject') and hasattr(e, 'object')), None)
    assert association is not None