from __future__ import annotations

import datetime

from types import TracebackType
from typing import Optional, Type, Union

from .config import NOTSET, TrailwatchConfig
from .exceptions import ExecutionTimeoutError, PartialSuccessError, TrailwatchError


class TrailwatchContext:
    def __init__(
        self,
        job: str,
        job_description: str,
        loggers: Union[Optional[list[str]], object] = NOTSET,
        execution_ttl: Union[Optional[int], object] = NOTSET,
        log_ttl: Union[Optional[int], object] = NOTSET,
        error_ttl: Union[Optional[int], object] = NOTSET,
    ) -> None:
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
        log_ttl : Optional[int], optional
            Time to live for the log records in seconds.
        error_ttl : Optional[int], optional
            Time to live for the error records in seconds.

        """
        self.config = TrailwatchConfig(
            job=job,
            job_description=job_description,
            loggers=loggers,
            execution_ttl=execution_ttl,
            log_ttl=log_ttl,
            error_ttl=error_ttl,
        )

    def __enter__(self) -> TrailwatchContext:
        for connector in self.config.shared_configuration.connectors:
            connector.reset()
            connector.configure(self.config)
            connector.start_execution()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[Exception]],
        exc_value: Optional[Exception],
        exc_traceback: Optional[TracebackType],
    ) -> bool:
        end = datetime.datetime.utcnow()
        if exc_type is None:
            status = "success"
        else:
            if issubclass(exc_type, ExecutionTimeoutError):
                status = "timeout"
            elif issubclass(exc_type, PartialSuccessError):
                status = "partial"
            else:
                status = "failure"
        for connector in self.config.shared_configuration.connectors:
            connector.finalize_execution(status, end)
            if exc_type is not None and not issubclass(exc_type, TrailwatchError):
                assert exc_value is not None
                assert exc_traceback is not None
                connector.handle_exception(
                    timestamp=end,
                    exc_type=exc_type,
                    exc_value=exc_value,
                    exc_traceback=exc_traceback,
                )

        if exc_type is None or issubclass(exc_type, TrailwatchError):
            return True
        return False
