from typing import Any, Dict, List, Optional, Type, cast
import collections
import logging as lg
import os
import yaml

import pinecone
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.chains.query_constructor.ir import StructuredQuery
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.retrievers import SelfQueryRetriever
from langchain.retrievers.self_query.pinecone import PineconeTranslator
from langchain.vectorstores.pinecone import Pinecone
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.schema import Document


METADATA_FIELD_INFO = [
    AttributeInfo(
        name="identificador",
        description="Identificador del documento. Ejemplo: BOE-A-2022-14630",
        type="string",
    ),
    AttributeInfo(
        name="ambito_geografico",
        description="Comunidad Autónoma",
        type="string",
    ),
    AttributeInfo(
        name="año",
        description="Año de publicación",
        type="int",
    ),
    AttributeInfo(
        name="departamento",
        description="Alertas",
        type="string",
    ),
    AttributeInfo(
        name="materias",
        description="Materias",
        type="string",
    ),
    AttributeInfo(
        name="rango",
        description="Tipo de ley",
        type="string",
    )
]


class OwnSelfQueryRetriever(SelfQueryRetriever):

    def get_filters(self, query: str) -> StructuredQuery:
        """Get filters relevant for a query.

        Args:
            query: string to find relevant documents for

        Returns:
            Dict with query, filters and limit
        """
        return self.get_relevant_documents(query)

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Get documents relevant for a query.

        Args:
            query: string to find relevant documents for

        Returns:
            List of relevant documents
        """
        inputs = self.llm_chain.prep_inputs({"query": query})
        structured_query = cast(
            StructuredQuery,
            self.llm_chain.predict_and_parse(
                callbacks=run_manager.get_child(), **inputs
            ),
        )
        if self.verbose:
            print(structured_query)
        return structured_query


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
    self_query_retriever = _init_self_query_retriever(vector_store, config_loader)
    logger.info('Initialized application')
    init_objects = collections.namedtuple(
        'init_objects', ['config_loader', 'vector_store', 'retrieval_qa', 'self_query_retriever']
    )
    return init_objects(config_loader, vector_store, retrieval_qa, self_query_retriever)


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


def _init_self_query_retriever(vector_store, config_loader):
    logger = lg.getLogger(_init_self_query_retriever.__name__)
    logger.info("Initializing SelfQueryRetriever")

    from langchain.chains.query_constructor.ir import Comparator, Operator

    self_query_retriever = OwnSelfQueryRetriever.from_llm(
        llm=ChatOpenAI(model_name=config_loader['llm_model_name'], temperature=0),
        vectorstore=vector_store,
        document_contents="Leyes, disposiciones y actos de inserción obligatoria del estado español",
        metadata_field_info=METADATA_FIELD_INFO,
        structured_query_translator=PineconeTranslator(),
        chain_kwargs={
            'allowed_operators': [Operator.AND, Operator.OR],
            'allowed_comparators': [Comparator.EQ, Comparator.GT]
        },
        enable_limit=False,
        verbose=True,  # TODO: remove in production
        use_original_query=True
    )

    logger.info("Initialized SelfQueryRetriever")
    return self_query_retriever
