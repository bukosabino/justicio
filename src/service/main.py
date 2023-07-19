import logging as lg
import uuid

from fastapi import FastAPI

from src.utils import QAResponsePayloadModel, timeit
from src.initialize import initialize_app, initialize_logging


initialize_logging()

APP = FastAPI()

INIT_OBJECTS = initialize_app()

DEFAULT_INPUT_QUERY = (
    "Según la Ley Orgánica 10/2022: ¿Es de aplicación esta ley a niños (varones) menores de edad víctimas de "
    "violencias sexuales o solo a niñas y mujeres?"
)


@APP.get("/healthcheck")
@timeit
async def healthcheck():
    """Asynchronous Health Check"""
    # TODO: healthcheck with pinecone and openai
    return {"status": "OK"}


DEFAULT_INPUT_QUERY2 = """
En lo que se refiere a ciencia, i+d o comercio en Andalucia o Aragón, ¿qué Ley es la última 
que habla de las multas de las subvenciones? Sólo dentro del BOE-A-2019-1414
"""

@APP.get("/query_filter")
@timeit
async def query_filter(input_query: str = DEFAULT_INPUT_QUERY2):
    logger = lg.getLogger(query_filter.__name__)
    logger.info(input_query)
    filters = INIT_OBJECTS.self_query_retriever.get_filters(
        query=input_query
    )
    return filters


@APP.get("/semantic_search")
@timeit
async def semantic_search(input_query: str = DEFAULT_INPUT_QUERY):
    logger = lg.getLogger(semantic_search.__name__)
    logger.info(input_query)
    docs = INIT_OBJECTS.vector_store.similarity_search_with_score(
        query=input_query,
        k=INIT_OBJECTS.config_loader['top_k_results']
    )
    logger.info(docs)
    return docs


@APP.get("/qa", response_model=QAResponsePayloadModel)
@timeit
async def qa(input_query: str = DEFAULT_INPUT_QUERY):
    logger = lg.getLogger(qa.__name__)
    logger.info(input_query)
    docs = INIT_OBJECTS.vector_store.similarity_search_with_score(
        query=input_query,
        k=INIT_OBJECTS.config_loader['top_k_results']
    )
    answer = INIT_OBJECTS.retrieval_qa.run(input_query)
    response_payload = QAResponsePayloadModel(
        scoring_id=str(uuid.uuid4()),
        context=docs,
        answer=answer
    )
    return response_payload
