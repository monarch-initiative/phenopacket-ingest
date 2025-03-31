"""
Core phenopacket models.

This module contains the main Pydantic models for phenopacket data,
closely following the phenopacket schema specification.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, model_validator, validator

from phenopacket_ingest.models.metadata import MetaData
from phenopacket_ingest.models.ontology import OntologyClass


class Age(BaseModel):
    iso8601duration: str


class Encounter(BaseModel):
    age: Age

    @property
    def age_value(self) -> str:
        return self.age.iso8601duration


class TimeElement(BaseModel):
    """A time element that can represent age or timestamps."""

    age: Optional[Age] = None  # ISO8601 duration
    timestamp: Optional[datetime] = None
    interval: Optional[Dict[str, Any]] = None


class Sex(str, Enum):
    """Sex of an individual."""

    UNKNOWN = "UNKNOWN"
    FEMALE = "FEMALE"
    MALE = "MALE"
    OTHER = "OTHER"


class KaryotypicSex(str, Enum):
    """Karyotypic sex of an individual."""

    UNKNOWN_KARYOTYPE = "UNKNOWN_KARYOTYPE"
    XX = "XX"
    XY = "XY"
    XO = "XO"
    XXY = "XXY"
    XXX = "XXX"
    XXYY = "XXYY"
    XXXY = "XXXY"
    XXXX = "XXXX"
    XYY = "XYY"
    OTHER_KARYOTYPE = "OTHER_KARYOTYPE"


class VitalStatus(BaseModel):
    """Vital status of an individual."""

    status: str
    time_of_death: Optional[TimeElement] = None
    cause_of_death: Optional[OntologyClass] = None
    survival_time_after_onset: Optional[TimeElement] = None


class Evidence(BaseModel):
    """Evidence for a phenotypic feature."""

    evidence_code: Optional[OntologyClass] = None
    reference: Optional[Dict[str, str]] = None


class PhenotypeTerm(BaseModel):
    id: str = Field(..., description="The ontology term ID of this feature")
    label: Optional[str] = None


class PhenotypicFeature(BaseModel):
    """A phenotypic feature (typically an HPO term)."""

    type: PhenotypeTerm
    excluded: bool = False
    description: Optional[str] = None
    severity: Optional[OntologyClass] = None
    modifiers: List[OntologyClass] = Field(default_factory=list)
    onset: Optional[TimeElement] = None
    resolution: Optional[TimeElement] = None
    evidence: Optional[List[Evidence]] = Field(default_factory=list)

    @property
    def id(self) -> str:
        return self.type.id

    @property
    def label(self) -> str:
        return self.type.label


class DiseaseTerm(BaseModel):
    id: str = Field(..., description="The ontology term ID of this disease")
    label: Optional[str]


class Disease(BaseModel):
    """A disease diagnosis."""

    term: DiseaseTerm
    excluded: bool = False
    onset: Optional[TimeElement] = None
    resolution: Optional[TimeElement] = None
    disease_stage: List[OntologyClass] = Field(default_factory=list)
    clinical_tnm_finding: List[OntologyClass] = Field(default_factory=list)
    primary_site: Optional[OntologyClass] = None
    laterality: Optional[OntologyClass] = None

    @property
    def id(self) -> str:
        return self.term.id

    @property
    def label(self) -> str:
        return self.term.label


class VcfRecord(BaseModel):
    """A variant in VCF format."""

    genome_assembly: str
    chrom: str
    pos: str
    id: Optional[str] = None
    ref: str
    alt: str
    qual: Optional[str] = None
    filter: Optional[str] = None
    info: Optional[str] = None


class Zygosity(BaseModel):
    id: str
    label: str = None


class Variant(BaseModel):
    """A genomic variant."""

    id: Optional[str] = None
    gene_symbol: Optional[str] = None
    gene_id: Optional[str] = None
    hgvs_expressions: List[str] = Field(default_factory=list)
    vcf_record: Optional[VcfRecord] = None
    zygosity: str = None
    interpretation_status: Optional[str] = None

    # Convenience properties to avoid nested access
    @property
    def chromosome(self) -> Optional[str]:
        """Get the chromosome from VCF record."""
        return self.vcf_record.chrom if self.vcf_record else None

    @property
    def position(self) -> Optional[str]:
        """Get the position from VCF record."""
        return self.vcf_record.pos if self.vcf_record else None

    @property
    def reference(self) -> Optional[str]:
        """Get the reference allele from VCF record."""
        return self.vcf_record.ref if self.vcf_record else None

    @property
    def alternate(self) -> Optional[str]:
        """Get the alternate allele from VCF record."""
        return self.vcf_record.alt if self.vcf_record else None

    @property
    def genome_assembly(self) -> Optional[str]:
        """Get the genome assembly from VCF record."""
        return self.vcf_record.genome_assembly if self.vcf_record else None


class Procedure(BaseModel):
    """A clinical procedure."""

    code: OntologyClass
    body_site: Optional[OntologyClass] = None
    performed: Optional[Union[str, Dict[str, Any]]] = None


class GenomeAssembly(BaseModel):
    genome_assembly: str
    """A genomic assembly."""


class File(BaseModel):
    """A reference to an external file."""

    uri: str
    file_format: Optional[str] = None
    file_attributes: GenomeAssembly = None
    file_type: Optional[str] = None


class ReferenceRange(BaseModel):
    high: Optional[float] = None
    low: Optional[float] = None
    unit: Optional[OntologyClass] = None


class Quantity(BaseModel):
    referenceRange: Optional[ReferenceRange] = None
    unit: Optional[OntologyClass] = None
    value: Optional[int] = None


class Value(BaseModel):
    """A measurement value."""

    quantity: Optional[Quantity] = None
    ontology_class: Optional[OntologyClass] = None
    time_value: Optional[TimeElement] = None
    string_value: Optional[str] = None
    boolean_value: Optional[bool] = None


class ComplexValue(BaseModel):
    """A complex measurement value."""

    typed_quantities: Dict[str, Any] = Field(default_factory=dict)


class Measurement(BaseModel):
    """A clinical measurement."""

    description: Optional[str] = None
    assay: OntologyClass
    value: Optional[Value] = None
    complex_value: Optional[ComplexValue] = None
    time_observed: Optional[TimeElement] = None
    procedure: Optional[Procedure] = None


class Treatment(BaseModel):
    """A treatment."""

    agent: OntologyClass
    route_of_administration: Optional[OntologyClass] = None
    dose_intervals: List[Dict[str, Any]] = Field(default_factory=list)
    drug_type: Optional[OntologyClass] = None


class MedicalAction(BaseModel):
    """A medical action such as treatment or procedure."""

    procedure: Optional[Procedure] = None
    treatment: Optional[Treatment] = None
    radiation_therapy: Optional[Dict[str, Any]] = None
    therapeutic_regimen: Optional[Dict[str, Any]] = None
    treatment_target: Optional[OntologyClass] = None
    treatment_intent: Optional[OntologyClass] = None
    response_to_treatment: Optional[OntologyClass] = None
    adverse_events: List[OntologyClass] = Field(default_factory=list)
    treatment_termination_reason: Optional[OntologyClass] = None


class Subject(BaseModel):
    """An individual subject of a phenopacket."""

    id: str
    alternate_ids: List[str] = Field(default_factory=list)
    date_of_birth: Optional[datetime] = None
    time_at_last_encounter: Encounter = None
    vital_status: Optional[VitalStatus] = None
    sex: Optional[Union[Sex, str]] = None
    karyotypic_sex: Optional[KaryotypicSex] = None
    gender: Optional[OntologyClass] = None
    taxonomy: Optional[OntologyClass] = None

    @validator('sex', pre=True)
    def validate_sex(cls, v):
        """Validate sex field."""
        if isinstance(v, str):
            try:
                return Sex(v)
            except ValueError:
                # If not a valid enum value, keep as string
                return v
        return v

    @property
    def age(self) -> str:
        """Shortcut to get the subject's age as ISO 8601 duration."""
        return self.time_at_last_encounter.age_value


