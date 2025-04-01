from pathlib import Path

from kgx.cli.cli_utils import transform as kgx_transform
from loguru import logger

logger.info(f"Creating rdf output: output/data_source, ex. alliance, flybase, or hpoa._type_of_ingest, ex. gene, disease_to_phenotype, or disease_associations..nt.gz ...")

src_files = []
src_nodes = f"output/data_source, ex. alliance, flybase, or hpoa._type_of_ingest, ex. gene, disease_to_phenotype, or disease_associations._nodes.tsv"
src_edges = f"output/data_source, ex. alliance, flybase, or hpoa._type_of_ingest, ex. gene, disease_to_phenotype, or disease_associations._edges.tsv"

if Path(src_nodes).is_file():
    src_files.append(src_nodes)
if Path(src_edges).is_file():
    src_files.append(src_edges)

kgx_transform(
    inputs=src_files,
    input_format="tsv",
    stream=True,
    output=f"output/data_source, ex. alliance, flybase, or hpoa._type_of_ingest, ex. gene, disease_to_phenotype, or disease_associations..nt.gz",
    output_format="nt",
    output_compression="gz",
)
