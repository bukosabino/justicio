import asyncio
import logging as lg
import time
import uuid

import httpx
from fastapi import FastAPI

from src.initialize import initialize_app, initialize_logging
from src.utils import timeit

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
    docs = await INIT_OBJECTS.vector_store.asimilarity_search_with_score(
        query=input_query, k=INIT_OBJECTS.config_loader["top_k_results"]
    )
    logger.info(docs)
    return docs


async def a_request_get(url):
    """Requests for sync/async load tests"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        return response.text


"""
@APP.get("/qa")
@timeit
async def qa(input_query: str = DEFAULT_INPUT_QUERY):
    # TODO: write a solution not using Langchain
    logger = lg.getLogger(qa.__name__)
    logger.info(input_query)
    answer = await INIT_OBJECTS.retrieval_qa.arun(input_query)
    response_payload = dict(scoring_id=str(uuid.uuid4()), context=docs, answer=answer)
    return response_payload
"""


@APP.get("/qa")
@timeit
async def qa(input_query: str = DEFAULT_INPUT_QUERY):
    # TODO: write a solution not using Langchain
    logger = lg.getLogger(qa.__name__)
    logger.info(input_query)
    response = INIT_OBJECTS.retrieval_qa(
        input_query
    )  # TODO: check if we can work async
    response_payload = dict(
        scoring_id=str(uuid.uuid4()),
        context=response["source_documents"],
        answer=response["result"],
    )
    return response_payload


@APP.get("/sleep")
@timeit
async def sleep():
    time.sleep(5)
    return {"status": "OK"}


@APP.get("/asleep")
@timeit
async def asleep():
    await asyncio.sleep(5)
    return {"status": "OK"}
