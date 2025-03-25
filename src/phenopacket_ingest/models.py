"""Models for phenopacket data parsing and transformation."""
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, validator


class OntologyClass(BaseModel):
    """An ontology class (term) with ID and label."""
    id: str
    label: str


class Age(BaseModel):
    """Age representation using ISO8601 duration format."""
    iso8601duration: str


class TimeElement(BaseModel):
    """A time element that can represent age or other time specifications."""
    age: Optional[Age] = None


class Variant(BaseModel):
    """A genomic variant as represented in phenopackets."""
    id: Optional[str] = None
    gene_symbol: str
    gene_id: str
    hgvs_expressions: List[str] = Field(default_factory=list)
    genome_assembly: Optional[str] = None
    chromosome: Optional[str] = None
    position: Optional[str] = None
    reference: Optional[str] = None
    alternate: Optional[str] = None
    zygosity: Optional[str] = None
    molecular_consequence: Optional[str] = None


class Disease(BaseModel):
    """A disease entity as represented in phenopackets."""
    id: str
    label: str
    onset: Optional[str] = None


class PhenotypicFeature(BaseModel):
    """A phenotypic feature (HPO term) as represented in phenopackets."""
    id: str
    label: str
    excluded: bool = False
    onset: Optional[str] = None


class Reference(BaseModel):
    """An external reference (e.g., PMID) for a phenopacket."""
    id: str
    reference: Optional[str] = None
    description: Optional[str] = None


class Subject(BaseModel):
    """Subject information from a phenopacket."""
    id: str
    sex: Optional[str] = None
    age: Optional[str] = None


class PhenopacketData(BaseModel):
    """
    Core model for phenopacket data extraction.
    
    This model contains all the relevant information extracted from a phenopacket
    that will be used in the transformation process.
    """
    phenopacket_id: str
    subject: Subject
    cohort: str
    external_references: List[Reference] = Field(default_factory=list)
    pmids: List[str] = Field(default_factory=list)
    disease: Optional[Disease] = None
    observed_phenotypes: List[PhenotypicFeature] = Field(default_factory=list)
    excluded_phenotypes: List[PhenotypicFeature] = Field(default_factory=list)
    variants: List[Variant] = Field(default_factory=list)
    interpretation_status: Optional[str] = None
    
    @property
    def gene_symbols(self) -> List[str]:
        """Get all unique gene symbols from variants."""
        return list(set(v.gene_symbol for v in self.variants if v.gene_symbol))
    
    @property
    def gene_ids(self) -> List[str]:
        """Get all unique gene IDs from variants."""
        return list(set(v.gene_id for v in self.variants if v.gene_id))
    
    @property
    def hpo_ids(self) -> List[str]:
        """Get all observed HPO IDs."""
        return [p.id for p in self.observed_phenotypes]
    
    @property
    def phenotypes_by_gene(self) -> Dict[str, List[PhenotypicFeature]]:
        """Get phenotypes organized by gene."""
        return {gene: self.observed_phenotypes for gene in self.gene_symbols}
    
    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to a flat JSON dictionary for JSONL export."""
        result = {
            "phenopacket_id": self.phenopacket_id,
            "subject_id": self.subject.id,
            "subject_sex": self.subject.sex or "",
            "cohort": self.cohort,
            "pmids": [p for p in self.pmids],
            "external_references": [r.model_dump() for r in self.external_references],
            "interpretation_status": self.interpretation_status or "",
        }
        
        if self.disease:
            result.update({
                "disease_id": self.disease.id,
                "disease_label": self.disease.label,
                "disease_onset": self.disease.onset or "",
            })
        else:
            result.update({
                "disease_id": "",
                "disease_label": "",
                "disease_onset": "",
            })
        
        result.update({
            "observed_phenotypes": [p.model_dump() for p in self.observed_phenotypes],
            "excluded_phenotypes": [p.model_dump() for p in self.excluded_phenotypes],
        })
        
        # This works for the simple case with one variant per record
        if self.variants:
            variant = self.variants[0]
            result.update({
                "gene_symbol": variant.gene_symbol,
                "gene_id": variant.gene_id,
                "variant_id": variant.id or "",
                "variant_hgvs": variant.hgvs_expressions,
                "genome_assembly": variant.genome_assembly or "",
                "chromosome": variant.chromosome or "",
                "position": variant.position or "",
                "reference": variant.reference or "",
                "alternate": variant.alternate or "",
                "zygosity": variant.zygosity or "",
            })
        else:
            result.update({
                "gene_symbol": "",
                "gene_id": "",
                "variant_id": "",
                "variant_hgvs": [],
                "genome_assembly": "",
                "chromosome": "",
                "position": "",
                "reference": "",
                "alternate": "",
                "zygosity": "",
            })
        
        return result


class PhenopacketRecord(BaseModel):
    """A single record for the JSONL file, representing one row of data."""
    phenopacket_id: str
    subject_id: str
    subject_sex: str = ""
    gene_symbol: str
    gene_id: str
    variant_id: str = ""
    variant_hgvs: List[str] = Field(default_factory=list)
    genome_assembly: str = ""
    chromosome: str = ""
    position: str = ""
    reference: str = ""
    alternate: str = ""
    zygosity: str = ""
    interpretation_status: str = ""
    disease_id: str = ""
    disease_label: str = ""
    disease_onset: str = ""
    pmids: List[str] = Field(default_factory=list)
    observed_phenotypes: List[Dict[str, Any]] = Field(default_factory=list)
    excluded_phenotypes: List[Dict[str, Any]] = Field(default_factory=list)
    cohort: str
    external_references: List[Dict[str, Any]] = Field(default_factory=list)
    pmids: List[str] = Field(default_factory=list)