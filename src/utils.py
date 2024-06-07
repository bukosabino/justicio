import asyncio
import logging as lg
import time
import typing as tp
from functools import wraps

from langchain.schema import Document
from langchain.vectorstores import SupabaseVectorStore
from pydantic import BaseModel


class StandardSupabaseVectorStore(SupabaseVectorStore):
    def similarity_search_with_score(
        self, query: str, k: int = 4, **kwargs: tp.Any
    ) -> tp.List[tp.Tuple[Document, float]]:
        return self.similarity_search_with_relevance_scores(query, k, **kwargs)


class QAResponsePayloadModel(BaseModel):
    scoring_id: str
    context: tp.List[tp.Tuple[Document, float]]
    answer: str


def timeit(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = lg.getLogger(func.__module__)
        logger.info("<<< Starting >>>")
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
        except Exception as e:
            logger.error("Exception occurred", exc_info=True)
            raise
        finally:
            end_time = time.time()
            delta = end_time - start_time
            msg = f"{delta:2.2f}s" if delta > 1 else f"{1000 * delta:2.1f}ms"
            logger.info("<<< Completed >>> in %s", msg)
        return result

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = lg.getLogger(func.__module__)
        logger.info("<<< Starting >>>")
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            logger.error("Exception occurred", exc_info=True)
            raise
        finally:
            end_time = time.time()
            delta = end_time - start_time
            msg = f"{delta:2.2f}s" if delta > 1 else f"{1000 * delta:2.1f}ms"
            logger.info("<<< Completed >>> in %s", msg)
        return result

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
