"""
Phenopacket extraction module for processing phenopacket files.
"""
import json
import logging
import os
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Iterator

from phenopacket_ingest.parser.phenopacket_parser import PhenopacketParser


class PhenopacketExtractor:
    """Extractor for phenopacket data from downloaded store."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize phenopacket extractor.

        Args:
            logger: Logger for tracking operations
        """
        self.logger = logger or logging.getLogger(__name__)
        self.parser = PhenopacketParser(logger)

    def extract_to_jsonl(
            self,
            zip_path: Path,
            output_path: Path,
            cohort_name: str = "unknown",
            force: bool = False
    ) -> Path:
        """
        Extract phenopacket data to JSONL format.

        Args:
            zip_path: Path to the phenopacket ZIP file
            output_path: Path for the output JSONL file
            cohort_name: Default cohort name if not determinable from file paths
            force: Force re-extraction even if output file exists

        Returns:
            Path to the generated JSONL file
        """
        if output_path.exists() and not force:
            self.logger.info(f"JSONL file already exists at {output_path}")
            return output_path

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            from phenopackets import Phenopacket as PBPhenopacket
            from google.protobuf.json_format import Parse
        except ImportError:
            self.logger.error("phenopackets library not available, cannot extract data")
            raise ImportError("phenopackets library is required for extraction")

        self.logger.info(f"Extracting phenopacket data from {zip_path} to {output_path}")

        with zipfile.ZipFile(zip_path) as zf, open(output_path, "w") as f:
            phenopacket_files = [name for name in zf.namelist()
                                 if name.endswith('.json') and not name.startswith('__MACOSX')]

            total_files = len(phenopacket_files)
            self.logger.info(f"Found {total_files} phenopacket files to process")

            for i, pp_file in enumerate(phenopacket_files):
                if i % 100 == 0:
                    self.logger.info(f"Processing file {i + 1}/{total_files}")

                parts = pp_file.split('/')
                file_cohort_name = parts[0] if len(parts) > 1 else cohort_name

                try:
                    pp_content = zf.read(pp_file).decode('utf-8')
                    phenopacket = Parse(pp_content, PBPhenopacket())

                    self._process_phenopacket(phenopacket, f, file_cohort_name)

                except Exception as e:
                    self.logger.error(f"Error processing {pp_file}: {e}")

        self.logger.info(f"Extraction complete. JSONL file written to {output_path}")
        return output_path

    def _process_phenopacket(self, phenopacket, output_file, cohort_name: str) -> None:
        """
        Process a single phenopacket and write to JSONL.

        Args:
            phenopacket: A phenopacket protocol buffer object
            output_file: File to write JSONL output to
            cohort_name: Cohort name for this phenopacket
        """
        try:
            record_dict = self.parser.phenopacket_to_jsonl_dict(phenopacket, cohort_name)

            if record_dict:
                output_file.write(json.dumps(record_dict) + "\n")
            else:
                self.logger.warning(f"No data extracted from phenopacket {getattr(phenopacket, 'id', 'unknown')}")

        except Exception as e:
            self.logger.error(f"Error processing phenopacket {getattr(phenopacket, 'id', 'unknown')}: {e}")

    def process_jsonl_file(self, jsonl_path: Path, output_func) -> None:
        """
        Process a JSONL file containing phenopacket data.

        Args:
            jsonl_path: Path to the JSONL file
            output_func: Function to process each record
        """
        self.logger.info(f"Processing JSONL file: {jsonl_path}")

        with open(jsonl_path, 'r') as f:
            for i, line in enumerate(f):
                if i % 1000 == 0:
                    self.logger.info(f"Processed {i} records")

                try:
                    record = self.parser.parse_from_jsonl(line.strip())

                    if record and "id" in record:
                        output_func(record)
                    else:
                        self.logger.warning(f"Invalid record at line {i + 1}")

                except Exception as e:
                    self.logger.error(f"Error processing line {i + 1}: {e}")

        self.logger.info(f"Finished processing {jsonl_path}")