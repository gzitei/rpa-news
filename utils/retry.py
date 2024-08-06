import traceback
import logging

logger = logging.getLogger("Retry")


def retry(retry_max=5, logger=logger):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(retry_max):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    logger.error(
                        f"{func.__name__} failed with error: {type(e)} - {e}"
                    )
                    if i == retry_max - 1:
                        logger.error(traceback.format_exc())
                        raise e
        return wrapper
    return decorator
