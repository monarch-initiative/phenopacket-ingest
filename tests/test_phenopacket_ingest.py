import types
from typing import Dict, List

import pytest
import yaml
from koza.app import KozaApp
from koza.io.yaml_loader import UniqueIncludeLoader
from koza.model.config.source_config import OutputFormat, PrimaryFileConfig
from koza.model.source import Source


def get_mock_koza(
    yaml_file: str, translation_table: str, output_dir: str, output_format: str, files: List[str]
) -> KozaApp:
    with open(yaml_file, 'r') as source_fh:
        yaml_data = yaml.load(source_fh, Loader=UniqueIncludeLoader)

    yaml_data['files'] = files
    source_config = PrimaryFileConfig(**yaml_data)

    koza_app = KozaApp(
        source=Source(source_config),
        translation_table=translation_table,
        output_dir=output_dir,
        output_format=OutputFormat(output_format),
    )

    def _mock_write(self, *entities):
        if hasattr(self, '_entities'):
            self._entities.extend(list(entities))
        else:
            self._entities = list(entities)

    koza_app.write = types.MethodType(_mock_write, koza_app)
    return koza_app


def get_koza_rows(mock_koza: KozaApp, n_rows: int) -> List[Dict]:
    rows = []
    for _ in range(n_rows):
        row = mock_koza.get_row()
        if row is not None:
            rows.append(row)
    return rows


@pytest.fixture
def phenopacket_yaml():
    return "../tests/data/test_transform.yaml"


@pytest.fixture
def phenopacket_translation_table() -> str:
    return "../tests/data/translation_table.yaml"


@pytest.fixture
def phenopacket_test_file() -> List[str]:
    return ["../tests/data/phenopacket_genes.jsonl"]


@pytest.fixture
def phenopacket_test_output() -> str:
    return "tests/output/phenopacket_test"


@pytest.fixture
def phenopacket_test_output_format() -> str:
    return "jsonl"


@pytest.fixture
def phenopacket_mock_koza(
    phenopacket_yaml,
    phenopacket_translation_table,
    phenopacket_test_output,
    phenopacket_test_output_format,
    phenopacket_test_file,
) -> KozaApp:
    return get_mock_koza(
        phenopacket_yaml,
        phenopacket_translation_table,
        phenopacket_test_output,
        phenopacket_test_output_format,
        phenopacket_test_file,
    )


@pytest.fixture
def row_group_1(phenopacket_mock_koza) -> List[Dict]:
    return get_koza_rows(phenopacket_mock_koza, 3)  # Example: first 3 rows


@pytest.fixture
def row_group_2(phenopacket_mock_koza) -> List[Dict]:
    _ = get_koza_rows(phenopacket_mock_koza, 3)  # skip first 3
    return get_koza_rows(phenopacket_mock_koza, 4)  # next 4 rows


@pytest.fixture
def row_group_3(phenopacket_mock_koza) -> List[Dict]:
    _ = get_koza_rows(phenopacket_mock_koza, 7)  # skip first 7
    return get_koza_rows(phenopacket_mock_koza, 3)  # last 3 rows


def test_row_group_1_structure(row_group_1):
    assert len(row_group_1) == 3
    for row in row_group_1:
        assert "phenopacket_id" in row
        assert "gene_symbol" in row
