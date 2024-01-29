import collections
import logging as lg
import os

import pinecone
import yaml
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.vectorstores.pinecone import Pinecone
from langchain.vectorstores.qdrant import Qdrant
from openai import AsyncOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from supabase.client import Client, create_client
from tavily import TavilyClient

from src.utils import StandardSupabaseVectorStore


def initialize_logging():
    logger = lg.getLogger()
    logger.info("Initializing logging")
    logger.handlers = []
    handler = lg.StreamHandler()
    formatter = lg.Formatter(
        "[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s] %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(lg.INFO)
    logger.info("Initialized logging")
    lg.getLogger("uvicorn.error").handlers = logger.handlers


def initialize_app():
    """Initializes the application"""
    logger = lg.getLogger(initialize_app.__name__)
    logger.info("Initializing application")
    config_loader = _init_config()
    vector_store = _init_vector_store(config_loader)
    openai_client = _init_openai_client()
    tavily_client = TavilyClient(api_key=os.environ['TAVILY_API_KEY'])
    # retrieval_qa = _init_retrieval_qa_llm(vector_store, config_loader)
    logger.info("Initialized application")
    init_objects = collections.namedtuple(
        "init_objects", ["config_loader", "vector_store", "openai_client", "tavily_client"]
    )
    return init_objects(config_loader, vector_store, openai_client, tavily_client)


def _init_config():
    yaml_config_path = os.path.join(os.environ["APP_PATH"], "config", "config.yaml")
    with open(yaml_config_path, "r") as stream:
        config_loader = yaml.safe_load(stream)
    return config_loader


def _init_vector_store(config_loader):
    logger = lg.getLogger(_init_vector_store.__name__)
    logger.info("Initializing vector store")
    if config_loader["vector_store"] == "pinecone":
        vector_store = _init_vector_store_pinecone(config_loader)
    elif config_loader["vector_store"] == "supabase":
        vector_store = _init_vector_store_supabase(config_loader)
    elif config_loader["vector_store"] == "qdrant":
        vector_store = _init_vector_store_qdrant(config_loader)
    else:
        raise ValueError("Vector Database not configured")
    return vector_store


def _init_vector_store_pinecone(config_loader):
    logger = lg.getLogger(_init_vector_store_pinecone.__name__)
    logger.info("Initializing vector store")
    pinecone.init(
        api_key=os.environ["PINECONE_API_KEY"],
        environment=os.environ["PINECONE_ENV"],
    )
    index_name = config_loader["vector_store_index_name"]
    index = pinecone.Index(index_name)
    embeddings = HuggingFaceEmbeddings(
        model_name=config_loader["embeddings_model_name"],
        model_kwargs={"device": "cpu"},
    )
    vector_store = Pinecone(index, embeddings.embed_query, "text")
    logger.info(pinecone.describe_index(index_name))
    logger.info(index.describe_index_stats())
    logger.info("Initialized vector store")
    return vector_store


def _init_vector_store_supabase(config_loader):
    from supabase.lib.client_options import ClientOptions

    logger = lg.getLogger(_init_vector_store_supabase.__name__)
    logger.info("Initializing vector store")
    supabase_client: Client = create_client(
        supabase_url=os.environ.get("SUPABASE_API_URL"),
        supabase_key=os.environ.get("SUPABASE_API_KEY"),
        options=ClientOptions(postgrest_client_timeout=60),
    )
    embeddings = HuggingFaceEmbeddings(
        model_name=config_loader["embeddings_model_name"],
        model_kwargs={"device": "cpu"},
    )
    vector_store = StandardSupabaseVectorStore(
        client=supabase_client,
        embedding=embeddings,
        table_name=config_loader["table_name"],
        query_name=config_loader["query_name"],
    )
    logger.info("Initialized vector store")
    return vector_store


def _init_vector_store_qdrant(config_loader):
    logger = lg.getLogger(_init_vector_store_qdrant.__name__)
    logger.info("Initializing vector store")
    qdrant_client = QdrantClient(
        url=os.environ["QDRANT_API_URL"],
        api_key=os.environ["QDRANT_API_KEY"],
        prefer_grpc=True,
    )
    embeddings = HuggingFaceEmbeddings(
        model_name=config_loader["embeddings_model_name"],
        model_kwargs={"device": "cpu"},
    )
    if len(qdrant_client.get_collections().collections) == 0:
        logger.info("Creating collection for vector store")
        qdrant_client.recreate_collection(
            collection_name=config_loader["collection_name"],
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            on_disk_payload=True,
        )
        logger.info("Created collection for vector store")
    vector_store = Qdrant(qdrant_client, config_loader["collection_name"], embeddings)
    logger.info("Initialized vector store")
    return vector_store


def _init_openai_client():
    logger = lg.getLogger(_init_openai_client.__name__)
    logger.info("Initializing OpenAI client")
    client = AsyncOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    logger.info("Initialized OpenAI client")
    return client


def _init_retrieval_qa_llm(vector_store, config_loader):
    # DEPRECATED
    logger = lg.getLogger(_init_retrieval_qa_llm.__name__)
    logger.info("Initializing RetrievalQA LLM")
    retriever = vector_store.as_retriever(
        search_type="similarity", search_kwargs={"k": config_loader["top_k_results"]}
    )
    system_template = f"{config_loader['prompt_system']}----------------\n{{context}}"
    messages = [
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template("{question}"),
    ]
    retrieval_qa = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(
            model_name=config_loader["llm_model_name"],
            temperature=config_loader["temperature"],
            max_tokens=config_loader["max_tokens"],
        ),
        chain_type="stuff",
        return_source_documents=True,
        retriever=retriever,
        chain_type_kwargs={"prompt": ChatPromptTemplate.from_messages(messages)},
    )
    logger.info(retrieval_qa.combine_documents_chain.llm_chain.prompt.format)
    logger.info("Initialized RetrievalQA LLM")
    return retrieval_qa
