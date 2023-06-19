from functools import wraps
import logging as lg
import time


def timeit(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = lg.getLogger(func.__name__)
        logger.info('<<< Starting  >>>')
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        delta = end_time - start_time
        msg = f'{delta:2.2f}s' if delta > 1 else f'{1000 * delta:2.1f}ms'
        logger.info('<<< Completed >>> in %s', msg)
        return result

    return wrapper
