import time
from functools import wraps


def retry(max_retries=3):
    """
    재시도 데코레이터
    Args:
        max_retries: 최대 재시도 횟수
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2**attempt)

        return wrapper

    return decorator
