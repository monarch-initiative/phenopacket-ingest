"""Test parsing individual entities from a phenopacket."""

import json

import pytest

from phenopacket_ingest.models import PhenopacketRecord
from phenopacket_ingest.parser.phenopacket_parser import PhenopacketParser
from phenopacket_ingest.transformer.phenopacket_transformer import PhenopacketTransformer

COMPLETE_PHENOPACKET = {
    "id": "phenopacket.test.1",
    "subject": {
        "id": "patient:1",
        "alternate_ids": ["alt:1", "alt:2"],
        "sex": "FEMALE",
        "time_at_last_encounter": {"age": {"iso8601duration": "P42Y"}},
        "taxonomy": {"id": "NCBITaxon:9606", "label": "Homo sapiens"},
    },
    "phenotypic_features": [
        {
            "type": {"id": "HP:0001250", "label": "Seizure"},
            "excluded": False,
            "severity": {"id": "HP:0012828", "label": "Severe"},
            "modifiers": [{"id": "HP:0032224", "label": "Worsened by febrile illness"}],
            "onset": {"age": {"iso8601duration": "P2Y6M"}},
            "evidence": [
                {
                    "evidence_code": {"id": "ECO:0000033", "label": "traceable author statement"},
                    "reference": {"id": "PMID:30566666", "description": "Publication describing the case"},
                }
            ],
        },
        {"type": {"id": "HP:0001263", "label": "Developmental delay"}, "excluded": False},
        {"type": {"id": "HP:0000252", "label": "Microcephaly"}, "excluded": True},
    ],
    "diseases": [
        {
            "term": {"id": "MONDO:0100038", "label": "KCNT1-related epilepsy"},
            "excluded": False,
            "onset": {"age": {"iso8601duration": "P2Y"}},
            "disease_stage": [{"id": "NCIT:C28554", "label": "Early Stage"}],
            "clinical_tnm_finding": [{"id": "NCIT:C48232", "label": "T2 Stage Finding"}],
        }
    ],
    "biosamples": [
        {
            "id": "biosample:1",
            "individual_id": "patient:1",
            "derived_from_id": "biosample:parent",
            "description": "Blood sample",
            "sampled_tissue": {"id": "UBERON:0000178", "label": "Blood"},
            "time_of_collection": {"age": {"iso8601duration": "P3Y"}},
            "histological_diagnosis": {"id": "NCIT:C38757", "label": "Normal"},
            "tumor_progression": {"id": "NCIT:C84509", "label": "Primary Malignant Neoplasm"},
            "tumor_grade": {"id": "NCIT:C28076", "label": "Grade 2"},
            "diagnostic_markers": [{"id": "NCIT:C13951", "label": "CD19"}],
        }
    ],
    "measurements": [
        {
            "description": "Blood pressure measurement",
            "assay": {"id": "LOINC:8462-4", "label": "Diastolic blood pressure"},
            "value": {"quantity": {"value": 80, "unit": {"id": "UCUM:mm[Hg]", "label": "mmHg"}}},
        }
    ],
    "interpretations": [
        {
            "id": "interpretation.1",
            "progress_status": "SOLVED",
            "diagnosis": {
                "disease": {"id": "MONDO:0100038", "label": "KCNT1-related epilepsy"},
                "genomic_interpretations": [
                    {
                        "subject_or_biosample_id": "patient:1",
                        "interpretation_status": "CAUSATIVE",
                        "gene": {"value_id": "HGNC:18865", "symbol": "KCNT1"},
                        "variant_interpretation": {
                            "acmg_pathogenicity_classification": "PATHOGENIC",
                            "therapeutic_actionability": "ACTIONABLE",
                            "variation_descriptor": {
                                "id": "variant:1",
                                "gene_context": {"value_id": "HGNC:18865", "symbol": "KCNT1"},
                                "vcf_record": {
                                    "genome_assembly": "GRCh38",
                                    "chrom": "9",
                                    "pos": "138650634",
                                    "ref": "C",
                                    "alt": "G",
                                },
                                "expressions": [
                                    {"syntax": "HGVS", "value": "NM_020822.2:c.2800G>A"},
                                    {"syntax": "HGVS.p", "value": "NP_065873.2:p.Ala934Thr"},
                                ],
                                "allelic_state": {"id": "GENO:0000135", "label": "heterozygous"},
                            },
                        },
                    }
                ],
            },
        }
    ],
    "medical_actions": [
        {
            "treatment": {
                "agent": {"id": "CHEBI:6801", "label": "Ketogenic diet"},
                "route_of_administration": {"id": "CHEBI:70989", "label": "Oral"},
            },
            "treatment_intent": {"id": "HP:0025265", "label": "Seizure management"},
            "adverse_events": [{"id": "HP:0031273", "label": "Gastrointestinal disorder"}],
        }
    ],
    "files": [
        {
            "uri": "file:///data/genomes/patient1.vcf.gz",
            "file_format": "VCF",
        }
    ],
    "meta_data": {
        "created": "2022-03-10T11:34:42Z",
        "created_by": "Dr. Jane Smith",
        "submitted_by": "Hospital X",
        "phenopacket_schema_version": "2.0",
        "external_references": [
            {"id": "PMID:33146646", "description": "Article describing the case"},
            {"id": "PMID:32489073", "description": "Review of KCNT1-related epilepsy"},
        ],
    },
    "cohort": "Epilepsy Study",
}


