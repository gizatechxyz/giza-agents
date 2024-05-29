from functools import partial, wraps
from typing import Any

from prefect import task as prefect_task


def task(func: Any, *task_init_args: Any, **task_init_kwargs: Any) -> Any:
    if func is None:
        return partial(task, *task_init_args, **task_init_kwargs)

    @wraps(func)
    def safe_func(*args: Any, **kwargs: Any) -> Any:
        try:
            res = func(*args, **kwargs)
            return res
        except Exception as e:
            raise e

    safe_func.__name__ = func.__name__
    return prefect_task(safe_func, *task_init_args, **task_init_kwargs)
