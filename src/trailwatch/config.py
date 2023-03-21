from dataclasses import dataclass, field
from typing import Optional, Union

from .exceptions import NotConfiguredError

NOTSET = object()


@dataclass(frozen=True)
class SharedConfiguration:
    is_configured: bool = False

    project: str = ""
    project_description: str = ""
    environment: str = ""
    url: str = ""
    api_key: str = ""
    loggers: list[str] = field(default_factory=list)
    execution_ttl: Optional[int] = None
    log_ttl: Optional[int] = None
    error_ttl: Optional[int] = None


class TrailwatchConfig:
    shared_configuration: SharedConfiguration = SharedConfiguration()

    # Job-specific properties
    job: str
    job_description: str

    # Shared properties which can be overridden for each job
    _loggers: Union[Optional[list[str]], object]
    _execution_ttl: Union[Optional[int], object]
    _log_ttl: Union[Optional[int], object]
    _error_ttl: Union[Optional[int], object]

    def __init__(
        self,
        job: str,
        job_description: str,
        loggers: Union[Optional[list[str]], object] = NOTSET,
        execution_ttl: Union[Optional[int], object] = NOTSET,
        log_ttl: Union[Optional[int], object] = NOTSET,
        error_ttl: Union[Optional[int], object] = NOTSET,
    ) -> None:
        """
        Initialize a TrailwatchConfig instance for a job.

        Parameters
        ----------
        job : str
            Job name. E.g., 'Upsert appointments'.
        job_description : str
            Job description. E.g., 'Upsert appointments from ModMed to Salesforce'.
        loggers : Optional[list[str]], optional
            List of loggers logs from which are sent to Trailwatch.
            By default, no logs are sent.
        execution_ttl : Optional[int], optional
            Time to live for the execution record in seconds.
        log_ttl : Optional[int], optional
            Time to live for the log records in seconds.
        error_ttl : Optional[int], optional
            Time to live for the error records in seconds.

        """
        if not self.shared_configuration.is_configured:
            raise NotConfiguredError(
                "Trailwatch must be configured with trailwatch.configure() before using"
            )
        self.job = job
        self.job_description = job_description
        self._loggers = loggers or []
        self._execution_ttl = execution_ttl
        self._log_ttl = log_ttl
        self._error_ttl = error_ttl

    @property
    def project(self) -> str:
        return self.shared_configuration.project

    @property
    def project_description(self) -> str:
        return self.shared_configuration.project_description

    @property
    def environment(self) -> str:
        return self.shared_configuration.environment

    @property
    def url(self) -> str:
        return self.shared_configuration.url

    @property
    def api_key(self) -> str:
        return self.shared_configuration.api_key

    @property
    def loggers(self) -> list[str]:
        if self._loggers is not NOTSET:
            assert isinstance(self._loggers, (list, type(None)))
            return self._loggers or []
        return self.shared_configuration.loggers

    @property
    def execution_ttl(self) -> Optional[int]:
        if self._execution_ttl is not NOTSET:
            assert isinstance(self._execution_ttl, (int, type(None)))
            return self._execution_ttl
        return self.shared_configuration.execution_ttl

    @property
    def log_ttl(self) -> Optional[int]:
        if self._log_ttl is not NOTSET:
            assert isinstance(self._log_ttl, (int, type(None)))
            return self._log_ttl
        return self.shared_configuration.log_ttl

    @property
    def error_ttl(self) -> Optional[int]:
        if self._error_ttl is not NOTSET:
            assert isinstance(self._error_ttl, (int, type(None)))
            return self._error_ttl
        return self.shared_configuration.error_ttl


def configure(
    project: str,
    project_description: str,
    environment: str,
    url: str,
    api_key: str,
    loggers: Optional[list[str]] = None,
    execution_ttl: Optional[int] = None,
    log_ttl: Optional[int] = None,
    error_ttl: Optional[int] = None,
):
    """
    Configure Trailwatch.

    This function configures global settings shared across all executions unless
    explicitly overridden for a specific job.
    This function must be called once per process.

    Parameters
    ----------
    project : str
        Short name of the project.
        E.g., 'companyname-middleware'.
    project_description : str
        User-friendly description of the project.
        E.g., 'Synchronize appointment data from ModMed with companyname's Salesforce'.
    environment : str
        Environment in which all jobs are executed.
        E.g., 'production', 'staging', 'development'.
    url : str
        URL pointing to TrailWatch instance deployed on AWS.
        E.g., 'https://somerandomstring.execute-api.us-west-2.amazonaws.com'.
    api_key : str
        API key to be included in the 'x-api-key' header when calling the REST API.
    loggers : Optional[list[str]], optional
        List of loggers logs from which are sent to Trailwatch.
        By default, no logs are sent.
    execution_ttl : Optional[int], optional
        Time to live for the execution record in seconds.
    log_ttl : Optional[int], optional
        Time to live for the log records in seconds.
    error_ttl : Optional[int], optional
        Time to live for the error records in seconds.

    """
    TrailwatchConfig.shared_configuration = SharedConfiguration(
        is_configured=True,
        project=project,
        project_description=project_description,
        environment=environment,
        url=url,
        api_key=api_key,
        loggers=loggers or [],
        execution_ttl=execution_ttl,
        log_ttl=log_ttl,
        error_ttl=error_ttl,
    )
