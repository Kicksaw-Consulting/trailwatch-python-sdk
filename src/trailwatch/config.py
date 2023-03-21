from typing import Optional, TypedDict


class TrailwatchConfig(TypedDict):
    project: str
    project_description: str
    environment: str
    url: str
    """URL pointing to TrailWatch instance deployed on AWS"""
    api_key: str
    """API key to be included in the 'x-api-key' header"""
    loggers: list[str]
    """List of loggers logs from which are sent to Trailwatch"""
    job: str
    job_description: str
    execution_ttl: Optional[int]
    log_ttl: Optional[int]
    error_ttl: Optional[int]


SHARED_CONFIGURATION: TrailwatchConfig = {
    "project": "",
    "project_description": "",
    "environment": "",
    "url": "",
    "api_key": "",
    "loggers": ["trailwatch"],
    "job": "",
    "job_description": "",
    "execution_ttl": None,
    "log_ttl": None,
    "error_ttl": None,
}
"""Parameters shared between trailwatch executions"""


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
    global SHARED_CONFIGURATION

    SHARED_CONFIGURATION["project"] = project
    SHARED_CONFIGURATION["project_description"] = project_description
    SHARED_CONFIGURATION["environment"] = environment
    SHARED_CONFIGURATION["url"] = url.rstrip("/")
    SHARED_CONFIGURATION["api_key"] = api_key

    if loggers is None:
        loggers = []
    if "trailwatch" not in loggers:
        loggers.append("trailwatch")
    SHARED_CONFIGURATION["loggers"] = loggers

    if execution_ttl is not None:
        SHARED_CONFIGURATION["execution_ttl"] = execution_ttl
    if log_ttl is not None:
        SHARED_CONFIGURATION["log_ttl"] = log_ttl
    if error_ttl is not None:
        SHARED_CONFIGURATION["error_ttl"] = error_ttl
