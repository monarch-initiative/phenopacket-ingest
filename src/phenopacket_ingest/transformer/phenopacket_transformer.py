"""
Transformer for converting phenopacket records to Biolink entities.

This module provides functionality to transform PhenopacketRecord objects
into Biolink model entities for knowledge graph integration.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from phenopacket_ingest.models import (
    Disease,
    PhenopacketRecord,
    PhenotypicFeature,
)

try:
    from biolink_model.datamodel.pydanticmodel_v2 import (
        AgentTypeEnum,
        BiologicalSex,
        Case,
        CaseToDiseaseAssociation,
        CaseToGeneAssociation,
        CaseToPhenotypicFeatureAssociation,
        KnowledgeLevelEnum,
    )

    BIOLINK_AVAILABLE = True
except ImportError:
    BIOLINK_AVAILABLE = False
    logging.warning("Biolink model not available. Using fallback implementations.")


class PhenopacketTransformer:
    """
    Transformer that converts PhenopacketRecord objects into Biolink entities.

    This class provides methods to transform phenopacket data into:
    - Case entities
    - Disease associations
    - Gene associations
    - Phenotypic feature associations
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the transformer."""
        self.logger = logger or logging.getLogger(__name__)

    @staticmethod
    def parse_phenopacket(row: Dict[str, Any]) -> Optional[PhenopacketRecord]:
        """
        Parse and validate a raw JSON row into a PhenopacketRecord.
        Pre-processes JSON string fields if necessary.

        Args:
            row: Dictionary from a JSONL file

        Returns:
            A validated PhenopacketRecord or None if validation fails

        """
        # Handle fields that might be serialized as strings
        for field in [
            "phenotypic_features",
            "observed_phenotypes",
            "excluded_phenotypes",
            "biosamples",
            "measurements",
            "medical_actions",
            "files",
            "diseases",
            "interpretations",
            "meta_data",
            "external_references",
            "variant_hgvs",
            "pmids",
        ]:
            if isinstance(row.get(field), str) and row.get(field):
                try:
                    row[field] = json.loads(row[field])
                except json.JSONDecodeError:
                    # If it's not valid JSON, leave as is
                    pass

        try:
            record = PhenopacketRecord.model_validate(row)
            return record
        except Exception as e:
            logging.error(f"Error validating phenopacket record: {e}")
            return None

    @staticmethod
    def transform_case(record: PhenopacketRecord) -> Optional[Any]:
        """
        Transform the subject of the Phenopacket into a Biolink Case entity.

        Args:
            record: A PhenopacketRecord

        Returns:
            A Biolink Case entity or fallback object if required fields are missing

        """
        if not record.subject.id:
            return None

        if not record.subject.sex:
            print("BiologicalSex not given.")

        if BIOLINK_AVAILABLE:
            case = Case(
                id=f"PPKT:{record.id}",
                name=record.subject.id,
                has_biological_sex=str(record.subject.sex.value),
            )

        return case

    @staticmethod
    def transform_phenotypic_features(
        case_id: str,
        phenotypic_features: List[Union[PhenotypicFeature, Dict[str, Any]]],
        pmids: Optional[List[str]] = None,
    ) -> List[CaseToPhenotypicFeatureAssociation]:
        """
        Transform phenotypic features into case-to-phenotypic-feature associations.

        Args:
            case_id: ID of the case
            phenotypic_features: List of phenotypic features
            pmids: List of PubMed IDs

        Returns:
            List of case-to-phenotypic-feature associations

        """
        associations = []

        for feature in phenotypic_features:
            feature_id = feature.id if hasattr(feature, 'id') else feature.get('id')
            excluded = feature.excluded if hasattr(feature, 'excluded') else feature.get('excluded', False)

            if not feature_id:
                continue

            onset = ""  # Default to empty string instead of None
            if hasattr(feature, 'onset') and feature.onset:
                if hasattr(feature.onset, 'age') and feature.onset.age:
                    if hasattr(feature.onset.age, 'iso8601duration'):
                        onset = feature.onset.age.iso8601duration or ""
            elif isinstance(feature, dict) and 'onset' in feature and feature['onset']:
                if isinstance(feature['onset'], dict) and 'age' in feature['onset'] and feature['onset']['age']:
                    if isinstance(feature['onset']['age'], dict) and 'iso8601duration' in feature['onset']['age']:
                        onset = feature['onset']['age']['iso8601duration'] or ""
                    elif isinstance(feature['onset']['age'], str):
                        onset = feature['onset']['age'] or ""
            assoc = CaseToPhenotypicFeatureAssociation(
                subject=case_id,
                id=f"PPKT:{case_id}",
                predicate="biolink:has_phenotype",
                object=feature_id,
                knowledge_level=KnowledgeLevelEnum.observation,
                agent_type=AgentTypeEnum.manual_agent,
                onset_qualifier=str(onset),
                negated=excluded,
                publications=pmids if pmids else None,
            )
            associations.append(assoc)

        return associations

    @staticmethod
    def transform_diseases(
        case_id: str, diseases: List[Union[Disease, Dict[str, Any]]], pmids: Optional[List[str]] = None
    ) -> List[CaseToDiseaseAssociation]:
        """
        Transform diseases into case-to-disease associations.

        Args:
            case_id: ID of the case
            diseases: List of diseases
            pmids: List of PubMed IDs

        Returns:
            List of case-to-disease associations

        """
        associations = []

        for disease in diseases:
            if hasattr(disease, 'id'):
                disease_id = disease.id
            elif isinstance(disease, dict):
                disease_id = disease.get('id', '')
                if not disease_id and 'term' in disease and isinstance(disease['term'], dict):
                    disease_id = disease['term'].get('id', '')
            else:
                continue

            if not disease_id:
                continue

            onset = ""  # Default to empty string instead of None
            if hasattr(disease, 'onset') and disease.onset:
                if hasattr(disease.onset, 'age') and disease.onset.age:
                    if hasattr(disease.onset.age, 'iso8601duration'):
                        onset = disease.onset.age.iso8601duration or ""
            elif isinstance(disease, dict) and 'onset' in disease and disease['onset']:
                if isinstance(disease['onset'], dict) and 'age' in disease['onset'] and disease['onset']['age']:
                    if isinstance(disease['onset']['age'], dict) and 'iso8601duration' in disease['onset']['age']:
                        onset = disease['onset']['age']['iso8601duration'] or ""
                    elif isinstance(disease['onset']['age'], str):
                        onset = disease['onset']['age'] or ""

            assoc = CaseToDiseaseAssociation(
                id=f"PPKT:{case_id}",
                subject=case_id,
                predicate="biolink:has_disease",
                object=disease_id,
                knowledge_level=KnowledgeLevelEnum.observation,
                agent_type=AgentTypeEnum.manual_agent,
                onset_qualifier=str(onset),
                publications=pmids if pmids else None,
            )
            associations.append(assoc)

        return associations

    @staticmethod
    def transform_genes(
        case_id: str, genes: List[Dict[str, Any]], pmids: Optional[List[str]] = None
    ) -> List[CaseToGeneAssociation]:
        """
        Transform genes into case-to-gene associations.

        Args:
            case_id: ID of the case
            genes: List of genes
            pmids: List of PubMed IDs

        Returns:
            List of case-to-gene associations

        """
        associations = []

        for gene in genes:
            gene_id = gene.get("id", "")
            if not gene_id:
                continue

            assoc = CaseToGeneAssociation(
                id=f"PPKT:{case_id}",
                subject=case_id,
                predicate="biolink:has_gene",
                object=gene_id,
                knowledge_level=KnowledgeLevelEnum.observation,
                agent_type=AgentTypeEnum.manual_agent,
                publications=pmids if pmids else None,
            )
            associations.append(assoc)

        return associations

    @classmethod
    def process_record(cls, record: Union[Dict[str, Any], PhenopacketRecord]) -> List[Any]:
        """
        Process a phenopacket record and transform it into Biolink entities.

        Args:
            record: A PhenopacketRecord or dictionary

        Returns:
            List of Biolink entities

        """
        entities = []

        if isinstance(record, dict):
            record = cls.parse_phenopacket(record)

        if not record:
            return entities

        case = cls.transform_case(record)
        if not case:
            return entities

        entities.append(case)

        case_id = case.id if hasattr(case, 'id') else case.get('id', '')

        if hasattr(record, 'phenotypic_features') and record.phenotypic_features:
            phenotype_assocs = cls.transform_phenotypic_features(
                case_id=case_id, phenotypic_features=record.phenotypic_features, pmids=record.pmids
            )
            entities.extend(phenotype_assocs)

        if hasattr(record, 'diseases') and record.diseases:
            disease_assocs = cls.transform_diseases(case_id=case_id, diseases=record.diseases, pmids=record.pmids)
            entities.extend(disease_assocs)

        if hasattr(record, 'genes') and record.genes:
            gene_assocs = cls.transform_genes(case_id=case_id, genes=record.genes, pmids=record.pmids)
            entities.extend(gene_assocs)

        return entities

    @classmethod
    def process_jsonl_line(cls, line: str) -> List[Any]:
        """
        Process a single line from a JSONL file.

        Args:
            line: A line from a JSONL file

        Returns:
            List of Biolink entities

        """
        try:
            data = json.loads(line)
            return cls.process_record(data)
        except Exception as e:
            raise e