@pytest.fixture
def phenopacket_record():
    """Create a PhenopacketRecord from the complete phenopacket."""
    parser = PhenopacketParser()
    record = parser.parse_from_json(json.dumps(COMPLETE_PHENOPACKET))
    print(record)
    return PhenopacketRecord.model_validate(record)


def test_subject_parsing(phenopacket_record):
    """Test parsing subject information."""
    subject = phenopacket_record.subject

    assert subject.id == "patient:1"
    assert len(subject.alternate_ids) == 2
    assert "alt:1" in subject.alternate_ids

    assert subject.sex == "FEMALE"

    assert subject.time_at_last_encounter is not None
    assert subject.time_at_last_encounter.age is not None
    assert subject.time_at_last_encounter.age_value == "P42Y"

    assert subject.taxonomy is not None
    assert subject.taxonomy.id == "NCBITaxon:9606"
    assert subject.taxonomy.label == "Homo sapiens"


def test_phenotypic_features_parsing(phenopacket_record):
    """Test parsing phenotypic features."""
    features = phenopacket_record.phenotypic_features

    assert len(features) == 3

    seizure = [f for f in features if f.type.id == "HP:0001250"][0]
    assert seizure.type.label == "Seizure"
    assert not seizure.excluded
    assert seizure.severity is not None
    assert seizure.severity.id == "HP:0012828"
    assert len(seizure.modifiers) == 1
    assert seizure.modifiers[0].id == "HP:0032224"
    assert seizure.onset is not None
    assert seizure.onset.age is not None
    assert seizure.onset.age.iso8601duration == "P2Y6M"
    assert len(seizure.evidence) == 1
    assert seizure.evidence[0].evidence_code.id == "ECO:0000033"

    dev_delay = [f for f in features if f.type.id == "HP:0001263"][0]
    assert dev_delay.type.label == "Developmental delay"
    assert not dev_delay.excluded

    microcephaly = [f for f in features if f.type.id == "HP:0000252"][0]
    assert microcephaly.type.label == "Microcephaly"
    assert microcephaly.excluded


def test_disease_parsing(phenopacket_record):
    """Test parsing disease information."""
    diseases = phenopacket_record.diseases

    assert len(diseases) == 1

    disease = diseases[0]
    assert disease.term.id == "MONDO:0100038"
    assert disease.term.label == "KCNT1-related epilepsy"
    assert not disease.excluded
    assert disease.onset is not None
    assert disease.onset.age is not None
    assert disease.onset.age.iso8601duration == "P2Y"
    assert len(disease.disease_stage) == 1
    assert disease.disease_stage[0].id == "NCIT:C28554"
    assert len(disease.clinical_tnm_finding) == 1
    assert disease.clinical_tnm_finding[0].id == "NCIT:C48232"


