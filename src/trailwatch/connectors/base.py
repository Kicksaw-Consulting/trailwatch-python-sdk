import datetime

from abc import ABC, abstractmethod
from types import TracebackType
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from trailwatch.config import TrailwatchConfig


class ConnectorBase(ABC):
    @abstractmethod
    def reset(self) -> None:
        ...

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        ...

    @abstractmethod
    def configure(self, config: "TrailwatchConfig") -> None:
        ...

    @abstractmethod
    def start_execution(self) -> None:
        ...

    @abstractmethod
    def finalize_execution(self, status: str, end: datetime.datetime) -> None:
        ...

    @abstractmethod
    def handle_exception(
        self,
        timestamp: datetime.datetime,
        exc_type: Type[Exception],
        exc_value: Exception,
        exc_traceback: TracebackType,
    ):
        ...
