"""Command line interface for phenopacket-ingest."""

import logging
from pathlib import Path

import typer
from kghub_downloader.download_utils import download_from_yaml
from koza.cli_utils import transform_source

app = typer.Typer()
logger = logging.getLogger(__name__)


@app.callback()
def callback(version: bool = typer.Option(False, "--version", is_eager=True)):
    """phenopacket-ingest CLI."""
    if version:
        from phenopacket_ingest import __version__

        typer.echo(f"phenopacket-ingest version: {__version__}")
        raise typer.Exit()


@app.command()
def download(
    force: bool = typer.Option(False, help="Force download of data, even if it exists"),
    release_tag: str = typer.Option(None, help="Specific release tag to download (e.g., '0.1.18')"),
):
    """Download phenopacket data for processing."""
    typer.echo("Downloading phenopacket data...")

    download_config = Path(__file__).parent / "download.yaml"
    download_from_yaml(yaml_file=download_config, output_dir=".")

    from phenopacket_ingest.config import PhenopacketStoreConfig
    from phenopacket_ingest.registry import PhenopacketRegistryService

    config = PhenopacketStoreConfig()
    if release_tag:
        config.release_tag = release_tag

    registry = PhenopacketRegistryService()
    zip_path = registry.download_latest_release()

    typer.echo(f"Downloaded phenopacket data to {zip_path}")


@app.command()
def extract(
    force: bool = typer.Option(False, help="Force re-extraction of data, even if it exists"),
    release_tag: str = typer.Option(None, help="Specific release tag to process"),
):
    """Extract phenopacket data to JSONL format for transformation."""
    from phenopacket_ingest.config import PhenopacketStoreConfig
    from phenopacket_ingest.registry import PhenopacketRegistryService

    config = PhenopacketStoreConfig()
    if release_tag:
        config.release_tag = release_tag
        print(f"Release tag: {release_tag}")

    registry = PhenopacketRegistryService()
    jsonl_path = registry.extract_phenopackets_to_jsonl()

    typer.echo(f"Extracted phenopacket data to {jsonl_path}")


@app.command()
def transform(
    output_dir: str = typer.Option("output", help="Output directory for transformed data"),
    row_limit: int = typer.Option(None, help="Number of rows to process"),
    limit: int = typer.Option(None, help="Limit to process only N phenopackets (shortcut for row_limit=1)"),
    verbose: bool = typer.Option(False, help="Whether to be verbose"),
):
    """Run the Koza transform for phenopacket-ingest."""
    jsonl_path = Path("data/phenopackets/output/phenopackets.jsonl")
    if not jsonl_path.exists():
        typer.echo(f"JSONL file {jsonl_path} does not exist. Running extraction...")
        extract()

    # If limit is specified, it overrides row_limit
    if limit is not None:
        row_limit = limit

    transform_code = Path(__file__).parent / "transform.yaml"
    transform_source(
        source=transform_code,
        output_dir=output_dir,
        output_format="tsv",
        row_limit=row_limit,
        verbose=verbose,
    )


@app.command()
def pipeline(
    output_dir: str = typer.Option("output", help="Output directory for transformed data"),
    release_tag: str = typer.Option(None, help="Specific release tag to process"),
    row_limit: int = typer.Option(None, help="Number of rows to process"),
    limit: int = typer.Option(None, help="Limit to process only N phenopackets (shortcut for row_limit=1)"),
    verbose: bool = typer.Option(False, help="Whether to be verbose"),
):
    """Run the complete phenopacket-ingest pipeline (download, extract, transform)."""
    download(force=False, release_tag=release_tag)
    extract(force=False, release_tag=release_tag)
    transform(output_dir=output_dir, row_limit=row_limit, limit=limit, verbose=verbose)


if __name__ == "__main__":
    app()
