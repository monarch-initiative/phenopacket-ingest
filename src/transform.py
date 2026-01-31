import koza
from koza.transform import KozaTransform

from phenopacket_ingest.transformer.phenopacket_transformer import PhenopacketTransformer


@koza.transform_record()
def transform(koza_app: KozaTransform, row: dict):
    entities = PhenopacketTransformer.process_record(row)
    if entities:
        koza_app.write(*entities)
