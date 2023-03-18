from typing import Optional, TypedDict


class TrailwatchConfig(TypedDict):
    project: str
    environment: str
    url: str
    """URL pointing to TrailWatch instance deployed on AWS"""
    api_key: str
    """API key to be included in the 'x-api-key' header"""
    loggers: list[str]
    """List of loggers logs from which are sent to Trailwatch"""
    job: str
    ttl: int


SHARED_CONFIGURATION: TrailwatchConfig = {
    "project": "",
    "environment": "",
    "url": "",
    "api_key": "",
    "loggers": ["trailwatch"],
    "job": "",
    "ttl": 60,
}
"""Parameters shared between trailwatch executions"""


def configure(
    project: str,
    environment: str,
    url: str,
    api_key: str,
    loggers: Optional[list[str]] = None,
):
    global SHARED_CONFIGURATION

    SHARED_CONFIGURATION["project"] = project
    SHARED_CONFIGURATION["environment"] = environment
    SHARED_CONFIGURATION["url"] = url.rstrip("/")
    SHARED_CONFIGURATION["api_key"] = api_key

    if loggers is None:
        loggers = []
    if "trailwatch" not in loggers:
        loggers.append("trailwatch")
    SHARED_CONFIGURATION["loggers"] = loggers
