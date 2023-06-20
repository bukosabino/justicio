import collections
import logging as lg
import os
import yaml

import pinecone
from langchain.vectorstores.pinecone import Pinecone
from langchain.embeddings import HuggingFaceEmbeddings


# TODO: duplicated code


def setup_logging():
    logger = lg.getLogger()
    logger.info('Starting initialization of application')
    logger.handlers = []
    handler = lg.StreamHandler()
    formatter = (
        lg.Formatter('[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s] %(message)s')
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(lg.INFO)
    logger.info('Logging set up')


def initialize():
    """Initializes the application
    """
    logger = lg.getLogger(initialize.__name__)
    logger.info('Starting initialization of application')
    config_loader = _config_parser_setup()
    vector_store = _vector_store_setup(config_loader)
    logger.info('Finished initialization of application')
    init_objects = collections.namedtuple('init_objects', ['config_loader', 'vector_store'])
    return init_objects(config_loader, vector_store)


def _config_parser_setup():
    yaml_config_path = os.path.join(os.environ['APP_PATH'], 'config', 'config.yaml')
    with open(yaml_config_path, "r") as stream:
        config_loader = yaml.safe_load(stream)
    return config_loader


def _vector_store_setup(config_loader):
    logger = lg.getLogger(_vector_store_setup.__name__)
    logger.info("Initializing vector store")
    pinecone.init(
        api_key=os.environ['PINECONE_API_KEY'],
        environment=os.environ['PINECONE_ENV'],
    )
    index_name = config_loader['vector_store_index_name']
    index = pinecone.Index(index_name)
    embeddings = HuggingFaceEmbeddings(
        model_name=config_loader['embeddings_model_name'], model_kwargs={'device': 'cpu'}
    )
    vector_store = Pinecone(index, embeddings.embed_query, "text")
    logger.info(pinecone.describe_index(index_name))
    logger.info(index.describe_index_stats())
    logger.info("Initialized vector store")
    return vector_store
