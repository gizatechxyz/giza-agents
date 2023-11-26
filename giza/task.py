from functools import partial, wraps
from typing import Callable

from prefect import task as prefect_task


# def task(*args, **kwargs):
#     def decorator(func: Callable):
#         @wraps(func)
#         @prefect_task(*args, **kwargs)
#         def wrapper(*w_args, **w_kwargs):
#             return func(*w_args, **w_kwargs)
#         return wrapper
    
def task(func=None, *task_init_args, **task_init_kwargs):
    if func is None:
        return partial(task, *task_init_args, **task_init_kwargs)
    
    @wraps(func)
    def safe_func(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            return res
        except Exception as e:
            print(e)
    safe_func.__name__= func.__name__
    return prefect_task(safe_func, *task_init_args, **task_init_kwargs)
