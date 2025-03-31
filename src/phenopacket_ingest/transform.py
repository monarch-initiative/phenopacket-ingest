from koza.cli_utils import get_koza_app

from phenopacket_ingest.transformer.phenopacket_transformer import PhenopacketTransformer

koza_app = get_koza_app("phenopacket_ingest")

while (row := koza_app.get_row()) is not None:
    entities = PhenopacketTransformer.process_record(row)
    if entities:
        koza_app.write(*entities)
