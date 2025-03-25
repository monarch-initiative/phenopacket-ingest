"""Transform extracted phenopacket data into biolink-compatible entities."""
import uuid
import logging
import json
from typing import List, Dict, Any, Optional, Union

from biolink_model.datamodel.pydanticmodel_v2 import (
    Gene,
    Disease,
    GeneToDiseaseAssociation,
    GeneToPhenotypicFeatureAssociation,
    DiseaseToPhenotypicFeatureAssociation,
    SequenceVariant,
    VariantToGeneAssociation,
    VariantToDiseaseAssociation,
    KnowledgeLevelEnum,
    AgentTypeEnum, CaseToPhenotypicFeatureAssociation,
)
from koza.cli_utils import get_koza_app

logger = logging.getLogger(__name__)

# Initialize the Koza application
# For testing, we'll handle the KeyError case in the test files
try:
    koza_app = get_koza_app("phenopacket_ingest")
except (KeyError, ImportError, ModuleNotFoundError):
    # This will be mocked in tests
    logger.warning("Koza app initialization failed, this is expected in test environments")
    koza_app = None

CAUSES = "biolink:causes"
CONTRIBUTES_TO = "biolink:contributes_to"
GENE_ASSOCIATED_WITH_CONDITION = "biolink:gene_associated_with_condition"
HAS_PHENOTYPE = "biolink:has_phenotype"
IS_SEQUENCE_VARIANT_OF = "biolink:is_sequence_variant_of"
DIAGNOSED_WITH = "biolink:diagnosed_with"  # For Case to Disease
HAS_VARIANT = "biolink:has_variant"        # For Case to Variant
HAS_GENE_VARIANT = "biolink:has_gene_variant"  # For Case to Gene

# FUTURE BIOLINK ENTITIES

"""
# Import future Biolink model classes when available
from biolink_model.datamodel.pydanticmodel_v2 import (
    Case,
    BiologicalSex,
    CaseToDiseaseAssociation,
    CaseToVariantAssociation,
    CaseToGeneAssociation,
)
"""


