import collections
import logging as lg
import os
import yaml

import pinecone
from langchain.vectorstores.pinecone import Pinecone
from langchain.embeddings import HuggingFaceEmbeddings


def initialize():
    """
    Initiates the application

    :return:
    """
    logger = lg.getLogger(initialize.__name__)
    logger.info('Starting initialization of application')

    config_loader = _config_parser_setup()

    pinecone.init(
        api_key=os.environ['PINECONE_API_KEY'],
        environment=os.environ['PINECONE_ENV'],
    )
    index = pinecone.Index(config_loader['vector_store_index_name'])

    embeddings = HuggingFaceEmbeddings(
        model_name=config_loader['embeddings_model_name'], model_kwargs={'device': 'cpu'}
    )

    vector_store = Pinecone(index, embeddings.embed_query, "text")

    logger.info('Finished initialization of application')

    # TODO: check what objects we need
    init_objects = collections.namedtuple('init_objects', ['config_loader', 'embeddings', 'vector_store'])
    return init_objects(config_loader, embeddings, vector_store)


def _config_parser_setup():
    yaml_config_path = os.path.join(os.environ['APP_PATH'], 'config', 'config.yaml')
    with open(yaml_config_path, "r") as stream:
        config_loader = yaml.safe_load(stream)
    return config_loader
