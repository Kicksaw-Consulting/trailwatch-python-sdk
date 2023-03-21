from __future__ import annotations

import datetime
import logging
import traceback

from types import TracebackType
from typing import Optional, Type

import requests

from .config import SHARED_CONFIGURATION, TrailwatchConfig
from .exceptions import TrailwatchError
from .handler import TrailwatchHandler

trailwatch_logger = logging.getLogger("trailwatch")
trailwatch_logger.setLevel(logging.DEBUG)


class TrailwatchContext:
    session: requests.Session
    config: TrailwatchConfig
    execution: dict
    handler: TrailwatchHandler

    def __init__(
        self,
        job: str,
        job_description: str,
        execution_ttl: Optional[int] = None,
        log_ttl: Optional[int] = None,
        error_ttl: Optional[int] = None,
    ) -> None:
        self.session = requests.Session()
        self.config = TrailwatchConfig(**SHARED_CONFIGURATION)
        self.config["job"] = job
        self.config["job_description"] = job_description
        self.config["execution_ttl"] = execution_ttl
        self.config["log_ttl"] = log_ttl
        self.config["error_ttl"] = error_ttl

    def __enter__(self) -> TrailwatchContext:
        # Upsert project
        self.session.put(
            "/".join(
                [
                    self.config["url"],
                    "api",
                    "v1",
                    "projects",
                ]
            ),
            json={
                "name": self.config["project"],
                "description": self.config["project_description"],
            },
            headers={"x-api-key": self.config["api_key"]},
            timeout=30,
        )

        # Upsert environment
        self.session.put(
            "/".join(
                [
                    self.config["url"],
                    "api",
                    "v1",
                    "environments",
                ]
            ),
            json={
                "name": self.config["environment"],
            },
            headers={"x-api-key": self.config["api_key"]},
            timeout=30,
        )

        # Upsert job
        self.session.put(
            "/".join(
                [
                    self.config["url"],
                    "api",
                    "v1",
                    "jobs",
                ]
            ),
            json={
                "name": self.config["job"],
                "description": self.config["job_description"],
                "project": self.config["project"],
            },
            headers={"x-api-key": self.config["api_key"]},
            timeout=30,
        )

        # Create execution
        self.execution = self.session.post(
            "/".join(
                [
                    self.config["url"],
                    "api",
                    "v1",
                    "executions",
                ]
            ),
            json={
                "project": self.config["project"],
                "environment": self.config["environment"],
                "job": self.config["job"],
                "status": "running",
                "start": datetime.datetime.utcnow().isoformat(),
                "ttl": self.config["execution_ttl"],
            },
            headers={"x-api-key": self.config["api_key"]},
            timeout=30,
        ).json()

        # Register handlers
        self.handler = TrailwatchHandler(
            config=self.config,
            session=self.session,
            execution_id=self.execution["id"],
        )
        self.handler.setLevel(logging.NOTSET)
        for logger_name in self.config["loggers"]:
            _logger = logging.getLogger(logger_name)
            _logger.addHandler(self.handler)

        trailwatch_logger.info("Started execution")

        return self

    def __exit__(
        self,
        exc_type: Optional[Type[Exception]],
        exc_value: Optional[Exception],
        exc_traceback: Optional[TracebackType],
    ) -> bool:
        # Update execution status
        self.session.patch(
            "/".join(
                [
                    self.config["url"],
                    "api",
                    "v1",
                    "executions",
                    self.execution["id"],
                ]
            ),
            json={
                "status": "failure" if exc_type is not None else "success",
                "end": datetime.datetime.utcnow().isoformat(),
            },
            headers={"x-api-key": self.config["api_key"]},
            timeout=30,
        )

        # Upload error and traceback to trailwatch server
        if exc_type is not None:
            self.session.post(
                "/".join(
                    [
                        self.config["url"],
                        "api",
                        "v1",
                        "errors",
                    ]
                ),
                json={
                    "execution_id": self.execution["id"],
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "name": exc_type.__name__,
                    "msg": str(exc_value),
                    "ttl": self.config["error_ttl"],
                    "traceback": "".join(
                        traceback.format_exception(
                            etype=exc_type,
                            value=exc_value,
                            tb=exc_traceback,
                        )
                    ),
                },
                headers={"x-api-key": self.config["api_key"]},
                timeout=30,
            )

        # Close session
        self.session.close()

        trailwatch_logger.info("Finished execution")

        # Remove trailwatch handler from loggers
        for logger_name in self.config["loggers"]:
            _logger = logging.getLogger(logger_name)
            _logger.removeHandler(self.handler)

        if exc_type is None or issubclass(exc_type, TrailwatchError):
            return True
        return False
