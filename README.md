# phenopacket-ingest

Koza ingest for phenopacket data, transforming phenopackets from the [phenopacket-store](https://github.com/monarch-initiative/phenopacket-store) into Biolink model format for knowledge graph integration.

## Data Source

[Phenopacket Store](https://github.com/monarch-initiative/phenopacket-store) contains structured phenotypic data about rare disease cases in the GA4GH Phenopacket format.

Data is downloaded from: `https://github.com/monarch-initiative/phenopacket-store/releases/latest/download/all_phenopackets.zip`

## Output

This ingest produces:
- **Case nodes** - Individual cases with subject information
- **Case-to-phenotype associations** - Links cases to phenotypic features (HPO terms)
- **Case-to-disease associations** - Links cases to diseases (MONDO terms)
- **Case-to-gene associations** - Links cases to genes from interpretation data

## Entity ID Format

Case entities use IDs that include the cohort for proper URI resolution:
```
phenopacket.store:{cohort}.{phenopacket_id}
```

## Usage

```bash
# Install dependencies
just install

# Run full pipeline
just run

# Or run steps individually
just download      # Download phenopacket data
just preprocess    # Extract to JSONL
just transform-all # Run Koza transform
just test          # Run tests
```

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- [just](https://github.com/casey/just) command runner

## License

BSD-3-Clause
