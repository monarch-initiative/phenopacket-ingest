"""
Metadata models for phenopacket data.

This module contains models for metadata associated with phenopackets,
including external references and resources.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ExternalReference(BaseModel):
    """A reference to an external resource."""

    id: str
    reference: Optional[str] = None
    description: Optional[str] = None


class Resource(BaseModel):
    """A description of an external resource."""

    id: str
    name: str
    namespace_prefix: Optional[str] = None
    url: Optional[str] = None
    version: Optional[str] = None
    iri_prefix: Optional[str] = None


class Update(BaseModel):
    """An update to a phenopacket."""

    timestamp: str
    updated_by: str
    comment: Optional[str] = None


class MetaData(BaseModel):
    """Metadata about a phenopacket."""

    created: Optional[str] = None
    created_by: Optional[str] = None
    submitted_by: Optional[str] = None
    resources: List[Resource] = Field(default_factory=list)
    updates: List[Update] = Field(default_factory=list)
    phenopacket_schema_version: Optional[str] = None
    external_references: List[ExternalReference] = Field(default_factory=list)
