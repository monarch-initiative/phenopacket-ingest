"""
Ontology classes for phenopacket data.

This module contains basic classes for ontology references used throughout
the phenopacket schema.
"""

from typing import Optional
from pydantic import BaseModel, Field


class OntologyClass(BaseModel):
    """
    A class in an ontology (term or concept).

    This class represents an ontology term with an ID (CURIE) and a human-readable label.
    """
    id: str
    label: Optional[str] = None

    def __str__(self) -> str:
        """String representation of the ontology class."""
        if self.label:
            return f"{self.id} ({self.label})"
        return self.id

    @classmethod
    def from_dict(cls, data: dict) -> "OntologyClass":
        """Create an OntologyClass from a dictionary."""
        id_value = data.get("id")
        label = data.get("label")
        return cls(id=id_value, label=label)