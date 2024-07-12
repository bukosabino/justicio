import asyncio
import logging as lg
import time
import uuid
import os
import typing as tp
import ipaddress

import httpx
from fastapi import FastAPI

from src.initialize import initialize_app, initialize_logging
from src.utils import inject_additional_attributes, timeit
from langtrace_python_sdk import SendUserFeedback, langtrace
from langtrace_python_sdk.utils.with_root_span import with_langtrace_root_span

langtrace.init(api_key=os.environ.get('LANGTRACE_API_KEY'))
initialize_logging()

APP = FastAPI()

INIT_OBJECTS = initialize_app()

DEFAULT_INPUT_QUERY = (
    "¿Es de aplicación la ley de garantía integral de la libertad sexual a niños (varones) menores de edad "
    "víctimas de violencias sexuales o solo a niñas y mujeres?"
)
DEFAULT_COLLECTION_NAME = "justicio"


@with_langtrace_root_span()
async def call_llm_api(span_id, trace_id, model_name: str, messages: tp.List[tp.Dict[str, str]]):
    response = await INIT_OBJECTS.openai_client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=INIT_OBJECTS.config_loader["temperature"],
        seed=INIT_OBJECTS.config_loader["seed"],
        max_tokens=INIT_OBJECTS.config_loader["max_tokens"],
    )
    return response, span_id, trace_id


@APP.get("/healthcheck")
@timeit
async def healthcheck():
    """Asynchronous Health Check"""
    # TODO: healthcheck with embeddings db api and llm api
    return {"status": "OK"}


@APP.get("/semantic_search")
@timeit
async def semantic_search(input_query: str = DEFAULT_INPUT_QUERY, collection_name: str = DEFAULT_COLLECTION_NAME):
    logger = lg.getLogger(semantic_search.__name__)
    logger.info(input_query)
    docs = await INIT_OBJECTS.vector_store[collection_name].asimilarity_search_with_score(
        query=input_query, k=INIT_OBJECTS.config_loader["top_k_results"]
    )
    logger.info(docs)
    return docs


@APP.get("/semantic_search_tavily")
@timeit
async def semantic_search_tavily(input_query: str = DEFAULT_INPUT_QUERY):
    logger = lg.getLogger(semantic_search_tavily.__name__)
    logger.info(input_query)
    docs = INIT_OBJECTS.tavily_client.search(
        query=input_query,
        search_depth="advanced",
        include_domains=["https://www.boe.es/"],
        max_results=10,
        topic="general",
        include_raw_content=False,
        include_answer=False,
    )
    logger.info(docs)
    return docs


async def a_request_get(url):
    """Requests for sync/async load tests"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        return response.text


@APP.get("/qa_feedback")
@with_langtrace_root_span("Feedback")
@timeit
async def qa_feedback(span_id: str, trace_id: str, user_score: int):
    data = {
        "spanId": span_id, "traceId": trace_id, "userScore": user_score, "userId": None
    }
    SendUserFeedback().evaluate(data=data)
    return {"feedback": "OK"}


@APP.get("/qa")
@with_langtrace_root_span("RAG Justicio")
@timeit
async def qa(
    input_query: str = DEFAULT_INPUT_QUERY,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    model_name: str = INIT_OBJECTS.config_loader["llm_model_name"],
    input_original_query: str | None = None,
    ip_request_client: ipaddress.IPv4Address | None = None,
):
    logger = lg.getLogger(qa.__name__)
    logger.info(input_query)

    # Getting context from embedding database (Qdrant)
    docs = await INIT_OBJECTS.vector_store[collection_name].asimilarity_search_with_score(
        query=input_query, k=INIT_OBJECTS.config_loader["top_k_results"]
    )

    # Generate response using a LLM (OpenAI)
    context_preprocessed = [{"context": doc[0].page_content, "score": doc[1]} for doc in docs]
    messages = [
        {"role": "system", "content": INIT_OBJECTS.config_loader["prompt_system"]},
        {
            "role": "system",
            "content": INIT_OBJECTS.config_loader["prompt_system_context"],
        },
        {"role": "system", "content": "A continuación se proporciona el contexto:"},
        {"role": "system", "content": str(context_preprocessed)},
        {
            "role": "system",
            "content": "A continuación se proporciona la pregunta del usuario:",
        },
        {"role": "user", "content": input_query},
    ]
    # logger.info(messages)
    additional_attributes = {
        "db.collection.name": collection_name,
        "service.ip": ip_request_client,
        "llm.original_query": input_original_query
    }
    response, span_id, trace_id = await inject_additional_attributes(
        lambda: call_llm_api(model_name=model_name, messages=messages), additional_attributes
    )
    answer = response.choices[0].message.content
    logger.info(answer)
    logger.info(response.usage)

    response_payload = dict(
        scoring_id=str(uuid.uuid4()),
        context=docs,
        answer=answer,
        span_id=str(span_id),
        trace_id=str(trace_id),
    )
    return response_payload


@APP.get("/qa_tavily")
@timeit
async def qa_tavily(input_query: str = DEFAULT_INPUT_QUERY):
    logger = lg.getLogger(qa_tavily.__name__)
    logger.info(input_query)

    # Getting context from internet browser (Tavily)
    docs = INIT_OBJECTS.tavily_client.search(
        query=input_query,
        search_depth="advanced",
        include_domains=["https://www.boe.es/"],
        max_results=10,
        topic="general",
        include_raw_content=False,
        include_answer=False,
    )

    # Generate response using a LLM (OpenAI)
    context_preprocessed = [{"context": doc["content"], "score": doc["score"]} for doc in docs["results"]]

    response = await INIT_OBJECTS.openai_client.chat.completions.create(
        model=INIT_OBJECTS.config_loader["llm_model_name"],
        messages=[
            {"role": "system", "content": INIT_OBJECTS.config_loader["prompt_system"]},
            {
                "role": "system",
                "content": INIT_OBJECTS.config_loader["prompt_system_context"],
            },
            {"role": "system", "content": "A continuación se proporciona el contexto:"},
            {"role": "system", "content": str(context_preprocessed)},
            {
                "role": "system",
                "content": "A continuación se proporciona la pregunta del usuario:",
            },
            {"role": "user", "content": input_query},
        ],
        temperature=INIT_OBJECTS.config_loader["temperature"],
        seed=INIT_OBJECTS.config_loader["seed"],
        max_tokens=INIT_OBJECTS.config_loader["max_tokens"],
    )
    answer = response.choices[0].message.content
    logger.info(answer)
    logger.info(response.usage)

    response_payload = dict(
        scoring_id=str(uuid.uuid4()),
        context=docs,
        answer=answer,
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
