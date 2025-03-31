"""
Interpretation models for phenopacket data.

This module contains models for interpretations of phenopacket data,
including disease diagnoses and genomic interpretations.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from phenopacket_ingest.models.ontology import OntologyClass


class InterpretationStatus(str, Enum):
    """Status of a genomic interpretation."""

    UNKNOWN_STATUS = "UNKNOWN_STATUS"
    REJECTED = "REJECTED"
    CANDIDATE = "CANDIDATE"
    CONTRIBUTORY = "CONTRIBUTORY"
    CAUSATIVE = "CAUSATIVE"

    @classmethod
    def from_proto_value(cls, value: Union[int, str]) -> "InterpretationStatus":
        """Convert from protobuf value."""
        if isinstance(value, str) and value in cls.__members__.values():
            return cls(value)

        mapping = {
            "0": cls.UNKNOWN_STATUS,
            "1": cls.REJECTED,
            "2": cls.CANDIDATE,
            "3": cls.CONTRIBUTORY,
            "4": cls.CAUSATIVE,
        }
        return mapping.get(str(value), cls.UNKNOWN_STATUS)


class ProgressStatus(str, Enum):
    """Status of a clinical interpretation."""

    UNKNOWN_PROGRESS = "UNKNOWN_PROGRESS"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SOLVED = "SOLVED"
    UNSOLVED = "UNSOLVED"


class VariationDescriptor(BaseModel):
    """A description of a genomic variation."""

    id: Optional[str] = None
    gene_context: Optional[Dict[str, str]] = None
    vcf_record: Optional[Dict[str, Any]] = None
    expressions: List[Dict[str, str]] = Field(default_factory=list)
    molecular_consequence: Optional[OntologyClass] = None
    allelic_state: Optional[OntologyClass] = None


class VariantInterpretation(BaseModel):
    """Interpretation of a variant."""

    acmg_pathogenicity_classification: Optional[str] = None
    therapeutic_actionability: Optional[str] = None
    variation_descriptor: Optional[VariationDescriptor] = None


class GenomicInterpretation(BaseModel):
    """Interpretation of genomic findings."""

    subject_or_biosample_id: Optional[str] = None
    interpretation_status: Optional[InterpretationStatus] = None
    gene: Optional[Dict[str, str]] = None
    variant_interpretation: Optional[VariantInterpretation] = None

    class Config:
        use_enum_values = True


class Diagnosis(BaseModel):
    """A diagnosis."""

    disease: Optional[OntologyClass] = None
    genomic_interpretations: List[GenomicInterpretation] = Field(default_factory=list)


class Interpretation(BaseModel):
    """A clinical interpretation."""

    id: str
    progress_status: Optional[ProgressStatus] = None
    diagnosis: Optional[Diagnosis] = None
    summary: Optional[str] = None

    class Config:
        use_enum_values = True