class Taxonomy(BaseModel):
    id: str
    label: str


class Biosample(BaseModel):
    """A biological sample."""

    id: str
    individual_id: Optional[str] = None
    derived_from_id: Optional[str] = None
    description: Optional[str] = None
    sampled_tissue: Optional[OntologyClass] = None
    sample_type: Optional[OntologyClass] = None
    phenotypic_features: List[PhenotypicFeature] = Field(default_factory=list)
    measurements: List[Measurement] = Field(default_factory=list)
    taxonomy: Optional[OntologyClass] = None
    time_of_collection: Optional[TimeElement] = None
    histological_diagnosis: Optional[OntologyClass] = None
    tumor_progression: Optional[OntologyClass] = None
    tumor_grade: Optional[OntologyClass] = None
    pathological_stage: Optional[OntologyClass] = None
    pathological_tnm_finding: List[OntologyClass] = Field(default_factory=list)
    diagnostic_markers: List[OntologyClass] = Field(default_factory=list)
    procedure: Optional[Procedure] = None
    files: List[File] = Field(default_factory=list)
    material_sample: Optional[OntologyClass] = None
    sample_processing: Optional[OntologyClass] = None
    sample_storage: Optional[OntologyClass] = None


class PhenopacketRecord(BaseModel):
    """
    A phenopacket record representing a complete phenopacket.

    This is the top-level model that corresponds to a complete phenopacket
    and can be serialized to/from JSONL for further processing.
    """

    id: str
    subject: Subject
    phenotypic_features: List[PhenotypicFeature] = Field(default_factory=list)
    measurements: List[Measurement] = Field(default_factory=list)
    biosamples: List[Biosample] = Field(default_factory=list)
    interpretations: List[Dict[str, Any]] = Field(default_factory=list)
    diseases: List[Disease] = Field(default_factory=list)
    medical_actions: List[MedicalAction] = Field(default_factory=list)
    files: List[File] = Field(default_factory=list)
    meta_data: Optional[MetaData] = None

    # Additional fields for working with the record
    cohort: Optional[str] = None

    # Extra fields not in the original schema but needed for convenience
    observed_phenotypes: List[PhenotypicFeature] = Field(default_factory=list)
    excluded_phenotypes: List[PhenotypicFeature] = Field(default_factory=list)
    genes: List[Dict[str, Any]] = Field(default_factory=list)
    variants: List[Variant] = Field(default_factory=list)
    pmids: List[str] = Field(default_factory=list)
    external_references: List[Dict[str, Any]] = Field(default_factory=list)

    # Convenience fields for simple access
    disease_id: Optional[str] = None
    disease_label: Optional[str] = None
    disease_onset: Optional[str] = None
    gene_symbol: Optional[str] = None
    gene_id: Optional[str] = None
    variant_id: Optional[str] = None
    genome_assembly: Optional[str] = None
    chromosome: Optional[str] = None
    position: Optional[str] = None
    reference: Optional[str] = None
    alternate: Optional[str] = None
    zygosity: Optional[str] = None
    variant_hgvs: List[str] = Field(default_factory=list)
    interpretation_status: Optional[str] = None

    @model_validator(mode='after')
    def process_nested_objects(self):
        """Process nested objects to ensure proper structure."""

        # If genes/variants not provided, extract from interpretations
        if not self.genes and not self.variants and self.interpretations:
            for interp in self.interpretations:
                if "diagnosis" in interp and "genomic_interpretations" in interp["diagnosis"]:
                    for gi in interp["diagnosis"]["genomic_interpretations"]:
                        if "gene" in gi:
                            gene_info = {
                                "id": gi["gene"].get("value_id", ""),
                                "symbol": gi["gene"].get("symbol", ""),
                                "interpretation_status": gi.get("interpretation_status", ""),
                            }
                            self.genes.append(gene_info)

                        if "variant_interpretation" in gi and "variation_descriptor" in gi["variant_interpretation"]:
                            vd = gi["variant_interpretation"]["variation_descriptor"]

                            variant = Variant(
                                id=vd.get("id", ""),
                                interpretation_status=gi.get("interpretation_status", ""),
                                hgvs_expressions=[],
                            )

                            if "gene_context" in vd:
                                variant.gene_symbol = vd["gene_context"].get("symbol", "")
                                variant.gene_id = vd["gene_context"].get("value_id", "")

                            if "vcf_record" in vd:
                                vcf = vd["vcf_record"]
                                variant.vcf_record = VcfRecord(
                                    genome_assembly=vcf.get("genome_assembly", ""),
                                    chrom=vcf.get("chrom", ""),
                                    pos=vcf.get("pos", ""),
                                    ref=vcf.get("ref", ""),
                                    alt=vcf.get("alt", ""),
                                )

                            if "allelic_state" in vd:
                                if isinstance(vd["allelic_state"], dict) and "label" in vd["allelic_state"]:
                                    variant.zygosity = vd["allelic_state"]["label"]
                                else:
                                    variant.zygosity = vd["allelic_state"]

                            if "expressions" in vd:
                                for expr in vd["expressions"]:
                                    if "value" in expr:
                                        variant.hgvs_expressions.append(expr["value"])

                            self.variants.append(variant)

        if not self.pmids and self.meta_data and hasattr(self.meta_data, "external_references"):
            for ref in self.meta_data.external_references:
                if hasattr(ref, "id") and ref.id.startswith("PMID:"):
                    self.pmids.append(ref.id)

        return self

    @classmethod
    def from_dict(cls, data: dict) -> "PhenopacketRecord":
        """Create a PhenopacketRecord from a dictionary."""
        if "subject" in data and isinstance(data["subject"], dict):
            data["subject"] = Subject.model_validate(data["subject"])

        if "phenotypic_features" in data and isinstance(data["phenotypic_features"], list):
            features = []
            for feature in data["phenotypic_features"]:
                if isinstance(feature, dict):
                    features.append(PhenotypicFeature.model_validate(feature))
            data["phenotypic_features"] = features

        if "diseases" in data and isinstance(data["diseases"], list):
            diseases = []
            for disease in data["diseases"]:
                if isinstance(disease, dict):
                    diseases.append(Disease.model_validate(disease))
            data["diseases"] = diseases

        return cls.model_validate(data)
