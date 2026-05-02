"""
Parser for phenopacket protobuf objects.

This module provides functionality to parse phenopacket protobuf objects
into JSON-serializable dictionaries and Pydantic models.
"""

import json
import logging
from typing import Any, Dict, Optional

PHENOPACKETS_AVAILABLE = False
try:
    from google.protobuf.json_format import MessageToDict, Parse
    from phenopackets import Phenopacket as PBPhenopacket

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
            phenopacket_dict = MessageToDict(
                phenopacket, preserving_proto_field_name=True
            )

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
            phenopacket_dict = self.phenopacket_to_dict(phenopacket)
            if not phenopacket_dict:
                return None

            # Convert all camelCase keys to snake_case for consistency
            phenopacket_dict = self.convert_dict_keys_to_snake_case(phenopacket_dict)
            phenopacket_dict["cohort"] = cohort_name

            result = {
                "id": phenopacket_dict.get("id", ""),
                "cohort": cohort_name,
            }

            if "subject" in phenopacket_dict:
                subject = phenopacket_dict["subject"]
                result["subject_id"] = subject.get("id", "")
                result["subject_sex"] = subject.get("sex", "")

                if "time_at_last_encounter" in subject and "age" in subject["time_at_last_encounter"]:
                    result["subject_age"] = subject["time_at_last_encounter"]["age"].get("iso8601duration", "")

                result["subject"] = subject

            if "phenotypic_features" in phenopacket_dict:
                result["phenotypic_features"] = phenopacket_dict["phenotypic_features"]

                observed = []
                excluded = []
                for feature in phenopacket_dict["phenotypic_features"]:
                    if feature.get("excluded", False):
                        excluded.append(feature)
                    else:
                        observed.append(feature)

                result["observed_phenotypes"] = observed
                result["excluded_phenotypes"] = excluded

            if "diseases" in phenopacket_dict:
                result["diseases"] = phenopacket_dict["diseases"]

                if phenopacket_dict["diseases"]:
                    disease = phenopacket_dict["diseases"][0]
                    if "term" in disease:
                        result["disease_id"] = disease["term"].get("id", "")
                        result["disease_label"] = disease["term"].get("label", "")

                    if "onset" in disease and "age" in disease["onset"]:
                        result["disease_onset"] = disease["onset"]["age"].get("iso8601duration", "")

            if "interpretations" in phenopacket_dict:
                result["interpretations"] = phenopacket_dict["interpretations"]

                genes = []
                variants = []

                for interp in phenopacket_dict.get("interpretations", []):
                    if "diagnosis" in interp and "genomic_interpretations" in interp["diagnosis"]:
                        for gi in interp["diagnosis"]["genomic_interpretations"]:
                            if "gene" in gi:
                                gene_info = {
                                    "id": gi["gene"].get("value_id", ""),
                                    "symbol": gi["gene"].get("symbol", ""),
                                    "interpretation_status": gi.get("interpretation_status", ""),
                                }
                                genes.append(gene_info)

                                if not result.get("gene_symbol") and not result.get("gene_id"):
                                    result["gene_symbol"] = gene_info["symbol"]
                                    result["gene_id"] = gene_info["id"]

                            if (
                                "variant_interpretation" in gi
                                and "variation_descriptor" in gi["variant_interpretation"]
                            ):
                                vd = gi["variant_interpretation"]["variation_descriptor"]
                                variant = {
                                    "id": vd.get("id", ""),
                                    "interpretation_status": gi.get("interpretation_status", ""),
                                    "hgvs_expressions": [],
                                }

                                if "gene_context" in vd:
                                    variant["gene_symbol"] = vd["gene_context"].get("symbol", "")
                                    variant["gene_id"] = vd["gene_context"].get("value_id", "")

                                if "vcf_record" in vd:
                                    vcf = vd["vcf_record"]
                                    variant["genome_assembly"] = vcf.get("genome_assembly", "")
                                    variant["chromosome"] = vcf.get("chrom", "")
                                    variant["position"] = vcf.get("pos", "")
                                    variant["reference"] = vcf.get("ref", "")
                                    variant["alternate"] = vcf.get("alt", "")

                                if "allelic_state" in vd:
                                    variant["zygosity"] = vd["allelic_state"].get("label", "")

                                if "expressions" in vd:
                                    for expr in vd["expressions"]:
                                        if "value" in expr:
                                            variant["hgvs_expressions"].append(expr["value"])

                                variants.append(variant)

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

            for field in ["biosamples", "measurements", "medical_actions", "files", "meta_data"]:
                if field in phenopacket_dict:
                    result[field] = phenopacket_dict[field]

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
        if "subject" in pb_dict and "sex" in pb_dict["subject"]:
            sex_value = pb_dict["subject"]["sex"]
            if isinstance(sex_value, (int, str)):
                sex_mapping = {
                    "0": "UNKNOWN",
                    "1": "FEMALE",
                    "2": "MALE",
                    "3": "OTHER",
                    "UNKNOWN_SEX": "UNKNOWN",
                    "FEMALE": "FEMALE",
                    "MALE": "MALE",
                    "OTHER_SEX": "OTHER",
                }
                pb_dict["subject"]["sex"] = sex_mapping.get(str(sex_value), str(sex_value))

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
                                "4": "CAUSATIVE",
                            }
                            gi["interpretation_status"] = status_mapping.get(str(status), str(status))

    def camel_to_snake(self, name: str) -> str:
        """Convert camelCase string to snake_case."""
        import re

        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def convert_dict_keys_to_snake_case(self, obj: Any) -> Any:
        """Recursively convert all dictionary keys from camelCase to snake_case."""
        if isinstance(obj, dict):
            new_dict = {}
            for key, value in obj.items():
                new_key = self.camel_to_snake(key)
                new_dict[new_key] = self.convert_dict_keys_to_snake_case(value)
            return new_dict
        elif isinstance(obj, list):
            return [self.convert_dict_keys_to_snake_case(item) for item in obj]
        else:
            return obj

    def validate_against_model(self, data: Dict[str, Any]) -> None:
        """Validate data against the PhenopacketRecord model and print warnings for mismatches."""
        from phenopacket_ingest.models import PhenopacketRecord

        model_fields = set(PhenopacketRecord.model_fields.keys())
        data_fields = set(data.keys())

        # Check for missing fields
        missing_fields = model_fields - data_fields
        if missing_fields:
            missing_required = []
            missing_optional = []

            for field in missing_fields:
                if field in PhenopacketRecord.model_fields:
                    field_info = PhenopacketRecord.model_fields[field]
                    if field_info.is_required():
                        missing_required.append(field)
                    else:
                        missing_optional.append(field)

            if missing_required:
                print(f"WARNING: Missing required fields: {', '.join(missing_required)}")

            if missing_optional and len(missing_optional) < 10:  # Only show if there are just a few
                print(f"INFO: Missing optional fields: {', '.join(missing_optional)}")

        # Check for extra fields
        extra_fields = data_fields - model_fields
        if extra_fields:
            print(f"WARNING: Found extra fields not in model: {', '.join(extra_fields)}")

    def parse_from_json(self, json_str: str) -> Dict[str, Any]:
        """
        Parse a phenopacket from a JSON string, converting camelCase to snake_case.

        Args:
            json_str: JSON string representation of a phenopacket

        Returns:
            A dictionary representation of the phenopacket with snake_case keys

        """
        try:
            data = json.loads(json_str)
            converted_data = self.convert_dict_keys_to_snake_case(data)
            self.validate_against_model(converted_data)
            return converted_data
        except Exception as e:
            self.logger.error(f"Error parsing phenopacket JSON: {e}")
            return {}

    def parse_from_jsonl(self, jsonl_line: str) -> Dict[str, Any]:
        """
        Parse a phenopacket from a JSONL line, converting camelCase to snake_case.

        Args:
            jsonl_line: A line from a JSONL file

        Returns:
            A dictionary representation of the phenopacket with snake_case keys

        """
        try:
            data = json.loads(jsonl_line)
            converted_data = self.convert_dict_keys_to_snake_case(data)
            self.validate_against_model(converted_data)
            return converted_data
        except Exception as e:
            self.logger.error(f"Error parsing JSONL line: {e}")
            return {}
