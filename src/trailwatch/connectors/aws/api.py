import datetime

from requests import Response, Session

from trailwatch.config import TrailwatchConfig


class TrailwatchApi:
    def __init__(self, session: Session, config: TrailwatchConfig) -> None:
        self.session = session
        self.config = config

    def _make_request(self, method: str, url: str, **kwargs) -> Response:
        return self.session.request(
            method,
            url,
            headers={"x-api-key": self.config.api_key},
            timeout=30,
            **kwargs,
        )

    def upsert_project(self, name: str, description: str) -> None:
        self._make_request(
            "PUT",
            "/".join([self.config.url, "api", "v1", "projects"]),
            json={"name": name, "description": description},
        )

    def upsert_environment(self, name: str) -> None:
        self._make_request(
            "PUT",
            "/".join([self.config.url, "api", "v1", "environments"]),
            json={"name": name},
        )

    def upsert_job(self, name: str, description: str, project: str) -> None:
        self._make_request(
            "PUT",
            "/".join([self.config.url, "api", "v1", "jobs"]),
            json={"name": name, "description": description, "project": project},
        )

    def create_execution(self, project: str, environment: str, job: str) -> str:
        response = self._make_request(
            "POST",
            "/".join([self.config.url, "api", "v1", "executions"]),
            json={
                "project": project,
                "environment": environment,
                "job": job,
                "status": "running",
                "start": datetime.datetime.utcnow().isoformat(),
                "ttl": self.config.execution_ttl,
            },
        )
        return response.json()["id"]

    def create_log(
        self,
        execution_id: str,
        timestamp: datetime.datetime,
        name: str,
        levelno: int,
        lineno: int,
        msg: str,
        func: str,
    ) -> None:
        self._make_request(
            "POST",
            "/".join([self.config.url, "api", "v1", "logs"]),
            json={
                "execution_id": execution_id,
                "timestamp": timestamp.isoformat(),
                "name": name,
                "levelno": levelno,
                "lineno": lineno,
                "msg": msg,
                "func": func,
                "ttl": self.config.log_ttl,
            },
        )

    def update_execution(
        self,
        execution_id: str,
        status: str,
        end: datetime.datetime,
    ) -> None:
        self._make_request(
            "PATCH",
            "/".join([self.config.url, "api", "v1", "executions", execution_id]),
            json={"status": status, "end": end.isoformat()},
        )

    def create_error(
        self,
        execution_id: str,
        timestamp: datetime.datetime,
        name: str,
        message: str,
        traceback: str,
    ) -> None:
        self._make_request(
            "POST",
            "/".join([self.config.url, "api", "v1", "errors"]),
            json={
                "execution_id": execution_id,
                "timestamp": timestamp.isoformat(),
                "name": name,
                "msg": message,
                "ttl": self.config.error_ttl,
                "traceback": traceback,
            },
        )
