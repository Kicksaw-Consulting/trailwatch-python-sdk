import datetime
import warnings

from typing import BinaryIO

from requests import Response, Session


class TrailwatchApi:
    def __init__(self, session: Session, url: str, api_key: str) -> None:
        self.session = session
        self.url = url
        self.api_key = api_key

    def _make_request(self, method: str, url: str, **kwargs) -> Response | None:
        """
        Make a request to the TrailWatch API.

        Helper method to make a request to the TrailWatch API. This method
        will automatically add the API key to the request headers.
        Additionally, it will catch any exception and return None instead to
        avoid breaking the execution.

        Parameters
        ----------
        method : str
            _description_
        url : str
            _description_

        Returns
        -------
        Response | None
            _description_
        """
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
            warnings.warn(
                f"Failed to make '{method}' request to '{url}' due to: {error}"
            )
            return None

    def upsert_project(self, name: str, description: str) -> None:
        """
        Create or update a project.

        Parameters
        ----------
        name : str
            Project name.
        description : str
            Project description.

        """
        self._make_request(
            "PUT",
            "/".join([self.url, "api", "v1", "projects"]),
            json={"name": name, "description": description},
        )

    def upsert_environment(self, name: str) -> None:
        """
        Create or update an environment.

        Parameters
        ----------
        name : str
            Environment name.

        """
        self._make_request(
            "PUT",
            "/".join([self.url, "api", "v1", "environments"]),
            json={"name": name},
        )

    def upsert_job(self, name: str, description: str, project: str) -> None:
        """
        Create or update a job.

        Parameters
        ----------
        name : str
            Job name.
        description : str
            Job description.
        project : str
            Name of a project to which the job belongs to.

        """
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
        ttl: int | None,
    ) -> str | None:
        """
        Create an execution record.

        Parameters
        ----------
        project : str
            Project name.
        environment : str
            Environment name.
        job : str
            Job name.
        ttl : int, optional
            Time to live in seconds.
            If not provided, the execution will be kept forever.

        Returns
        -------
        str | None
            Execution ID or None if the request failed.

        """
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
            warnings.warn(f"Failed to create execution due to: '{error}'")
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
        ttl: int | None,
    ) -> None:
        """
        Create a log record.

        Parameters
        ----------
        execution_id : str
            Execution ID.
        timestamp : datetime.datetime
            Timestamp of the log record.
        name : str
            Name of the logger.
        levelno : int
            Log level number.
        lineno : int
            Source code line number.
        msg : str
            Log message.
        func : str
            Name of the function from which the log was created.
        ttl : int | None
            Time to live in seconds.
            If not provided, the log will be kept forever.

        """
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
        """
        Update an execution record.

        Parameters
        ----------
        execution_id : str
            Execution ID.
        status : str
            Execution status.
        end : datetime.datetime
            Execution end timestamp.

        """
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
        ttl: int | None,
    ) -> None:
        """
        Create an error record.

        Parameters
        ----------
        execution_id : str
            Execution ID.
        timestamp : datetime.datetime
            Timestamp of the error.
        name : str
            Error name.
        message : str
            Error message.
        traceback : str
            Traceback.
        ttl : int | None
            Time to live in seconds.
            If not provided, the error will be kept forever.

        """
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

    def upload_file(
        self,
        execution_id: str,
        name: str,
        file: BinaryIO,
    ) -> None:
        """
        Upload a file.

        Parameters
        ----------
        execution_id : str
            Execution ID.
        name : str
            File name.
        file : BinaryIO
            File object.

        """
        try:
            # Get pre-signed upload URL
            response = self._make_request(
                "POST",
                "/".join(
                    [
                        self.url,
                        "api",
                        "v1",
                        "executions",
                        execution_id,
                        "files",
                    ]
                ),
                json={"file": name},
            )
            if response is None:
                return

            # Upload file
            response_json = response.json()
            response = self.session.post(
                response_json["url"],
                data=response_json["fields"],
                files={"file": file},
            )
            response.raise_for_status()
        except Exception as error:
            warnings.warn(f"Failed to upload file due to: '{error}'")
