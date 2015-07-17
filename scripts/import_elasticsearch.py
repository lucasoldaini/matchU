#!/usr/bin/python

# author:       Luca Soldaini
# email:        luca@soldaini.net
# description:  import AUIs in elasticsearch from MRCONSO

# default modules
import json

# installed modules

# project modules
from src.concept_importer import ElasticSearchScoller

from utils.config import parse_config
from utils.es_tools import create_index, bulk_create, connect



def driver(config):

    # create index
    with file(config.mapping_path) as f:
        mapping = json.load(f)
    create_kwargs = dict(config.elasticsearch)
    create_kwargs['mapping'] = mapping
    create_index(**create_kwargs)

    # connect to new index
    es = connect(**config.elasticsearch)

    doc_type = mapping['mappings'].keys()[0]
    scroller = ElasticSearchScoller(config.mrconso_path,
                                    config.elasticsearch.index, doc_type,
                                    notifiy_every=config.notifiy_every)
    bulk_create(client=es, docs=scroller, chunk_size=config.chunk_size)



if __name__ == '__main__':
    config = parse_config('config/import_elasticsearch.json')
    driver(config)
