import datetime
import logging
import traceback

from types import TracebackType
from typing import TYPE_CHECKING, Optional, Type

from requests import Session

from trailwatch.connectors.base import ConnectorBase
from trailwatch.exceptions import NotConfiguredError

from .api import TrailwatchApi
from .handler import TrailwatchHandler

if TYPE_CHECKING:
    from trailwatch.config import TrailwatchConfig

logger = logging.getLogger(__name__)


class AwsConnector(ConnectorBase):
    __config: Optional["TrailwatchConfig"]
    __api: Optional[TrailwatchApi]
    __is_configured: bool
    __execution_id: Optional[str]
    __handler: Optional[TrailwatchHandler]

    def __init__(self, url: str, api_key: str) -> None:
        """
        Configure Trailwatch AWS connector.

        Parameters
        ----------
        url : str
            URL pointing to TrailWatch instance deployed on AWS.
            E.g., 'https://somerandomstring.execute-api.us-west-2.amazonaws.com'.
        api_key : str
            API key to be included in the 'x-api-key' header when calling the REST API.

        """
        self.url = url
        self.api_key = api_key

        self.__config = None
        self.__api = None
        self.__is_configured = False
        self.__execution_id = None
        self.__handler = None

    def reset(self) -> None:
        self.__config = None
        self.__api = None
        self.__is_configured = False
        self.__execution_id = None
        self.__handler = None

    @property
    def is_configured(self) -> bool:
        return self.__is_configured

    def configure(self, config: "TrailwatchConfig") -> None:
        self.__config = config
        self.__api = TrailwatchApi(Session(), self.url, self.api_key)
        self.__is_configured = True

    @property
    def config(self) -> "TrailwatchConfig":
        if not self.is_configured:
            raise NotConfiguredError("AwsConnector is not configured")
        assert self.__config is not None
        return self.__config

    @property
    def api(self) -> TrailwatchApi:
        if not self.is_configured:
            raise NotConfiguredError("AwsConnector is not configured")
        assert self.__api is not None
        return self.__api

    def start_execution(self) -> None:
        # Create entries in Trailwatch database
        self.api.upsert_project(
            self.config.project,
            self.config.project_description,
        )
        self.api.upsert_environment(self.config.environment)
        self.api.upsert_job(
            self.config.job,
            self.config.job_description,
            self.config.project,
        )
        self.__execution_id = self.api.create_execution(
            self.config.project,
            self.config.environment,
            self.config.job,
            self.config.execution_ttl,
        )

        # Register logging handlers
        if self.__execution_id is not None:
            self.__handler = TrailwatchHandler(
                self.__execution_id,
                self.api,
                self.config.log_ttl,
            )
            for logger_name in self.config.loggers:
                logging.getLogger(logger_name).addHandler(self.__handler)

    def finalize_execution(self, status: str, end: datetime.datetime) -> None:
        if self.__execution_id is not None:
            self.api.update_execution(self.__execution_id, status, end)

        # Remove logging handlers
        if self.__handler is not None:
            for logger_name in self.config.loggers:
                logging.getLogger(logger_name).removeHandler(self.__handler)

    def handle_exception(
        self,
        timestamp: datetime.datetime,
        exc_type: Type[Exception],
        exc_value: Exception,
        exc_traceback: TracebackType,
    ):
        if self.__execution_id is not None:
            self.api.create_error(
                execution_id=self.__execution_id,
                timestamp=timestamp,
                name=exc_type.__name__,
                message=str(exc_value),
                traceback="".join(
                    traceback.format_exception(
                        etype=exc_type,
                        value=exc_value,
                        tb=exc_traceback,
                    )
                ),
                ttl=self.config.error_ttl,
            )
