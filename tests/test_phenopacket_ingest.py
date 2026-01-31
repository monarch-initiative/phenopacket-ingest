import importlib.util
from pathlib import Path
from typing import Dict, List

import pytest
from koza.runner import KozaRunner, PassthroughWriter, load_transform

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)


# Paths relative to the tests directory
TESTS_DIR = Path(__file__).parent
TRANSFORM_SCRIPT = TESTS_DIR.parent / "src" / "transform.py"
TEST_DATA_DIR = TESTS_DIR / "data"


def load_module_from_path(path: Path):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_transform(rows: List[Dict]) -> List:
    """Run the transform on a list of input rows and return the output entities."""
    module = load_module_from_path(TRANSFORM_SCRIPT)
    hooks = load_transform(module)
    writer = PassthroughWriter()
    runner = KozaRunner(
        data=iter(rows),
        writer=writer,
        hooks=hooks,
        base_directory=TRANSFORM_SCRIPT.parent,
    )
    runner.run()
    return writer.data


def get_test_data_path(relative_path: str) -> str:
    return str(TEST_DATA_DIR.joinpath(relative_path).resolve())


def load_test_rows(file_path: str, n_rows: int = None, skip_rows: int = 0) -> List[Dict]:
    """Load rows from a JSONL file for testing."""
    import json

    rows = []
    with open(file_path, "r") as f:
        for i, line in enumerate(f):
            if i < skip_rows:
                continue
            if n_rows is not None and len(rows) >= n_rows:
                break
            rows.append(json.loads(line))
    return rows


@pytest.fixture
def phenopacket_test_file() -> str:
    return get_test_data_path("phenopacket_genes.jsonl")


@pytest.fixture
def row_group_1(phenopacket_test_file) -> List[Dict]:
    return load_test_rows(phenopacket_test_file, n_rows=3)


@pytest.fixture
def row_group_2(phenopacket_test_file) -> List[Dict]:
    return load_test_rows(phenopacket_test_file, n_rows=4, skip_rows=3)


@pytest.fixture
def row_group_3(phenopacket_test_file) -> List[Dict]:
    return load_test_rows(phenopacket_test_file, n_rows=3, skip_rows=7)


def test_row_group_1_structure(row_group_1):
    assert len(row_group_1) == 3
    for row in row_group_1:
        assert "id" in row
        assert "subject_sex" in row
        assert "phenotypic_features" in row


def test_transform_produces_entities(row_group_1):
    """Test that the transform produces output entities."""
    entities = run_transform(row_group_1)
    assert len(entities) > 0, "Transform should produce at least one entity"


def test_transform_produces_case_entities(row_group_1):
    """Test that the transform produces Case entities."""
    entities = run_transform(row_group_1)
    # Check for Case entities (type checking based on the biolink model)
    case_entities = [e for e in entities if hasattr(e, "has_biological_sex")]
    assert len(case_entities) > 0, "Transform should produce Case entities"


def test_transform_produces_associations(row_group_1):
    """Test that the transform produces association entities."""
    entities = run_transform(row_group_1)
    # Associations have subject/predicate/object
    associations = [e for e in entities if hasattr(e, "subject") and hasattr(e, "predicate") and hasattr(e, "object")]
    assert len(associations) > 0, "Transform should produce association entities"


def test_row_group_2_transform(row_group_2):
    """Test transform on second group of rows."""
    entities = run_transform(row_group_2)
    assert len(entities) > 0, "Transform should produce entities from row_group_2"


def test_row_group_3_transform(row_group_3):
    """Test transform on third group of rows."""
    entities = run_transform(row_group_3)
    assert len(entities) > 0, "Transform should produce entities from row_group_3"
