"""
Association models for mapping to Biolink.

This module contains models for associations between cases and other entities
that can be used for mapping to the Biolink model.
"""

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field


class CaseToDiseaseAssociation(BaseModel):
    """Association between a case and a disease."""

    id: str = Field(default_factory=lambda: f"uuid:{str(uuid.uuid4())}")
    subject: str
    predicate: str = "biolink:diagnosed_with"
    object: str
    primary_knowledge_source: str = "infores:phenopacket-store"
    aggregator_knowledge_source: List[str] = Field(default_factory=lambda: ["infores:monarchinitiative"])
    knowledge_level: str = "knowledge_assertion"
    agent_type: str = "manual_agent"
    onset_qualifier: Optional[str] = None
    publications: Optional[List[str]] = None


class CaseToVariantAssociation(BaseModel):
    """Association between a case and a variant."""

    id: str = Field(default_factory=lambda: f"uuid:{str(uuid.uuid4())}")
    subject: str
    predicate: str = "biolink:has_variant"
    object: str
    primary_knowledge_source: str = "infores:phenopacket-store"
    aggregator_knowledge_source: List[str] = Field(default_factory=lambda: ["infores:monarchinitiative"])
    knowledge_level: str = "knowledge_assertion"
    agent_type: str = "manual_agent"
    zygosity: Optional[str] = None
    interpretation_status: Optional[str] = None
    publications: Optional[List[str]] = None


class CaseToGeneAssociation(BaseModel):
    """Association between a case and a gene."""

    id: str = Field(default_factory=lambda: f"uuid:{str(uuid.uuid4())}")
    subject: str
    predicate: str = "biolink:gene_associated_with_condition"
    object: str
    primary_knowledge_source: str = "infores:phenopacket-store"
    aggregator_knowledge_source: List[str] = Field(default_factory=lambda: ["infores:monarchinitiative"])
    knowledge_level: str = "knowledge_assertion"
    agent_type: str = "manual_agent"
    publications: Optional[List[str]] = None


class CaseToPhenotypicFeatureAssociation(BaseModel):
    """Association between a case and a phenotypic feature."""

    id: str = Field(default_factory=lambda: f"uuid:{str(uuid.uuid4())}")
    subject: str
    predicate: str = "biolink:has_phenotype"
    object: str
    primary_knowledge_source: str = "infores:phenopacket-store"
    aggregator_knowledge_source: List[str] = Field(default_factory=lambda: ["infores:monarchinitiative"])
    knowledge_level: str = "knowledge_assertion"
    agent_type: str = "manual_agent"
    onset: Optional[str] = None
    negated: bool = False
    publications: Optional[List[str]] = None
