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
  - `versions.py` - Per-ingest upstream version fetcher (consumed by `just metadata`)
- `scripts/write_metadata.py` - Emits `output/release-metadata.yaml` from `versions.py`
- `tests/` - Unit tests for transforms
- `output/` - Generated nodes and edges (gitignored)
  - `release-metadata.yaml` - Per-build manifest of upstream sources, versions, artifacts (kozahub-metadata-schema)
- `data/` - Downloaded source data (gitignored)

## Key Commands

- `just run` - Full pipeline (download -> preprocess -> transform)
- `just download` - Download phenopacket data from phenopacket-store
- `just preprocess` - Extract phenopackets to JSONL format
- `just transform-all` - Run all transforms
- `just transform <name>` - Run specific transform
- `just metadata` - Emit `output/release-metadata.yaml`
- `just test` - Run tests

## Preprocessing

This ingest requires a preprocessing step to extract phenopacket data from the zip archive and convert to JSONL:
```bash
just preprocess
```

This uses the PhenopacketRegistryService to extract and parse phenopackets.

## Release Metadata

Every kozahub ingest emits an `output/release-metadata.yaml` describing the upstream sources, their versions, the artifacts produced, and the versions of build-time tools. This file is the contract monarch-ingest reads to assemble the merged knowledge graph's release receipt.

`src/versions.py` is the only per-ingest piece — it implements `get_source_versions()` returning a list of SourceVersion dicts. The `kozahub_metadata_schema` package provides reusable fetchers for the common patterns (HTTP Last-Modified, GitHub releases, URL-path regex, file-header parsing). The boilerplate (transform-content hashing, tool versions, build_version composition, yaml emission) is handled by `scripts/write_metadata.py`.

The `kozahub-metadata-schema` repo is expected as a sibling checkout (path-dep). Switch to a git or PyPI dep once published.

## Skills

- `.claude/skills/create-koza-ingest.md` - Create new koza ingests
- `.claude/skills/update-template.md` - Update to latest template version
