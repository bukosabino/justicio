import collections
import logging as lg
import os
import yaml

import pinecone
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.vectorstores.pinecone import Pinecone
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI


def initialize_logging():
    logger = lg.getLogger()
    logger.info('Initializing logging')
    logger.handlers = []
    handler = lg.StreamHandler()
    formatter = (
        lg.Formatter('[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s] %(message)s')
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(lg.INFO)
    logger.info('Initialized logging')
    lg.getLogger('uvicorn.error').handlers = logger.handlers


def initialize_app():
    """Initializes the application
    """
    logger = lg.getLogger(initialize_app.__name__)
    logger.info('Initializing application')
    config_loader = _init_config()
    vector_store = _init_vector_store(config_loader)
    retrieval_qa = _init_retrieval_qa_llm(vector_store, config_loader)
    logger.info('Initialized application')
    init_objects = collections.namedtuple('init_objects', ['config_loader', 'vector_store', 'retrieval_qa'])
    return init_objects(config_loader, vector_store, retrieval_qa)


def _init_config():
    yaml_config_path = os.path.join(os.environ['APP_PATH'], 'config', 'config.yaml')
    with open(yaml_config_path, "r") as stream:
        config_loader = yaml.safe_load(stream)
    return config_loader


def _init_vector_store(config_loader):
    logger = lg.getLogger(_init_vector_store.__name__)
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


def _init_retrieval_qa_llm(vector_store, config_loader):
    logger = lg.getLogger(_init_retrieval_qa_llm.__name__)
    logger.info("Initializing RetrievalQA LLM")
    retriever = vector_store.as_retriever()
    system_template = f"{config_loader['prompt_system']}----------------\n{{context}}"
    messages = [
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template("{question}"),
    ]
    retrieval_qa = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model_name=config_loader['llm_model_name'], temperature=0),
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={
            "prompt": ChatPromptTemplate.from_messages(messages),
            "verbose": True  # TODO: remove in production
        },
    )
    logger.info(retrieval_qa.combine_documents_chain.llm_chain.prompt.format)
    logger.info("Initialized RetrievalQA LLM")
    return retrieval_qa
