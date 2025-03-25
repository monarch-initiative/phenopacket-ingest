"""Tests for the phenopacket data models."""
import pytest
from phenopacket_ingest.models import (
    OntologyClass,
    Age,
    TimeElement,
    Variant,
    Disease,
    PhenotypicFeature,
    Reference,
    Subject,
    PhenopacketData,
    PhenopacketRecord,
)


def test_phenotypic_feature():
    """Test the PhenotypicFeature model."""
    feature = PhenotypicFeature(
        id="HP:0001250",
        label="Seizure",
    )
    
    assert feature.id == "HP:0001250"
    assert feature.label == "Seizure"
    assert feature.excluded is False
    assert feature.onset is None
    
    feature_with_onset = PhenotypicFeature(
        id="HP:0001250",
        label="Seizure",
        excluded=True,
        onset="P10Y",
    )
    
    assert feature_with_onset.id == "HP:0001250"
    assert feature_with_onset.label == "Seizure"
    assert feature_with_onset.excluded is True
    assert feature_with_onset.onset == "P10Y"


def test_variant():
    """Test the Variant model."""
    variant = Variant(
        gene_symbol="SCN1A",
        gene_id="HGNC:10585",
    )
    
    assert variant.gene_symbol == "SCN1A"
    assert variant.gene_id == "HGNC:10585"
    
    assert variant.id is None
    assert variant.hgvs_expressions == []
    assert variant.genome_assembly is None
    
    variant_full = Variant(
        id="var_12345",
        gene_symbol="SCN1A",
        gene_id="HGNC:10585",
        hgvs_expressions=["NM_001165963.4:c.2447G>A", "NC_000002.12:g.165991235G>A"],
        genome_assembly="GRCh38",
        chromosome="chr2",
        position="165991235",
        reference="G",
        alternate="A",
        zygosity="heterozygous",
    )
    
    assert variant_full.id == "var_12345"
    assert variant_full.gene_symbol == "SCN1A"
    assert variant_full.gene_id == "HGNC:10585"
    assert "NM_001165963.4:c.2447G>A" in variant_full.hgvs_expressions
    assert variant_full.genome_assembly == "GRCh38"
    assert variant_full.position == "165991235"


def test_phenopacket_data():
    """Test the PhenopacketData model."""
    subject = Subject(id="patient1")
    variant = Variant(gene_symbol="SCN1A", gene_id="HGNC:10585")
    
    data = PhenopacketData(
        phenopacket_id="test_id",
        subject=subject,
        cohort="TEST",
        variants=[variant],
    )
    
    assert data.phenopacket_id == "test_id"
    assert data.subject.id == "patient1"
    assert data.cohort == "TEST"
    assert len(data.variants) == 1
    assert data.variants[0].gene_symbol == "SCN1A"
    
    assert data.gene_symbols == ["SCN1A"]
    assert data.gene_ids == ["HGNC:10585"]
    assert data.hpo_ids == []
    
    json_dict = data.to_json_dict()
    assert json_dict["phenopacket_id"] == "test_id"
    assert json_dict["subject_id"] == "patient1"
    assert json_dict["gene_symbol"] == "SCN1A"
    assert json_dict["gene_id"] == "HGNC:10585"


def test_phenopacket_data_with_disease_and_phenotypes():
    """Test PhenopacketData with disease and phenotypes."""
    subject = Subject(id="patient1")
    variant = Variant(gene_symbol="SCN1A", gene_id="HGNC:10585")
    disease = Disease(id="MONDO:0005737", label="Epilepsy")
    observed_phenotypes = [
        PhenotypicFeature(id="HP:0001250", label="Seizure"),
        PhenotypicFeature(id="HP:0001251", label="Ataxia"),
    ]
    
    data = PhenopacketData(
        phenopacket_id="test_id",
        subject=subject,
        cohort="TEST",
        variants=[variant],
        disease=disease,
        observed_phenotypes=observed_phenotypes,
    )
    
    assert data.disease.id == "MONDO:0005737"
    assert data.disease.label == "Epilepsy"
    
    assert len(data.observed_phenotypes) == 2
    assert data.hpo_ids == ["HP:0001250", "HP:0001251"]
    
    json_dict = data.to_json_dict()
    assert json_dict["disease_id"] == "MONDO:0005737"
    assert json_dict["disease_label"] == "Epilepsy"
    assert len(json_dict["observed_phenotypes"]) == 2