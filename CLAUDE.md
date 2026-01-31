# phenopacket-ingest

This is a Koza ingest repository for transforming phenopacket data into Biolink model format.

## Project Structure

- `download.yaml` - Configuration for downloading phenopacket data from phenopacket-store
- `src/` - Transform code and configuration
  - `transform.py` / `transform.yaml` - Main transform for phenopacket data
  - `phenopacket_ingest/` - Supporting modules
    - `models/` - Pydantic models for phenopacket data
    - `parser/` - Phenopacket parsing utilities
    - `registry/` - Registry service for downloading and extracting phenopackets
    - `transformer/` - Biolink entity transformer
- `tests/` - Unit tests for transforms
- `output/` - Generated nodes and edges (gitignored)
- `data/` - Downloaded source data (gitignored)

## Key Commands

- `just run` - Full pipeline (download -> preprocess -> transform)
- `just download` - Download phenopacket data from phenopacket-store
- `just preprocess` - Extract phenopackets to JSONL format
- `just transform-all` - Run all transforms
- `just test` - Run tests

## Preprocessing

This ingest requires a preprocessing step to extract phenopacket data from the zip archive and convert to JSONL:
```bash
just preprocess
```

This uses the PhenopacketRegistryService to extract and parse phenopackets.
