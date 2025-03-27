"""
Models for phenopacket data.

This module contains Pydantic models for representing phenopacket data
and associated entities for validation and transformation.
"""

from phenopacket_ingest.models.ontology import OntologyClass
from phenopacket_ingest.models.phenopacket import (
    PhenopacketRecord,
    Subject,
    PhenotypicFeature,
    Disease,
    Variant,
    Biosample,
    Measurement,
    MedicalAction,
    File,
    TimeElement,
)
from phenopacket_ingest.models.metadata import (
    MetaData,
    ExternalReference,
)
from phenopacket_ingest.models.interpretation import (
    Interpretation,
    Diagnosis,
    GenomicInterpretation,
    InterpretationStatus,
)
from phenopacket_ingest.models.associations import (
    CaseToDiseaseAssociation,
    CaseToGeneAssociation,
    CaseToVariantAssociation,
)

__all__ = [
    "OntologyClass",
    "PhenopacketRecord",
    "Subject",
    "PhenotypicFeature",
    "Disease",
    "Variant",
    "Biosample",
    "Measurement",
    "MedicalAction",
    "File",
    "TimeElement",
    "MetaData",
    "ExternalReference",
    "Interpretation",
    "Diagnosis",
    "GenomicInterpretation",
    "InterpretationStatus",
    "CaseToDiseaseAssociation",
    "CaseToGeneAssociation",
    "CaseToVariantAssociation",
]