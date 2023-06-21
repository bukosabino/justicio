import logging as lg

from fastapi import FastAPI

from src.utils import timeit
from src.initialize import initialize, setup_logging


setup_logging()

APP = FastAPI()

INIT_OBJECTS = initialize()

DEFAULT_INPUT_QUERY = (
    "Según la Ley Orgánica 10/2022: ¿Es de aplicación esta ley a niños (varones) menores de edad víctimas de "
    "violencias sexuales o solo a niñas y mujeres?"
)


@APP.get("/healthcheck")
@timeit
async def healthcheck():
    """Asynchronous Health Check"""
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


@APP.get("/qa")
@timeit
async def qa(input_query: str = DEFAULT_INPUT_QUERY):
    return {"message": "not developed yet"}
