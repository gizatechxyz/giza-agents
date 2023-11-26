from functools import wraps
from typing import Callable

from prefect import task as prefect_task


def task(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return prefect_task(func)(*args, **kwargs)
    return wrapper
