import datetime
import io
import signal

from pathlib import Path
from types import TracebackType
from typing import BinaryIO, Type

from .config import DEFAULT, Default, TrailwatchConfig
from .connectors.aws.connector import AwsConnector
from .connectors.base import Connector
from .exceptions import ExecutionTimeoutError, PartialSuccessError, TrailwatchError

try:
    from .connectors.salesforce.connector import SalesforceConnector
except ImportError:
    SalesforceConnector = None


def throw_timeout_on_alarm(signum, frame):
    raise ExecutionTimeoutError


signal.signal(signal.SIGALRM, throw_timeout_on_alarm)


class TrailwatchContext:
    """
    This is a context manager that should be used to wrap the execution of a job.

    It will initialize and attach connectors to the job execution, and finalize
    the execution when the context is exited.
    Connectors, depending on their implementation, do the following:
    - Create execution record (in AWS, Salesforce, etc.)
    - Capture logs from loggers, record them, and associate them with the execution
    - Capture exceptions, record them, and associate them with the execution
    - Allow sending files associated with an execution
    - Finalize the execution record by setting its status and end time

    """

    def __init__(
        self,
        job: str,
        job_description: str,
        loggers: list[str] | Default | None = DEFAULT,
        execution_ttl: int | Default | None = DEFAULT,
        log_ttl: int | Default | None = DEFAULT,
        error_ttl: int | Default | None = DEFAULT,
        timeout: int | None = None,
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
        timeout : int, optional
            Timeout in seconds. If the callable takes longer than this to execute,
            an execution timeout error is raised and execution is marked as timed out.
            By default, no timeout is set.

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
        self.timeout = timeout

    def send_file(self, file: Path | str) -> None:
        """
        Send a file to TrailWatch.

        This file will be associated with the execution.

        Parameters
        ----------
        file : Path | str
            File to send to all connectors supporting this feature.

        """
        if isinstance(file, str):
            file = Path(file)
        if not isinstance(file, Path):
            raise TypeError(
                f"'file' must be a 'pathlib.Path' or a 'str', "
                f"not '{type(file).__name__}"
            )
        assert isinstance(file, Path)
        with open(file, "rb") as file_stream:
            self.send_fileobj(file.name, file_stream)

    def send_fileobj(self, name: str, file: BinaryIO) -> None:
        """
        Send a file object to TrailWatch.

        This file will be associated with the execution.

        Parameters
        ----------
        name : str
            Name of the file.
        file : BinaryIO
            File object to send to all connectors supporting this feature.

        """
        for connector in self.connectors:
            connector.send_fileobj(name, file)

    def send_file_content(self, name: str, content: str | bytes) -> None:
        """
        Send a file content to TrailWatch.

        This file will be associated with the execution.

        Parameters
        ----------
        name : str
            Name of the file.
        content : str | bytes
            File content to send to all connectors supporting this feature.

        """
        if isinstance(content, str):
            content = content.encode(encoding="utf-8")
        if not isinstance(content, bytes):
            raise TypeError(
                f"'content' must be a 'bytes', not '{type(content).__name__}"
            )
        assert isinstance(content, bytes)
        self.send_fileobj(name, io.BytesIO(content))

    def __enter__(self) -> "TrailwatchContext":
        if self.timeout is not None:
            signal.alarm(self.timeout)
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
        # Add URL of execution on AWS to Salesforce connectors
        if SalesforceConnector is not None:
            url = None
            for connector in self.connectors:
                if isinstance(connector, AwsConnector):
                    url = connector.execution_url
                    break
            if url is not None:
                for connector in self.connectors:
                    if isinstance(connector, SalesforceConnector):
                        connector.trailwatch_aws_execution_url = url

        end = datetime.datetime.utcnow()
        if exc_type is None:
            status = "success"
        else:
            if exc_type is ExecutionTimeoutError:
                status = "timeout"
            elif exc_type is PartialSuccessError:
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

        # Return True to suppress any exception raised in the context
        if exc_type is PartialSuccessError:
            return True
        if exc_type is ExecutionTimeoutError:
            raise TimeoutError("Function execution was timed out by TrailWatch")

        # Return False to propagate any exception raised in the context
        return False
