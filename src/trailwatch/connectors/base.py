import logging

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Optional, Type

from trailwatch.config import TrailwatchConfig


class Connector(ABC):
    def __init__(self, config: TrailwatchConfig) -> None:
        self.config = config

    @abstractmethod
    def register_logger(self, logger: logging.Logger):
        ...

    @abstractmethod
    def unregister_logger(self, logger: logging.Logger):
        ...

    @abstractmethod
    def handle_exception(
        self,
        exc_type: Optional[Type[Exception]],
        exc_value: Optional[Exception],
        exc_traceback: Optional[TracebackType],
    ):
        ...