def test_biosample_parsing(phenopacket_record):
    """Test parsing biosample information."""
    biosamples = phenopacket_record.biosamples

    assert len(biosamples) == 1

    biosample = biosamples[0]
    assert biosample.id == "biosample:1"
    assert biosample.individual_id == "patient:1"
    assert biosample.derived_from_id == "biosample:parent"
    assert biosample.description == "Blood sample"
    assert biosample.sampled_tissue.id == "UBERON:0000178"
    assert biosample.sampled_tissue.label == "Blood"
    assert biosample.time_of_collection.age.iso8601duration == "P3Y"
    assert biosample.histological_diagnosis.id == "NCIT:C38757"
    assert biosample.tumor_progression.id == "NCIT:C84509"
    assert biosample.tumor_grade.id == "NCIT:C28076"
    assert len(biosample.diagnostic_markers) == 1
    assert biosample.diagnostic_markers[0].id == "NCIT:C13951"


def test_measurement_parsing(phenopacket_record):
    """Test parsing measurement information."""
    measurements = phenopacket_record.measurements

    assert len(measurements) == 1

    measurement = measurements[0]
    assert measurement.description == "Blood pressure measurement"
    assert measurement.assay.id == "LOINC:8462-4"
    assert measurement.assay.label == "Diastolic blood pressure"
    assert measurement.value.quantity.value == 80
    assert measurement.value.quantity.unit.id == "UCUM:mm[Hg]"
    assert measurement.value.quantity.unit.label == "mmHg"


def test_interpretation_parsing(phenopacket_record):
    """Test parsing interpretation information."""
    interpretations = phenopacket_record.interpretations

    assert len(interpretations) == 1

    interpretation = interpretations[0]
    assert interpretation["id"] == "interpretation.1"
    assert interpretation["progress_status"] == "SOLVED"
    assert interpretation["diagnosis"]["disease"]["id"] == "MONDO:0100038"

    genomic_interpretations = interpretation["diagnosis"]["genomic_interpretations"]
    assert len(genomic_interpretations) == 1

    gi = genomic_interpretations[0]
    assert gi["subject_or_biosample_id"] == "patient:1"
    assert gi["interpretation_status"] == "CAUSATIVE"
    assert gi["gene"]["value_id"] == "HGNC:18865"
    assert gi["gene"]["symbol"] == "KCNT1"

    vi = gi["variant_interpretation"]
    assert vi["acmg_pathogenicity_classification"] == "PATHOGENIC"
    assert vi["therapeutic_actionability"] == "ACTIONABLE"

    vd = vi["variation_descriptor"]
    assert vd["id"] == "variant:1"
    assert vd["gene_context"]["value_id"] == "HGNC:18865"
    assert vd["gene_context"]["symbol"] == "KCNT1"

    vcf = vd["vcf_record"]
    assert vcf["genome_assembly"] == "GRCh38"
    assert vcf["chrom"] == "9"
    assert vcf["pos"] == "138650634"
    assert vcf["ref"] == "C"
    assert vcf["alt"] == "G"

    expressions = vd["expressions"]
    assert len(expressions) == 2
    assert expressions[0]["value"] == "NM_020822.2:c.2800G>A"
    assert expressions[1]["value"] == "NP_065873.2:p.Ala934Thr"

    assert vd["allelic_state"]["id"] == "GENO:0000135"
    assert vd["allelic_state"]["label"] == "heterozygous"


def test_medical_action_parsing(phenopacket_record):
    """Test parsing medical action information."""
    medical_actions = phenopacket_record.medical_actions

    assert len(medical_actions) == 1

    action = medical_actions[0]
    assert action.treatment.agent.id == "CHEBI:6801"
    assert action.treatment.agent.label == "Ketogenic diet"
    assert action.treatment.route_of_administration.id == "CHEBI:70989"
    assert action.treatment_intent.id == "HP:0025265"
    assert len(action.adverse_events) == 1
    assert action.adverse_events[0].id == "HP:0031273"


def test_file_parsing(phenopacket_record):
    """Test parsing file information."""
    files = phenopacket_record.files

    assert len(files) == 1

    # File
    file = files[0]
    assert file.uri == "file:///data/genomes/patient1.vcf.gz"
    assert file.file_format == "VCF"


def test_metadata_parsing(phenopacket_record):
    """Test parsing metadata information."""
    metadata = phenopacket_record.meta_data

    assert metadata.created == "2022-03-10T11:34:42Z"
    assert metadata.created_by == "Dr. Jane Smith"
    assert metadata.submitted_by == "Hospital X"
    assert metadata.phenopacket_schema_version == "2.0"

    assert len(metadata.external_references) == 2
    assert metadata.external_references[0].id == "PMID:33146646"
    assert metadata.external_references[1].id == "PMID:32489073"


