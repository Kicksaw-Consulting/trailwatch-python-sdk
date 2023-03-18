import logging

import requests

from .config import TrailwatchConfig


class TrailwatchHandler(logging.Handler):
    __trailwatch_config: TrailwatchConfig
    __requests_session: requests.Session
    __execution_id: str

    def __init__(
        self,
        config: TrailwatchConfig,
        session: requests.Session,
        execution_id: str,
    ):
        logging.Handler.__init__(self)
        self.__trailwatch_config = config
        self.__requests_session = session
        self.__execution_id = execution_id

    def emit(self, record: logging.LogRecord):
        self.format(record)
        self.__requests_session.post(
            "/".join(
                [
                    self.__trailwatch_config["url"],
                    "api",
                    "v1",
                    "logs",
                ]
            ),
            json={
                "execution_id": self.__execution_id,
                "timestamp": record.created,
                "name": record.name,
                "levelno": record.levelno,
                "lineno": record.lineno,
                "msg": record.message,
                "func": record.funcName,
                "ttl": self.__trailwatch_config["ttl"],
            },
            headers={"x-api-key": self.__trailwatch_config["api_key"]},
            timeout=30,
        )
