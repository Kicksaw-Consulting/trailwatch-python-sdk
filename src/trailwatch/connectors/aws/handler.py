import datetime
import logging

from .api import TrailwatchApi


class TrailwatchHandler(logging.Handler):
    def __init__(self, execution_id: str, api: TrailwatchApi):
        logging.Handler.__init__(self)
        self.execution_id = execution_id
        self.api = api

    def emit(self, record: logging.LogRecord):
        self.format(record)
        self.api.create_log(
            execution_id=self.execution_id,
            timestamp=datetime.datetime.utcfromtimestamp(record.created),
            name=record.name,
            levelno=record.levelno,
            lineno=record.lineno,
            msg=record.message,
            func=record.funcName,
        )