def test_pmids_extraction(phenopacket_record):
    """Test extraction of PMIDs."""
    pmids = phenopacket_record.pmids

    assert len(pmids) == 2
    assert "PMID:33146646" in pmids
    assert "PMID:32489073" in pmids


def test_genes_extraction(phenopacket_record):
    """Test extraction of genes."""
    genes = phenopacket_record.genes

    assert len(genes) == 1
    assert genes[0]["id"] == "HGNC:18865"
    assert genes[0]["symbol"] == "KCNT1"
    assert genes[0]["interpretation_status"] == "CAUSATIVE"


def test_variants_extraction(phenopacket_record):
    """Test extraction of variants."""
    variants = phenopacket_record.variants

    assert len(variants) == 1
    assert variants[0].id == "variant:1"
    assert variants[0].gene_symbol == "KCNT1"
    assert variants[0].gene_id == "HGNC:18865"
    assert variants[0].vcf_record.genome_assembly == "GRCh38"
    assert variants[0].vcf_record.chrom == "9"
    assert variants[0].vcf_record.pos == "138650634"
    assert variants[0].vcf_record.ref == "C"
    assert variants[0].vcf_record.alt == "G"
    assert len(variants[0].hgvs_expressions) == 2
    assert "NM_020822.2:c.2800G>A" in variants[0].hgvs_expressions
    assert variants[0].zygosity == "heterozygous"


def test_phenotypes_extraction(phenopacket_record):
    """Test extraction of observed phenotypes."""
    observed = phenopacket_record.phenotypic_features
    assert len(observed) == 3


def test_biolink_entity_generation(phenopacket_record):
    """Test generation of Biolink entities."""
    entities = PhenopacketTransformer.process_record(phenopacket_record)
    assert len(entities) > 0
    entity_types = [type(e).__name__ for e in entities]
    type_counts = {}
    for entity_type in entity_types:
        type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
    # We should have:
    # - 1 Case
    # - 3 CaseToPhenotypicFeatureAssociation (incl. negated)
    # - 1 CaseToDiseaseAssociation
    # - 1 CaseToGeneAssociation
    # - 1 CaseToVariantAssociation
    case_count = sum(1 for t in entity_types if t == "Case" or (isinstance(t, str) and "case" in t.lower()))
    phenotype_assoc_count = sum(1 for t in entity_types if "Phenotypic" in t)
    disease_assoc_count = sum(1 for t in entity_types if "Disease" in t)
    gene_assoc_count = sum(1 for t in entity_types if "Gene" in t)
    variant_assoc_count = sum(1 for t in entity_types if "Variant" in t)

    assert case_count == 7, f"Expected 6 Case, got {case_count} ({type_counts})"
    assert (
        phenotype_assoc_count == 3
    ), f"Expected 2 CaseToPhenotypicFeatureAssociation, got {phenotype_assoc_count} ({type_counts})"
    assert disease_assoc_count == 1, f"Expected 1 CaseToDiseaseAssociation, got {disease_assoc_count} ({type_counts})"
    assert gene_assoc_count == 1, f"Expected 1 CaseToGeneAssociation, got {gene_assoc_count} ({type_counts})"
    assert variant_assoc_count == 1, f"Expected 1 CaseToVariantAssociation, got {variant_assoc_count} ({type_counts})"


if __name__ == "__main__":
    parser = PhenopacketParser()
    record = parser.parse_from_json(json.dumps(COMPLETE_PHENOPACKET))
    phenopacket_record = PhenopacketRecord.model_validate(record)

    test_subject_parsing(phenopacket_record)
    test_phenotypic_features_parsing(phenopacket_record)
    test_disease_parsing(phenopacket_record)
    test_biosample_parsing(phenopacket_record)
    test_measurement_parsing(phenopacket_record)
    test_interpretation_parsing(phenopacket_record)
    test_medical_action_parsing(phenopacket_record)
    test_file_parsing(phenopacket_record)
    test_metadata_parsing(phenopacket_record)
    test_pmids_extraction(phenopacket_record)
    test_genes_extraction(phenopacket_record)
    test_variants_extraction(phenopacket_record)
    test_biolink_entity_generation(phenopacket_record)
