"""Test the transform functionality for phenopacket-ingest."""
import pytest
from unittest.mock import patch, MagicMock
import sys

mock_koza_app = MagicMock()
with patch('koza.cli_utils.get_koza_app', return_value=mock_koza_app):
    from phenopacket_ingest.transform import PhenopacketTransformer


@pytest.fixture
def example_row():
    """Define an example row from the phenopacket JSONL file."""
    return {
        "gene_symbol": "SCN1A",
        "gene_id": "HGNC:10585",
        "phenopacket_id": "test-phenopacket",
        "subject_id": "patient-001",
        "subject_sex": "FEMALE",
        "disease_id": "MONDO:0005737",
        "disease_label": "Epilepsy",
        "hpo_ids": "HP:0001250,HP:0002353",
        "cohort": "TEST",
        "observed_phenotypes": [
            {"id": "HP:0001250", "label": "Seizure"},
            {"id": "HP:0002353", "label": "EEG abnormality"}
        ],
        "interpretation_status": "CAUSATIVE"
    }


def test_transform_gene(example_row):
    """Test transforming a row into a Gene entity."""
    gene = PhenopacketTransformer.transform_gene(example_row)
    
    assert gene is not None
    assert gene.id == "HGNC:10585"
    assert gene.symbol == "SCN1A"
    assert gene.name == "SCN1A"
    assert gene.in_taxon == ["NCBITaxon:9606"]
    assert gene.in_taxon_label == "Homo sapiens"
    assert gene.provided_by == ["infores:phenopacket-store"]


def test_transform_disease(example_row):
    """Test transforming a row into a Disease entity."""
    disease = PhenopacketTransformer.transform_disease(example_row)
    
    assert disease is not None
    assert disease.id == "MONDO:0005737"
    assert disease.name == "Epilepsy"
    assert disease.provided_by == ["infores:phenopacket-store"]


def test_process_row(example_row):
    """Test processing a row directly using the PhenopacketTransformer."""
    entities = PhenopacketTransformer.process_row(example_row)
    
    assert len(entities) > 0
    
    gene = next((e for e in entities if hasattr(e, 'id') and e.id == "HGNC:10585"), None)
    assert gene is not None
    assert gene.symbol == "SCN1A"
    
    disease = next((e for e in entities if hasattr(e, 'id') and e.id == "MONDO:0005737"), None)
    assert disease is not None
    assert disease.name == "Epilepsy"
    
    gene_disease = next((e for e in entities if hasattr(e, 'subject') and e.subject == "HGNC:10585" and hasattr(e, 'object') and e.object == "MONDO:0005737"), None)
    assert gene_disease is not None
    
    gene_pheno = [e for e in entities if hasattr(e, 'subject') and e.subject == "HGNC:10585" and hasattr(e, 'object') and e.object.startswith("HP:")]
    assert len(gene_pheno) == 2
    
    disease_pheno = [e for e in entities if hasattr(e, 'subject') and e.subject == "MONDO:0005737" and hasattr(e, 'object') and e.object.startswith("HP:")]
    assert len(disease_pheno) == 2


"""
# FUTURE BIOLINK TESTS
# Uncomment these tests when Case entities are available in Biolink model

def test_transform_case(example_row):
    '''Test transforming a row into a Case entity.'''
    # This test will be enabled when Case entity is available in Biolink
    case = PhenopacketTransformer.transform_case(example_row)
    
    assert case is not None
    assert case.id == "CASE:patient-001"
    assert case.sex.id == "PATO:0000383"  # Female
    assert case.sex.name == "Female"
    assert case.provided_by == ["infores:phenopacket-store"]

def test_case_associations(example_row):
    '''Test creating case associations with other entities.'''
    # This test will be enabled when Case entities are available in Biolink
    
    # Mock required IDs
    case_id = "CASE:patient-001"
    disease_id = "MONDO:0005737"
    disease_name = "Epilepsy"
    variant_id = "PPKT:12-12345-A-G"
    gene_id = "HGNC:10585"
    
    # Test case to disease association
    case_disease = PhenopacketTransformer.create_case_to_disease_association(
        case_id=case_id,
        disease_id=disease_id,
        disease_name=disease_name
    )
    
    assert case_disease is not None
    assert case_disease.subject == case_id
    assert case_disease.predicate == "biolink:diagnosed_with"
    assert case_disease.object == disease_id
    
    # Test case to variant association
    case_variant = PhenopacketTransformer.create_case_to_variant_association(
        case_id=case_id,
        variant_id=variant_id,
        interpretation_status="CAUSATIVE"
    )
    
    assert case_variant is not None
    assert case_variant.subject == case_id
    assert case_variant.predicate == "biolink:has_variant"
    assert case_variant.object == variant_id
    
    # Test case to gene association
    case_gene = PhenopacketTransformer.create_case_to_gene_association(
        case_id=case_id,
        gene_id=gene_id
    )
    
    assert case_gene is not None
    assert case_gene.subject == case_id
    assert case_gene.predicate == "biolink:has_gene_variant"
    assert case_gene.object == gene_id
"""