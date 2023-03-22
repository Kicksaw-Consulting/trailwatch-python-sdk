import datetime
import logging

from typing import Optional

from requests import Response, Session

logger = logging.getLogger(__name__)


class TrailwatchApi:
    def __init__(self, session: Session, url: str, api_key: str) -> None:
        self.session = session
        self.url = url
        self.api_key = api_key

    def _make_request(self, method: str, url: str, **kwargs) -> Optional[Response]:
        try:
            response = self.session.request(
                method,
                url,
                headers={"x-api-key": self.api_key},
                timeout=30,
                **kwargs,
            )
            response.raise_for_status()
            return response
        except Exception as error:
            logger.error(
                "Failed to make '%s' request to '%s' due to: '%s'",
                method,
                url,
                error,
            )
            return None

    def upsert_project(self, name: str, description: str) -> None:
        self._make_request(
            "PUT",
            "/".join([self.url, "api", "v1", "projects"]),
            json={"name": name, "description": description},
        )

    def upsert_environment(self, name: str) -> None:
        self._make_request(
            "PUT",
            "/".join([self.url, "api", "v1", "environments"]),
            json={"name": name},
        )

    def upsert_job(self, name: str, description: str, project: str) -> None:
        self._make_request(
            "PUT",
            "/".join([self.url, "api", "v1", "jobs"]),
            json={"name": name, "description": description, "project": project},
        )

    def create_execution(
        self,
        project: str,
        environment: str,
        job: str,
        ttl: Optional[int],
    ) -> Optional[str]:
        try:
            response = self._make_request(
                "POST",
                "/".join([self.url, "api", "v1", "executions"]),
                json={
                    "project": project,
                    "environment": environment,
                    "job": job,
                    "status": "running",
                    "start": datetime.datetime.utcnow().isoformat(),
                    "ttl": ttl,
                },
            )
            if response is None:
                return None
            return response.json()["id"]
        except KeyError as error:
            logger.error("Failed to create execution due to: '%s'", error)
            return None

    def create_log(
        self,
        execution_id: str,
        timestamp: datetime.datetime,
        name: str,
        levelno: int,
        lineno: int,
        msg: str,
        func: str,
        ttl: Optional[int],
    ) -> None:
        self._make_request(
            "POST",
            "/".join([self.url, "api", "v1", "logs"]),
            json={
                "execution_id": execution_id,
                "timestamp": timestamp.isoformat(),
                "name": name,
                "levelno": levelno,
                "lineno": lineno,
                "msg": msg,
                "func": func,
                "ttl": ttl,
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
            "/".join([self.url, "api", "v1", "executions", execution_id]),
            json={"status": status, "end": end.isoformat()},
        )

    def create_error(
        self,
        execution_id: str,
        timestamp: datetime.datetime,
        name: str,
        message: str,
        traceback: str,
        ttl: Optional[int],
    ) -> None:
        self._make_request(
            "POST",
            "/".join([self.url, "api", "v1", "errors"]),
            json={
                "execution_id": execution_id,
                "timestamp": timestamp.isoformat(),
                "name": name,
                "msg": message,
                "ttl": ttl,
                "traceback": traceback,
            },
        )
