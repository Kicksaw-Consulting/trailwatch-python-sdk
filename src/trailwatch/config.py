from dataclasses import dataclass, field

from trailwatch.connectors.base import ConnectorFactory

from .exceptions import NotConfiguredError


class Default:
    """
    Sentinel value to indicate that user did not set a value.

    Used to distinguish between None and using globally configured value.

    """


DEFAULT = Default()


@dataclass(frozen=True)
class SharedConfiguration:
    is_configured: bool = False
    connectors: list[ConnectorFactory] = field(default_factory=list)

    project: str = ""
    project_description: str = ""
    environment: str = ""
    loggers: list[str] = field(default_factory=list)
    execution_ttl: int | None = None
    log_ttl: int | None = None
    error_ttl: int | None = None


class TrailwatchConfig:
    shared_configuration: SharedConfiguration = SharedConfiguration()

    # Job-specific properties
    job: str
    job_description: str

    # Shared properties which can be overridden for each job
    _loggers: list[str] | Default | None
    _execution_ttl: int | Default | None
    _log_ttl: int | Default | None
    _error_ttl: int | Default | None

    def __init__(
        self,
        job: str,
        job_description: str,
        loggers: list[str] | Default | None = DEFAULT,
        execution_ttl: int | Default | None = DEFAULT,
        log_ttl: int | Default | None = DEFAULT,
        error_ttl: int | Default | None = DEFAULT,
    ) -> None:
        """
        Initialize a TrailwatchConfig instance for a job.

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
            By default, global configuration is used.
        log_ttl : int, optional
            Time to live for the log records in seconds.
            By default, global configuration is used.
        error_ttl : int, optional
            Time to live for the error records in seconds.
            By default, global configuration is used.

        """
        if not self.shared_configuration.is_configured:
            raise NotConfiguredError(
                "TrailWatch must be configured with trailwatch.configure() before using"
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
    def loggers(self) -> list[str]:
        if self._loggers is not DEFAULT:
            assert isinstance(self._loggers, (list, type(None)))
            return self._loggers or []
        return self.shared_configuration.loggers

    @property
    def execution_ttl(self) -> int | None:
        if self._execution_ttl is not DEFAULT:
            assert isinstance(self._execution_ttl, (int, type(None)))
            return self._execution_ttl
        return self.shared_configuration.execution_ttl

    @property
    def log_ttl(self) -> int | None:
        if self._log_ttl is not DEFAULT:
            assert isinstance(self._log_ttl, (int, type(None)))
            return self._log_ttl
        return self.shared_configuration.log_ttl

    @property
    def error_ttl(self) -> int | None:
        if self._error_ttl is not DEFAULT:
            assert isinstance(self._error_ttl, (int, type(None)))
            return self._error_ttl
        return self.shared_configuration.error_ttl


def configure(
    project: str,
    project_description: str,
    environment: str,
    connectors: list[ConnectorFactory],
    loggers: list[str] | None = None,
    execution_ttl: int | None = None,
    log_ttl: int | None = None,
    error_ttl: int | None = None,
):
    """
    Configure TrailWatch.

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
    connectors : list[ConnectorFactoryBase]
        List of connectors to use.
    loggers : list[str], optional
        List of loggers logs from which are sent to TrailWatch.
        By default, no logs are sent.
    execution_ttl : int, optional
        Time to live for the execution record in seconds.
        By default, the execution record is kept indefinitely.
    log_ttl : int, optional
        Time to live for the log records in seconds.
        By default, the log records are kept indefinitely.
    error_ttl : int, optional
        Time to live for the error records in seconds.
        By default, the error records are kept indefinitely.

    """
    if len(connectors) == 0:
        raise ValueError("At least one connector must be configured")
    TrailwatchConfig.shared_configuration = SharedConfiguration(
        is_configured=True,
        project=project,
        project_description=project_description,
        environment=environment,
        loggers=loggers or [],
        execution_ttl=execution_ttl,
        log_ttl=log_ttl,
        error_ttl=error_ttl,
        connectors=connectors,
    )
