import datetime

from types import TracebackType
from typing import Type

from .config import DEFAULT, Default, TrailwatchConfig
from .connectors.base import Connector
from .exceptions import ExecutionTimeoutError, PartialSuccessError, TrailwatchError


class TrailwatchContext:
    def __init__(
        self,
        job: str,
        job_description: str,
        loggers: list[str] | Default | None = DEFAULT,
        execution_ttl: int | Default | None = DEFAULT,
        log_ttl: int | Default | None = DEFAULT,
        error_ttl: int | Default | None = DEFAULT,
    ) -> None:
        """
        Initialize a TrailwatchContext instance for a job.

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
        log_ttl : int, optional
            Time to live for the log records in seconds.
        error_ttl : int, optional
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
        self.connectors: list[Connector] = []

    def __enter__(self) -> "TrailwatchContext":
        for connector_factory in self.config.shared_configuration.connectors:
            connector = connector_factory(self.config)
            connector.start_execution()
            self.connectors.append(connector)
        return self

    def __exit__(
        self,
        exc_type: Type[Exception] | None,
        exc_value: Exception | None,
        exc_traceback: TracebackType | None,
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
        for connector in self.connectors:
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
        if isinstance(exc_type, PartialSuccessError):
            return True
        return False
