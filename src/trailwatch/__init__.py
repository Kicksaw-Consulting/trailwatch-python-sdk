__all__ = [
    "configure",
    "TrailwatchContext",
    "watch",
]

import functools

from typing import Optional

from .config import configure
from .context import TrailwatchContext


def watch(
    job: Optional[str] = None,
    job_description: Optional[str] = None,
):
    def wrapper(func):
        decorator_kwargs = {
            "job": job or func.__name__,
            "job_description": job_description or func.__doc__,
        }
        if decorator_kwargs["job_description"] is None:
            raise ValueError(
                "Job description must either be provided or set as a docstring"
            )

        @functools.wraps(func)
        def inner(*args, **kwargs):
            with TrailwatchContext(**decorator_kwargs):
                return func(*args, **kwargs)

        return inner

    return wrapper
