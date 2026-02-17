# Phenopacket Store

[Phenopacket Store](https://github.com/monarch-initiative/phenopacket-store) contains structured phenotypic data about rare disease cases in the [GA4GH Phenopacket](https://phenopacket-schema.readthedocs.io/) format. Each phenopacket describes an individual case with observed phenotypic features, disease diagnoses, and genomic interpretations.

Data is downloaded from: `https://github.com/monarch-initiative/phenopacket-store/releases/latest/download/all_phenopackets.zip`

## Case Entities

Case nodes represent individual subjects from phenopackets. Case IDs include the cohort for proper URI resolution:

```
phenopacket.store:{cohort}.{phenopacket_id}
```

**Biolink Captured:**

- `biolink:Case`
    - id (`phenopacket.store:{cohort}.{id}`)
    - name (subject ID from phenopacket)
    - has_biological_sex (when present)

## Case to Phenotype

Links cases to their observed phenotypic features using HPO terms.

**Biolink Captured:**

- `biolink:CaseToPhenotypicFeatureAssociation`
    - id (UUID)
    - subject (case ID)
    - predicate (`biolink:has_phenotype`)
    - object (HPO term ID)
    - negated (true when phenotypic feature is excluded)
    - onset_qualifier (ISO8601 age duration, when onset is available)
    - publications (PMIDs, when available)
    - primary_knowledge_source (`infores:phenopacket-store`)
    - knowledge_level (`observation`)
    - agent_type (`manual_agent`)

## Case to Disease

Links cases to their disease diagnoses.

**Biolink Captured:**

- `biolink:CaseToDiseaseAssociation`
    - id (UUID)
    - subject (case ID)
    - predicate (`biolink:has_disease`)
    - object (disease ID, typically MONDO)
    - onset_qualifier (ISO8601 age duration, when onset is available)
    - publications (PMIDs, when available)
    - primary_knowledge_source (`infores:phenopacket-store`)
    - knowledge_level (`observation`)
    - agent_type (`manual_agent`)

## Case to Gene

Links cases to genes from genomic interpretation data.

**Biolink Captured:**

- `biolink:CaseToGeneAssociation`
    - id (UUID)
    - subject (case ID)
    - predicate (`biolink:has_gene`)
    - object (gene ID)
    - publications (PMIDs, when available)
    - primary_knowledge_source (`infores:phenopacket-store`)
    - knowledge_level (`observation`)
    - agent_type (`manual_agent`)

## Citation

Danis D, Bamshad MJ, Bridges Y, Cacheiro P, Carmody LC, Chong JX, Coleman B, Dalgleish R, Freeman PJ, Graefe ASL, Groza T, Jacobsen JOB, Klocperk A, Kusters M, Ladewig MS, Marcello AJ, Mattina T, Mungall CJ, Munoz-Torres MC, Reese JT, Rehburg F, Reis BCS, Schuetz C, Smedley D, Strauss T, Sundaramurthi JC, Thun S, Wissink K, Wagstaff JF, Zocche D, Haendel MA, Robinson PN. A corpus of GA4GH Phenopackets: case-level phenotyping for genomic diagnostics and discovery. HGG Advances. 2025;6(1):100371. doi: 10.1016/j.xhgg.2024.100371. PMID: 39394689

## License

BSD-3-Clause
