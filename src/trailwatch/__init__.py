__all__ = [
    "configure",
    "TrailwatchContext",
    "watch",
]

import functools

from typing import Optional, Union

from .config import NOTSET, configure
from .context import TrailwatchContext


# TODO - add timeout configuration; add support for uploading files
def watch(
    job: Optional[str] = None,
    job_description: Optional[str] = None,
    loggers: Union[Optional[list[str]], object] = NOTSET,
    execution_ttl: Union[Optional[int], object] = NOTSET,
    log_ttl: Union[Optional[int], object] = NOTSET,
    error_ttl: Union[Optional[int], object] = NOTSET,
):
    """
    Initialize a TrailwatchContext instance for a job.

    Parameters
    ----------
    job : str
        Job name. E.g., 'Upsert appointments'.
    job_description : str
        Job description. E.g., 'Upsert appointments from ModMed to Salesforce'.
    loggers : Optional[list[str]], optional
        List of loggers logs from which are sent to Trailwatch.
        By default, no logs are sent.
    execution_ttl : Optional[int], optional
        Time to live for the execution record in seconds.
        By default, global configuration is used.
    log_ttl : Optional[int], optional
        Time to live for the log records in seconds.
        By default, global configuration is used.
    error_ttl : Optional[int], optional
        Time to live for the error records in seconds.
        By default, global configuration is used.

    """

    def wrapper(func):
        decorator_kwargs = {
            "job": job or func.__name__,
            "job_description": job_description or func.__doc__,
            "loggers": loggers,
            "execution_ttl": execution_ttl,
            "log_ttl": log_ttl,
            "error_ttl": error_ttl,
        }
        if decorator_kwargs["job_description"] is None:
            raise ValueError(
                "Job description must either be provided explicitly or "
                "via the docstring of the decorated function"
            )

        @functools.wraps(func)
        def inner(*args, **kwargs):
            with TrailwatchContext(**decorator_kwargs):
                return func(*args, **kwargs)

        return inner

    return wrapper
