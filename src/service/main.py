import logging as lg
import uuid

from fastapi import FastAPI

from src.initialize import initialize_app, initialize_logging
from src.utils import QAResponsePayloadModel, timeit

initialize_logging()

APP = FastAPI()

INIT_OBJECTS = initialize_app()

DEFAULT_INPUT_QUERY = (
    "¿Es de aplicación la ley de garantía integral de la libertad sexual a niños (varones) menores de edad "
    "víctimas de violencias sexuales o solo a niñas y mujeres?"
)


@APP.get("/healthcheck")
@timeit
async def healthcheck():
    """Asynchronous Health Check"""
    # TODO: healthcheck with embeddings db api and llm api
    return {"status": "OK"}


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
