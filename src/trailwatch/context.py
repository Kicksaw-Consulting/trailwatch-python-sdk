from __future__ import annotations

import datetime
import logging
import traceback

from types import TracebackType
from typing import Optional, Type, Union

import requests

from .config import NOTSET, TrailwatchConfig
from .connectors.aws.api import TrailwatchApi
from .connectors.aws.handler import TrailwatchHandler
from .exceptions import TrailwatchError


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
        self.session = requests.Session()
        self.config = TrailwatchConfig(
            job=job,
            job_description=job_description,
            loggers=loggers,
            execution_ttl=execution_ttl,
            log_ttl=log_ttl,
            error_ttl=error_ttl,
        )
        self.api = TrailwatchApi(self.session, self.config)
        self.execution_id = None
        self.handler = None

    def __enter__(self) -> TrailwatchContext:
        self.api.upsert_project(self.config.project, self.config.project_description)
        self.api.upsert_environment(self.config.environment)
        self.api.upsert_job(
            self.config.job,
            self.config.job_description,
            self.config.project,
        )
        self.execution_id = self.api.create_execution(
            self.config.project,
            self.config.environment,
            self.config.job,
        )

        # Register handlers
        self.handler = TrailwatchHandler(execution_id=self.execution_id, api=self.api)
        self.handler.setLevel(logging.NOTSET)
        for logger_name in self.config.loggers:
            _logger = logging.getLogger(logger_name)
            _logger.addHandler(self.handler)

        return self

    def __exit__(
        self,
        exc_type: Optional[Type[Exception]],
        exc_value: Optional[Exception],
        exc_traceback: Optional[TracebackType],
    ) -> bool:
        end = datetime.datetime.utcnow()
        self.api.update_execution(
            self.execution_id,
            "failure" if exc_type is not None else "success",
            end,
        )

        # Upload error and traceback to trailwatch server
        if exc_type is not None:
            self.api.create_error(
                execution_id=self.execution_id,
                timestamp=end,
                name=exc_type.__name__,
                message=str(exc_value),
                traceback="".join(
                    traceback.format_exception(
                        etype=exc_type,
                        value=exc_value,
                        tb=exc_traceback,
                    )
                ),
            )

        # Remove trailwatch handler from loggers
        for logger_name in self.config.loggers:
            _logger = logging.getLogger(logger_name)
            _logger.removeHandler(self.handler)

        if exc_type is None or issubclass(exc_type, TrailwatchError):
            return True
        return False
