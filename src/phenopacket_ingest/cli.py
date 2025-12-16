"""Command line interface for phenopacket-ingest."""

import json
import logging
import ssl
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

import certifi
import typer
from kghub_downloader.download_utils import download_from_yaml
from koza.cli_utils import transform_source

app = typer.Typer()
logger = logging.getLogger(__name__)


def _get_latest_release_info() -> dict:
    """Fetch latest release info from GitHub API."""
    ctx = ssl.create_default_context(cafile=certifi.where())
    api_url = "https://api.github.com/repos/monarch-initiative/phenopacket-store/releases/latest"
    with urlopen(api_url, timeout=10.0, context=ctx) as response:
        return json.load(response)


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
):
    """Download phenopacket data for processing."""
    typer.echo("Downloading phenopacket data...")

    # Fetch release info from GitHub API
    release_info = _get_latest_release_info()
    release_tag = release_info.get("tag_name", "unknown")
    published_at = release_info.get("published_at", "unknown")

    typer.echo(f"Latest release: {release_tag} (published {published_at})")

    download_config = Path(__file__).parent / "download.yaml"
    download_from_yaml(yaml_file=download_config, output_dir=".")

    # Save version metadata
    metadata_dir = Path("data/phenopackets")
    metadata_dir.mkdir(parents=True, exist_ok=True)
    metadata_file = metadata_dir / "version.json"
    metadata = {
        "release_tag": release_tag,
        "published_at": published_at,
        "downloaded_at": datetime.now().isoformat(),
        "source_url": release_info.get("html_url", ""),
    }
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    typer.echo(f"Downloaded phenopacket data to data/phenopackets/all_phenopackets.zip")
    typer.echo(f"Version metadata saved to {metadata_file}")


@app.command()
def extract(
    force: bool = typer.Option(False, help="Force re-extraction of data, even if it exists"),
):
    """Extract phenopacket data to JSONL format for transformation."""
    from phenopacket_ingest.registry import PhenopacketRegistryService

    zip_path = Path("data/phenopackets/all_phenopackets.zip")
    if not zip_path.exists():
        typer.echo(f"Zip file {zip_path} not found. Run 'download' first.")
        raise typer.Exit(1)

    registry = PhenopacketRegistryService()
    jsonl_path = registry.extract_phenopackets_to_jsonl(zip_path=zip_path)

    typer.echo(f"Extracted phenopacket data to {jsonl_path}")


@app.command()
def transform(
    output_dir: str = typer.Option("output", help="Output directory for transformed data"),
    row_limit: int = typer.Option(None, help="Number of rows to process"),
    limit: int = typer.Option(None, help="Limit to process only N phenopackets (shortcut for row_limit=1)"),
    verbose: bool = typer.Option(False, help="Whether to be verbose"),
):
    """Run the Koza transform for phenopacket-ingest."""
    jsonl_path = Path("data/phenopackets.jsonl")
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
    row_limit: int = typer.Option(None, help="Number of rows to process"),
    limit: int = typer.Option(None, help="Limit to process only N phenopackets (shortcut for row_limit=1)"),
    verbose: bool = typer.Option(False, help="Whether to be verbose"),
):
    """Run the complete phenopacket-ingest pipeline (download, extract, transform)."""
    download(force=False)
    extract(force=False)
    transform(output_dir=output_dir, row_limit=row_limit, limit=limit, verbose=verbose)


if __name__ == "__main__":
    app()
