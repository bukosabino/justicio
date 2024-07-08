import logging as lg
import time
import typing as tp
from functools import wraps

from langchain.schema import Document
from langchain.vectorstores import SupabaseVectorStore
from pydantic import BaseModel
from fastapi import Request
from opentelemetry import baggage, context
from langtrace_python_sdk.constants.instrumentation.common import (
    LANGTRACE_ADDITIONAL_SPAN_ATTRIBUTES_KEY,
)


class QAResponsePayloadModel(BaseModel):
    scoring_id: str
    context: tp.List[tp.Tuple[Document, float]]
    answer: str


def timeit(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger = lg.getLogger(func.__name__)
        logger.info("<<< Starting  >>>")
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        delta = end_time - start_time
        msg = f"{delta:2.2f}s" if delta > 1 else f"{1000 * delta:2.1f}ms"
        logger.info("<<< Completed >>> in %s", msg)
        return result

    return wrapper


async def inject_additional_attributes(fn, attributes=None):
    if attributes:
        new_ctx = baggage.set_baggage(
            LANGTRACE_ADDITIONAL_SPAN_ATTRIBUTES_KEY, attributes
        )
        context.attach(new_ctx)

    return await fn()
