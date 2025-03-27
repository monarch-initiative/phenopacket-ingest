"""
Parser for phenopacket protobuf objects.

This module provides functionality to parse phenopacket protobuf objects
into JSON-serializable dictionaries and Pydantic models.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union

# Check if phenopackets library is available
PHENOPACKETS_AVAILABLE = False
try:
    from phenopackets import Phenopacket as PBPhenopacket
    from google.protobuf.json_format import MessageToDict, Parse

    PHENOPACKETS_AVAILABLE = True
except ImportError:
    logging.warning("phenopackets library not available. Functionality will be limited.")


class PhenopacketParser:
    """
    Parser for phenopacket data.

    This class provides methods to:
    1. Parse phenopacket protobuf objects into dictionaries
    2. Convert dictionaries to JSON-serializable format
    3. Handle special fields and enums
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the parser."""
        self.logger = logger or logging.getLogger(__name__)

    def phenopacket_to_dict(self, phenopacket: 'PBPhenopacket') -> Dict[str, Any]:
        """
        Convert a phenopacket protocol buffer object to a Python dictionary.

        Args:
            phenopacket: A phenopacket protocol buffer object

        Returns:
            A dictionary representation of the phenopacket
        """
        if not PHENOPACKETS_AVAILABLE:
            self.logger.error("Cannot parse phenopacket: phenopackets library not available")
            return {}

        try:
            # Convert protobuf to dictionary
            phenopacket_dict = MessageToDict(
                phenopacket,
                preserving_proto_field_name=True,
                including_default_value_fields=False
            )

            # Process special fields
            self._process_special_fields(phenopacket_dict)

            return phenopacket_dict

        except Exception as e:
            self.logger.error(f"Error converting phenopacket to dict: {e}")
            return {}

    def phenopacket_to_jsonl_dict(self, phenopacket: 'PBPhenopacket', cohort_name: str) -> Optional[Dict[str, Any]]:
        """
        Convert a phenopacket to a flat dictionary suitable for JSONL export.

        Args:
            phenopacket: A phenopacket protocol buffer object
            cohort_name: The name of the cohort this phenopacket belongs to

        Returns:
            A dictionary with flattened phenopacket data or None if conversion fails
        """
        try:
            # Convert to dictionary
            phenopacket_dict = self.phenopacket_to_dict(phenopacket)
            if not phenopacket_dict:
                return None

            # Add cohort information
            phenopacket_dict["cohort"] = cohort_name

            # Extract and flatten needed fields
            result = {
                "id": phenopacket_dict.get("id", ""),
                "cohort": cohort_name,
            }

            # Process subject
            if "subject" in phenopacket_dict:
                subject = phenopacket_dict["subject"]
                result["subject_id"] = subject.get("id", "")
                result["subject_sex"] = subject.get("sex", "")

                # Extract age if available
                if "time_at_last_encounter" in subject and "age" in subject["time_at_last_encounter"]:
                    result["subject_age"] = subject["time_at_last_encounter"]["age"].get("iso8601duration", "")

                # Include complete subject data
                result["subject"] = subject

            # Include phenotypic features
            if "phenotypic_features" in phenopacket_dict:
                result["phenotypic_features"] = phenopacket_dict["phenotypic_features"]

                # Split into observed and excluded phenotypes for convenience
                observed = []
                excluded = []
                for feature in phenopacket_dict["phenotypic_features"]:
                    if feature.get("excluded", False):
                        excluded.append(feature)
                    else:
                        observed.append(feature)

                result["observed_phenotypes"] = observed
                result["excluded_phenotypes"] = excluded

            # Include diseases
            if "diseases" in phenopacket_dict:
                result["diseases"] = phenopacket_dict["diseases"]

                # Include first disease details for convenience
                if phenopacket_dict["diseases"]:
                    disease = phenopacket_dict["diseases"][0]
                    if "term" in disease:
                        result["disease_id"] = disease["term"].get("id", "")
                        result["disease_label"] = disease["term"].get("label", "")

                    # Extract onset if available
                    if "onset" in disease and "age" in disease["onset"]:
                        result["disease_onset"] = disease["onset"]["age"].get("iso8601duration", "")

            # Include interpretations and extract variant/gene information
            if "interpretations" in phenopacket_dict:
                result["interpretations"] = phenopacket_dict["interpretations"]

                # Process genomic interpretations
                genes = []
                variants = []

                for interp in phenopacket_dict.get("interpretations", []):
                    if "diagnosis" in interp and "genomic_interpretations" in interp["diagnosis"]:
                        for gi in interp["diagnosis"]["genomic_interpretations"]:
                            # Extract gene information
                            if "gene" in gi:
                                gene_info = {
                                    "id": gi["gene"].get("value_id", ""),
                                    "symbol": gi["gene"].get("symbol", ""),
                                    "interpretation_status": gi.get("interpretation_status", "")
                                }
                                genes.append(gene_info)

                                # Include first gene details for convenience
                                if not result.get("gene_symbol") and not result.get("gene_id"):
                                    result["gene_symbol"] = gene_info["symbol"]
                                    result["gene_id"] = gene_info["id"]

                            # Extract variant information
                            if "variant_interpretation" in gi and "variation_descriptor" in gi[
                                "variant_interpretation"]:
                                vd = gi["variant_interpretation"]["variation_descriptor"]
                                variant = {
                                    "id": vd.get("id", ""),
                                    "interpretation_status": gi.get("interpretation_status", ""),
                                    "hgvs_expressions": []
                                }

                                # Get gene context
                                if "gene_context" in vd:
                                    variant["gene_symbol"] = vd["gene_context"].get("symbol", "")
                                    variant["gene_id"] = vd["gene_context"].get("value_id", "")

                                # Get VCF information
                                if "vcf_record" in vd:
                                    vcf = vd["vcf_record"]
                                    variant["genome_assembly"] = vcf.get("genome_assembly", "")
                                    variant["chromosome"] = vcf.get("chrom", "")
                                    variant["position"] = vcf.get("pos", "")
                                    variant["reference"] = vcf.get("ref", "")
                                    variant["alternate"] = vcf.get("alt", "")

                                # Get zygosity
                                if "allelic_state" in vd:
                                    variant["zygosity"] = vd["allelic_state"].get("label", "")

                                # Extract HGVS expressions
                                if "expressions" in vd:
                                    for expr in vd["expressions"]:
                                        if "value" in expr:
                                            variant["hgvs_expressions"].append(expr["value"])

                                variants.append(variant)

                                # Include first variant details for convenience
                                if not result.get("variant_id"):
                                    result["variant_id"] = variant["id"]
                                    result["genome_assembly"] = variant.get("genome_assembly", "")
                                    result["chromosome"] = variant.get("chromosome", "")
                                    result["position"] = variant.get("position", "")
                                    result["reference"] = variant.get("reference", "")
                                    result["alternate"] = variant.get("alternate", "")
                                    result["zygosity"] = variant.get("zygosity", "")
                                    result["variant_hgvs"] = variant["hgvs_expressions"]

                result["genes"] = genes
                result["variants"] = variants

            # Include other data
            for field in ["biosamples", "measurements", "medical_actions", "files", "meta_data"]:
                if field in phenopacket_dict:
                    result[field] = phenopacket_dict[field]

            # Extract PMIDs from meta_data
            if "meta_data" in phenopacket_dict and "external_references" in phenopacket_dict["meta_data"]:
                pmids = []
                external_references = []

                for ref in phenopacket_dict["meta_data"]["external_references"]:
                    external_references.append(ref)
                    if "id" in ref and ref["id"].startswith("PMID:"):
                        pmids.append(ref["id"])

                result["external_references"] = external_references
                result["pmids"] = pmids

            return result

        except Exception as e:
            self.logger.error(f"Error converting phenopacket to JSONL dict: {e}")
            return None

    def _process_special_fields(self, pb_dict: Dict[str, Any]) -> None:
        """
        Process special fields in the protobuf dictionary.

        Args:
            pb_dict: Dictionary converted from protobuf
        """
        # Process subject sex
        if "subject" in pb_dict and "sex" in pb_dict["subject"]:
            sex_value = pb_dict["subject"]["sex"]
            if isinstance(sex_value, (int, str)):
                # Map from protobuf enum to string
                sex_mapping = {
                    "0": "UNKNOWN",
                    "1": "FEMALE",
                    "2": "MALE",
                    "3": "OTHER",
                    "UNKNOWN_SEX": "UNKNOWN",
                    "FEMALE": "FEMALE",
                    "MALE": "MALE",
                    "OTHER_SEX": "OTHER"
                }
                pb_dict["subject"]["sex"] = sex_mapping.get(str(sex_value), str(sex_value))

        # Process interpretation status
        for interp in pb_dict.get("interpretations", []):
            if "diagnosis" in interp and "genomic_interpretations" in interp["diagnosis"]:
                for gi in interp["diagnosis"]["genomic_interpretations"]:
                    if "interpretation_status" in gi:
                        status = gi["interpretation_status"]
                        if isinstance(status, (int, str)):
                            status_mapping = {
                                "0": "UNKNOWN_STATUS",
                                "1": "REJECTED",
                                "2": "CANDIDATE",
                                "3": "CONTRIBUTORY",
                                "4": "CAUSATIVE"
                            }
                            gi["interpretation_status"] = status_mapping.get(str(status), str(status))

    def parse_from_json(self, json_str: str) -> Dict[str, Any]:
        """
        Parse a phenopacket from a JSON string.

        Args:
            json_str: JSON string representation of a phenopacket

        Returns:
            A dictionary representation of the phenopacket
        """
        try:
            data = json.loads(json_str)
            return data
        except Exception as e:
            self.logger.error(f"Error parsing phenopacket JSON: {e}")
            return {}

    def parse_from_jsonl(self, jsonl_line: str) -> Dict[str, Any]:
        """
        Parse a phenopacket from a JSONL line.

        Args:
            jsonl_line: A line from a JSONL file

        Returns:
            A dictionary representation of the phenopacket
        """
        try:
            data = json.loads(jsonl_line)
            return data
        except Exception as e:
            self.logger.error(f"Error parsing JSONL line: {e}")
            return {}