class PhenopacketTransformer:
    """Transform phenopacket data into biolink entities."""
    
    @staticmethod
    def transform_gene(row: Dict[str, Any]) -> Optional[Gene]:
        """Transform a row into a Gene entity."""
        if not row.get("gene_id") or not row.get("gene_symbol"):
            return None
        
        return Gene(
            id=row["gene_id"],
            symbol=row["gene_symbol"],
            name=row["gene_symbol"],
            # in_taxon=["NCBITaxon:9606"],  # Human
            # in_taxon_label="Homo sapiens",
            provided_by=["infores:phenopacket-store"],
        )
    
    @staticmethod
    def transform_disease(row: Dict[str, Any]) -> Optional[Disease]:
        """Transform a row into a Disease entity."""
        if not row.get("disease_id") or not row.get("disease_label"):
            return None
        
        return Disease(
            id=row["disease_id"],
            name=row["disease_label"],
            provided_by=["infores:phenopacket-store"],
        )
    
    @staticmethod
    def transform_variant(row: Dict[str, Any]) -> Optional[SequenceVariant]:
        """Transform a row into a SequenceVariant entity."""
        if not (row.get("variant_id") or
                (row.get("chromosome") and row.get("position") and 
                 row.get("reference") and row.get("alternate"))):
            return None
        
        variant_id = row.get("variant_id")
        if not variant_id and row.get("chromosome") and row.get("position"):
            chrom = row["chromosome"].replace("chr", "")
            pos = row["position"]
            ref = row.get("reference", "")
            alt = row.get("alternate", "")
            variant_id = f"{chrom}-{pos}-{ref}-{alt}"
        
        xrefs = []
        if row.get("variant_hgvs") and isinstance(row["variant_hgvs"], list):
            xrefs.extend(row["variant_hgvs"])
        
        return SequenceVariant(
            id=variant_id,
            has_gene=[row["gene_id"]] if row.get("gene_id") else None,
            xref=xrefs if xrefs else None,
            # in_taxon=["NCBITaxon:9606"],  # Human
            # in_taxon_label="Homo sapiens",
            provided_by=["infores:phenopacket-store"],
        )
        
    # FUTURE BIOLINK ENTITIES
    # Uncomment these methods when the Biolink model is updated with Case entities
    
    """
    @staticmethod
    def transform_case(row: Dict[str, Any]) -> Optional['Case']:
        '''Transform a row into a Case entity representing a patient/subject.'''
        if not row.get("subject_id"):
            return None

        case = Case(
            id=row['subject_id']",
            name=row['subject_id']",
            provided_by=["infores:phenopacket-store"],
        )

        # Add biological sex if available
        if row.get("subject_sex"):
            # Keep the original string values for sex
            if row["subject_sex"] in ["MALE", "FEMALE"]:
                case.sex = row["subject_sex"]
            
            # When BiologicalSex becomes available in biolink model, we can use this instead:
            # sex_val = row["subject_sex"]
            # case.sex = BiologicalSex(
            #     id=f"PATO:{'0000384' if sex_val == 'MALE' else '0000383'}",
            #     name=sex_val.capitalize()
            # )

        return case

    @staticmethod
    def create_case_to_disease_association(
        case_id: str, 
        disease_id: str,
        disease_name: str
    ) -> Optional['CaseToDiseaseAssociation']:
        '''Create an association between a case and a disease.'''
        if not case_id or not disease_id:
            return None
            
        return CaseToDiseaseAssociation(
            id=f"{uuid.uuid4()}",
            subject=case_id,
            predicate=DIAGNOSED_WITH,
            object=disease_id,
            primary_knowledge_source="infores:phenopacket-store",
            aggregator_knowledge_source=["infores:monarchinitiative"],
            knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
            agent_type=AgentTypeEnum.manual_agent,
        )
        
    @staticmethod
    def create_case_to_variant_association(
        case_id: str, 
        variant_id: str,
        interpretation_status: Optional[str] = None
    ) -> Optional['CaseToVariantAssociation']:
        '''Create an association between a case and a variant.'''
        if not case_id or not variant_id:
            return None
            
        return CaseToVariantAssociation(
            id=f"{uuid.uuid4()}",
            subject=case_id,
            predicate=HAS_VARIANT,
            object=variant_id,
            primary_knowledge_source="infores:phenopacket-store",
            aggregator_knowledge_source=["infores:monarchinitiative"],
            knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
            agent_type=AgentTypeEnum.manual_agent,
        )
        
    @staticmethod
    def create_case_to_gene_association(
        case_id: str, 
        gene_id: str
    ) -> Optional['CaseToGeneAssociation']:
        '''Create an association between a case and a gene.'''
        if not case_id or not gene_id:
            return None
            
        return CaseToGeneAssociation(
            id=f"{uuid.uuid4()}",
            subject=case_id,
            predicate=HAS_GENE_VARIANT,
            object=gene_id,
            primary_knowledge_source="infores:phenopacket-store",
            aggregator_knowledge_source=["infores:monarchinitiative"],
            knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
            agent_type=AgentTypeEnum.manual_agent,
        )
    """
    
    @staticmethod
    def process_row(row: Dict[str, Any]) -> List[Any]:
        """
        Process a single row of data from the phenopacket JSONL file.
        
        Args:
            row: A dictionary containing the extracted phenopacket data
            
        Returns:
            List of entities to write (gene, disease, variant, associations)
        """
        entities = []
        
        try:
            # Pre-process any JSON strings in the input
            parsed_row = row.copy()
            for field in ["observed_phenotypes", "excluded_phenotypes", "external_references", 
                         "variant_hgvs", "pmids", "onset"]:
                if isinstance(parsed_row.get(field), str) and parsed_row.get(field):
                    try:
                        parsed_row[field] = json.loads(parsed_row[field])
                    except json.JSONDecodeError:
                        # If it's not valid JSON, keep it as is
                        pass
            
            # Parse the row into a PhenopacketRecord
            from phenopacket_ingest.models import PhenopacketRecord
            
            # Parse with defaults for missing fields
            phenopacket_record = None
            try:
                phenopacket_record = PhenopacketRecord.model_validate(parsed_row)
                logger.debug(f"Successfully parsed row into PhenopacketRecord: {phenopacket_record.phenopacket_id}")
            except Exception as e:
                logger.warning(f"Error parsing row into PhenopacketRecord: {e}")
                # Continue with the parsed_row dictionary
            
            # Get publications for associations - either from model or original data
            publications = []
            if phenopacket_record and phenopacket_record.pmids:
                publications = phenopacket_record.pmids
            elif parsed_row.get("pmids") and isinstance(parsed_row["pmids"], list):
                publications = parsed_row["pmids"]
            
            # Create Biolink entities - use the record when available, fall back to dictionary
            
            # Gene entity
            gene = None
            if phenopacket_record and phenopacket_record.gene_id and phenopacket_record.gene_symbol:
                gene = Gene(
                    id=phenopacket_record.gene_id,
                    symbol=phenopacket_record.gene_symbol,
                    name=phenopacket_record.gene_symbol,
                    in_taxon=["NCBITaxon:9606"],  # Human
                    in_taxon_label="Homo sapiens",
                    provided_by=["infores:phenopacket-store"],
                )
            else:
                gene = PhenopacketTransformer.transform_gene(parsed_row)
                
            if gene:
                entities.append(gene)
            
            # Disease entity
            disease = None
            if phenopacket_record and phenopacket_record.disease_id and phenopacket_record.disease_label:
                disease = Disease(
                    id=phenopacket_record.disease_id,
                    name=phenopacket_record.disease_label,
                    provided_by=["infores:phenopacket-store"],
                )
            else:
                disease = PhenopacketTransformer.transform_disease(parsed_row)
                
            if disease:
                entities.append(disease)
            
            # Variant entity
            variant = None
            if phenopacket_record:
                variant_id = phenopacket_record.variant_id
                # Create variant ID if missing but we have coordinates
                if not variant_id and phenopacket_record.chromosome and phenopacket_record.position:
                    chrom = phenopacket_record.chromosome.replace("chr", "")
                    pos = phenopacket_record.position
                    ref = phenopacket_record.reference or ""
                    alt = phenopacket_record.alternate or ""
                    variant_id = f"PPKT:{chrom}-{pos}-{ref}-{alt}"
                
                if variant_id:
                    variant = SequenceVariant(
                        id=variant_id,
                        name=variant_id,
                        has_gene=[phenopacket_record.gene_id] if phenopacket_record.gene_id else None,
                        xref=phenopacket_record.variant_hgvs if phenopacket_record.variant_hgvs else None,
                        in_taxon=["NCBITaxon:9606"],
                        in_taxon_label="Homo sapiens",
                        provided_by=["infores:phenopacket-store"],
                    )
            
            if not variant:
                variant = PhenopacketTransformer.transform_variant(parsed_row)
                
            if variant:
                entities.append(variant)
            
            # FUTURE: Case entity
            # Uncomment when Case entity is available in Biolink model
            """
            case = None
            if phenopacket_record and phenopacket_record.subject_id:
                # Create Case entity from the phenopacket record
                case = Case(
                    id=f"CASE:{phenopacket_record.subject_id}",
                    name=f"Subject {phenopacket_record.subject_id}",
                    provided_by=["infores:phenopacket-store"],
                )
                
                # Add biological sex if available
                if phenopacket_record.subject_sex:
                    # Keep the original string values for sex
                    if phenopacket_record.subject_sex in ["MALE", "FEMALE"]:
                        case.sex = phenopacket_record.subject_sex
                    
                    # When BiologicalSex becomes available in biolink model, we can use this instead:
                    # case.sex = BiologicalSex(
                    #     id=f"PATO:{'0000384' if phenopacket_record.subject_sex == 'MALE' else '0000383'}",
                    #     name=phenopacket_record.subject_sex.capitalize()
                    # )
                
                entities.append(case)
                
                # Create Case associations
                case = PhenopacketTransformer.transform_case(parsed_row)
                if case:
                    entities.append(case)
                    
                    # Case to Disease association
                    if disease:
                        case_disease_assoc = PhenopacketTransformer.create_case_to_disease_association(
                            case_id=case.id,
                            disease_id=disease.id,
                            disease_name=disease.name
                        )
                        if case_disease_assoc:
                            entities.append(case_disease_assoc)
                    
                    # Case to Variant association
                    if variant:
                        case_variant_assoc = PhenopacketTransformer.create_case_to_variant_association(
                            case_id=case.id,
                            variant_id=variant.id,
                            interpretation_status=parsed_row.get("interpretation_status")
                        )
                        if case_variant_assoc:
                            entities.append(case_variant_assoc)
                    
                    # Case to Gene association
                    if gene:
                        case_gene_assoc = PhenopacketTransformer.create_case_to_gene_association(
                            case_id=case.id,
                            gene_id=gene.id
                        )
                        if case_gene_assoc:
                            entities.append(case_gene_assoc)
            """

            if gene and disease:
                gene_disease_assoc = GeneToDiseaseAssociation(
                    id=f"{uuid.uuid4()}",
                    subject=gene.id,
                    predicate=GENE_ASSOCIATED_WITH_CONDITION,
                    object=disease.id,
                    primary_knowledge_source="infores:phenopacket-store",
                    aggregator_knowledge_source=["infores:monarchinitiative"],
                    knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
                    agent_type=AgentTypeEnum.manual_agent,
                    publications=publications if publications else None,
                )
                entities.append(gene_disease_assoc)
            
            if variant and gene:
                variant_gene_assoc = VariantToGeneAssociation(
                    id=f"{uuid.uuid4()}",
                    subject=variant.id,
                    predicate=IS_SEQUENCE_VARIANT_OF,
                    object=gene.id,
                    primary_knowledge_source="infores:phenopacket-store",
                    aggregator_knowledge_source=["infores:monarchinitiative"],
                    knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
                    agent_type=AgentTypeEnum.manual_agent,
                    publications=publications if publications else None,
                )
                entities.append(variant_gene_assoc)
            
            if variant and disease:
                variant_disease_assoc = VariantToDiseaseAssociation(
                    id=f"{uuid.uuid4()}",
                    subject=variant.id,
                    predicate=CAUSES if parsed_row.get("interpretation_status") == "CAUSATIVE" else CONTRIBUTES_TO,
                    object=disease.id,
                    primary_knowledge_source="infores:phenopacket-store",
                    aggregator_knowledge_source=["infores:monarchinitiative"],
                    knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
                    agent_type=AgentTypeEnum.manual_agent,
                    publications=publications if publications else None,
                )
                entities.append(variant_disease_assoc)
            
            if parsed_row.get("observed_phenotypes") and isinstance(parsed_row["observed_phenotypes"], list):
                for phenotype in parsed_row["observed_phenotypes"]:
                    phenotype_id = phenotype.get("id")
                    if not phenotype_id:
                        continue
                    
                    if gene:
                        gene_pheno_assoc = CaseToPhenotypicFeatureAssociation(
                            id=f"{uuid.uuid4()}",
                            subject=gene.id,
                            predicate=HAS_PHENOTYPE,
                            object=phenotype_id,
                            primary_knowledge_source="infores:phenopacket-store",
                            aggregator_knowledge_source=["infores:monarchinitiative"],
                            knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
                            agent_type=AgentTypeEnum.manual_agent,
                            publications=publications if publications else None
                        )
                        entities.append(gene_pheno_assoc)
                    
                    if disease:
                        disease_pheno_assoc = DiseaseToPhenotypicFeatureAssociation(
                            id=f"{uuid.uuid4()}",
                            subject=disease.id,
                            predicate=HAS_PHENOTYPE,
                            object=phenotype_id,
                            primary_knowledge_source="infores:phenopacket-store",
                            aggregator_knowledge_source=["infores:monarchinitiative"],
                            knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
                            agent_type=AgentTypeEnum.manual_agent,
                            publications=publications if publications else None
                        )
                        entities.append(disease_pheno_assoc)
        
        except Exception as e:
            logger.error(f"Error processing row: {e}")
            logger.debug(f"Problematic row: {row}")
        
        return entities


if koza_app is not None:
    while (row := koza_app.get_row()) is not None:
        entities = PhenopacketTransformer.process_row(row)

        if entities:
            koza_app.write(*entities)