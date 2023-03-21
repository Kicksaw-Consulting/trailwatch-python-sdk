import logging

from requests import Session

from trailwatch.config import TrailwatchConfig

from .api import TrailwatchApi
from .handler import TrailwatchHandler


class AwsConnector:
    def __init__(self, session: Session, config: TrailwatchConfig) -> None:
        self.api = TrailwatchApi(session, config)

        self.handler = TrailwatchHandler(self.api)

    def register_logger(self, logger: logging.Logger) -> None:
        logger.addHandler()
