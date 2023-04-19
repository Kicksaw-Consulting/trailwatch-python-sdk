import datetime

from abc import ABC, abstractmethod
from types import TracebackType
from typing import TYPE_CHECKING, BinaryIO, Type

if TYPE_CHECKING:
    from trailwatch.config import TrailwatchConfig


class Connector(ABC):
    @abstractmethod
    def start_execution(self) -> None:
        """Create execution record, attach handlers, etc."""

    @abstractmethod
    def finalize_execution(self, status: str, end: datetime.datetime) -> None:
        """Update execution record, detach handlers, etc."""

    @abstractmethod
    def handle_exception(
        self,
        timestamp: datetime.datetime,
        exc_type: Type[Exception],
        exc_value: Exception,
        exc_traceback: TracebackType,
    ):
        """Add exception to execution record (or do nothing)."""

    @abstractmethod
    def send_fileobj(self, name: str, file: BinaryIO) -> None:
        """Send a file to TrailWatch (or do nothing)."""


class ConnectorFactory(ABC):
    @abstractmethod
    def __call__(self, config: "TrailwatchConfig") -> Connector:
        """Create connector instance."""
