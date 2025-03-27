"""Test the full phenopacket-ingest pipeline from end to end."""
import os
import json
import logging
import zipfile
from pathlib import Path
from typing import List, Dict, Any

from phenopacket_ingest.registry import PhenopacketRegistryService
from phenopacket_ingest.transform import PhenopacketTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_pipeline():
    """Run the complete pipeline from extract to transform without relying on Koza."""
    data_dir = Path("data")
    output_dir = Path("manual_output")
    output_dir.mkdir(exist_ok=True)
    
    test_data_dir = Path("/tests/data/test_phenopackets")
    test_zip_path = Path("/Users/ck/Monarch/phenopacket-ingest/data/test_phenopackets.zip")
    
    with zipfile.ZipFile(test_zip_path, 'w') as zip_file:
        for json_file in test_data_dir.glob("*.json"):
            cohort_name = json_file.stem.split('_')[0]
            zip_file.write(json_file, f"{cohort_name}/phenopackets/{json_file.name}")
    

    registry = PhenopacketRegistryService()
    jsonl_path = registry.extract_phenopackets_to_jsonl(test_zip_path)

    nodes_file = output_dir / "nodes.tsv"
    edges_file = output_dir / "edges.tsv"
    
    with open(nodes_file, 'w') as nf:
        nf.write("id\tname\tcategory\tsymbol\tsex\tin_taxon\tin_taxon_label\tprovided_by\txref\treference\n")
    
    with open(edges_file, 'w') as ef:
        ef.write("id\tsubject\tpredicate\tobject\tknowledge_level\tagent_type\tprimary_knowledge_source\taggregator_knowledge_source\tpublications\n")
    
    node_count = 0
    edge_count = 0
    record_count = 0
    entity_counts = {}
    
    with open(jsonl_path, 'r') as f:
        for line in f:
            record_count += 1
            row = json.loads(line)
            
            try:
                entities = PhenopacketTransformer.process_row(row)
                
                for entity in entities:
                    entity_type = type(entity).__name__
                    entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
                    
                    if hasattr(entity, 'id') and not (hasattr(entity, 'subject') and hasattr(entity, 'object')):
                        # It's a node
                        node_count += 1
                        with open(nodes_file, 'a') as nf:
                            nf.write(f"{entity.id}\t")
                            nf.write(f"{getattr(entity, 'name', '')}\t")
                            nf.write(f"{getattr(entity, 'category', '')}\t")
                            nf.write(f"{getattr(entity, 'symbol', '')}\t")
                            nf.write(f"{getattr(entity, 'sex', '')}\t")
                            nf.write(f"{','.join(getattr(entity, 'in_taxon', [])) if hasattr(entity, 'in_taxon') and entity.in_taxon else ''}\t")
                            nf.write(f"{getattr(entity, 'in_taxon_label', '')}\t")
                            nf.write(f"{','.join(getattr(entity, 'provided_by', [])) if hasattr(entity, 'provided_by') and entity.provided_by else ''}\t")
                            nf.write(f"{','.join(getattr(entity, 'xref', [])) if hasattr(entity, 'xref') and entity.xref else ''}\t")
                            nf.write(f"{getattr(entity, 'reference', '')}\n")
                    
                    elif hasattr(entity, 'subject') and hasattr(entity, 'object'):
                        # It's an edge
                        edge_count += 1
                        with open(edges_file, 'a') as ef:
                            ef.write(f"{entity.id}\t")
                            ef.write(f"{entity.subject}\t")
                            ef.write(f"{entity.predicate}\t")
                            ef.write(f"{entity.object}\t")
                            ef.write(f"{getattr(entity, 'knowledge_level', '')}\t")
                            ef.write(f"{getattr(entity, 'agent_type', '')}\t")
                            ef.write(f"{getattr(entity, 'primary_knowledge_source', '')}\t")
                            ef.write(f"{','.join(getattr(entity, 'aggregator_knowledge_source', [])) if hasattr(entity, 'aggregator_knowledge_source') and entity.aggregator_knowledge_source else ''}\t")
                            ef.write(f"{','.join(getattr(entity, 'publications', [])) if hasattr(entity, 'publications') and entity.publications else ''}\n")
            
            except Exception as e:
                logger.error(f"Error processing record {record_count}: {e}")

    
    if test_zip_path.exists():
        os.remove(test_zip_path)

    return nodes_file, edges_file


if __name__ == "__main__":
    test_pipeline()