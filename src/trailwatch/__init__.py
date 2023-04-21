__all__ = [
    "configure",
    "TrailwatchContext",
    "watch",
]

import functools
import inspect

from .config import DEFAULT, Default, configure
from .context import TrailwatchContext


def watch(
    job: str | None = None,
    job_description: str | None = None,
    loggers: list[str] | Default | None = DEFAULT,
    execution_ttl: int | Default | None = DEFAULT,
    log_ttl: int | Default | None = DEFAULT,
    error_ttl: int | Default | None = DEFAULT,
    timeout: int | None = None,
):
    """
    Watch a callable (function or method).

    This is a decorator that can be used to wrap a callable (function or method)
    and send execution statistics (start, end, name, logs, exceptions, etc.)
    to configured connectors.

    If decorated function takes a keyword argument named `trailwatch_execution_context`,
    the context object is passed to the function. You can ignore static analysis
    warnings about this argument not being used.

    Parameters
    ----------
    job : str
        Job name. E.g., 'Upsert appointments'.
    job_description : str
        Job description. E.g., 'Upsert appointments from ModMed to Salesforce'.
    loggers : list[str], optional
        List of loggers logs from which are sent to TrailWatch.
        By default, no logs are sent.
    execution_ttl : int, optional
        Time to live for the execution record in seconds.
        By default, global configuration is used.
    log_ttl : int, optional
        Time to live for the log records in seconds.
        By default, global configuration is used.
    error_ttl : int, optional
        Time to live for the error records in seconds.
        By default, global configuration is used.
    timeout : int, optional
        Timeout in seconds. If the callable takes longer than this to execute,
        an execution timeout error is raised and execution is marked as timed out.
        By default, no timeout is set.

    """

    def wrapper(func):
        if inspect.iscoroutinefunction(func):
            raise NotImplementedError("Coroutine functions are not supported")

        decorator_kwargs = {
            "job": job or func.__name__,
            "job_description": job_description
            or (inspect.cleandoc(func.__doc__) if func.__doc__ else None),
            "loggers": loggers,
            "execution_ttl": execution_ttl,
            "log_ttl": log_ttl,
            "error_ttl": error_ttl,
            "timeout": timeout,
        }
        if decorator_kwargs["job_description"] is None:
            raise ValueError(
                "Job description must either be provided explicitly or "
                "via the docstring of the decorated function"
            )

        @functools.wraps(func)
        def inner(*args, **kwargs):
            with TrailwatchContext(**decorator_kwargs) as tw_context:
                if "trailwatch_execution_context" in [
                    *inspect.getfullargspec(func).args,
                    *inspect.getfullargspec(func).kwonlyargs,
                ]:
                    return func(
                        *args,
                        **kwargs,
                        trailwatch_execution_context=tw_context,
                    )
                return func(*args, **kwargs)

        return inner

    return wrapper
