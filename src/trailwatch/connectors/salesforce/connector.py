import datetime
import warnings

from types import TracebackType
from typing import TYPE_CHECKING, BinaryIO, Type

from simple_salesforce import Salesforce, format_soql

from trailwatch.connectors.base import Connector, ConnectorFactory

if TYPE_CHECKING:
    from trailwatch.config import TrailwatchConfig

NAMESPACE = "KicksawEng__"  # prefix for all custom Salesforce objects
INTEGRATION = "Integration__c"  # job
EXECUTION = "IntegrationExecution__c"  # execution


class SalesforceConnector(Connector):
    def __init__(
        self,
        config: "TrailwatchConfig",
        username: str,
        password: str,
        security_token: str,
        domain: str,
    ) -> None:
        self.config = config
        self.username = username
        self.password = password
        self.security_token = security_token
        self.domain = domain
        self.salesforce: Salesforce | None = None
        try:
            self.salesforce = Salesforce(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain,
            )
        except Exception as error:
            warnings.warn(f"Unable to connect to Salesforce due to: '{error}'")
            self.salesforce = None
        self.integration_object_id: str | None = None
        self.execution_object_id: str | None = None
        self.trailwatch_aws_execution_url: str | None = None

    def start_execution(self) -> None:
        if self.salesforce is None:
            return

        try:
            # Create integration
            response = self.salesforce.query_all(
                format_soql(
                    (
                        f"SELECT Id FROM {NAMESPACE}{INTEGRATION} "  # nosec
                        f"WHERE Name = {{name}}"
                    ),
                    name=self.config.job,
                )
            )
            if len(response["records"]) == 0:
                response = getattr(
                    self.salesforce,
                    f"{NAMESPACE}{INTEGRATION}",
                ).create(
                    {
                        "Name": self.config.job,
                        f"{NAMESPACE}LambdaName__c": None,
                    }
                )
                self.integration_object_id = response["id"]
            else:
                assert len(response["records"]) == 1
                self.integration_object_id = response["records"][0]["Id"]

            # Create execution
            response = getattr(
                self.salesforce,
                f"{NAMESPACE}{EXECUTION}",
            ).create(
                {
                    f"{NAMESPACE}{INTEGRATION}": self.integration_object_id,
                    f"{NAMESPACE}ExecutionPayload__c": None,
                }
            )
            self.execution_object_id = response["id"]

        except Exception as error:
            warnings.warn(f"Unable to start execution in Salesforce due to: '{error}'")
            return

    def finalize_execution(self, status: str, end: datetime.datetime) -> None:
        if self.execution_object_id is None:
            return

        try:
            response_payload = None
            if self.trailwatch_aws_execution_url is not None:
                response_payload = f"See details at {self.trailwatch_aws_execution_url}"

            # Set execution status (toggles checkbox to indicate success)
            if status == "success":
                getattr(
                    self.salesforce,
                    f"{NAMESPACE}{EXECUTION}",
                ).update(
                    self.execution_object_id,
                    {
                        f"{NAMESPACE}ResponsePayload__c": response_payload,
                        f"{NAMESPACE}SuccessfulCompletion__c": True,
                    },
                )
            else:
                getattr(
                    self.salesforce,
                    f"{NAMESPACE}{EXECUTION}",
                ).update(
                    self.execution_object_id,
                    {
                        f"{NAMESPACE}ResponsePayload__c": response_payload,
                        f"{NAMESPACE}SuccessfulCompletion__c": False,
                        f"{NAMESPACE}ErrorMessage__c": f"Soft error: {status}",
                    },
                )
        except Exception as error:
            warnings.warn(
                f"Unable to finalize execution in Salesforce due to: '{error}'"
            )
            return

    def handle_exception(
        self,
        timestamp: datetime.datetime,
        exc_type: Type[Exception],
        exc_value: Exception,
        exc_traceback: TracebackType,
    ):
        if self.execution_object_id is None:
            return

        try:
            # Add exception to execution
            message = f"{exc_type.__name__}: {exc_value}"
            getattr(
                self.salesforce,
                f"{NAMESPACE}{EXECUTION}",
            ).update(
                self.execution_object_id,
                {
                    f"{NAMESPACE}SuccessfulCompletion__c": False,
                    f"{NAMESPACE}ErrorMessage__c": message[:1000],
                },
            )
        except Exception as error:
            warnings.warn(f"Unable to handle exception in Salesforce due to: '{error}'")
            return

    def send_fileobj(self, name: str, file: BinaryIO) -> None:
        # No-op: Salesforce integration app does not support file uploads
        pass


class SalesforceConnectorFactory(ConnectorFactory):
    def __init__(
        self,
        username: str,
        password: str,
        security_token: str,
        domain: str,
    ) -> None:
        self.username = username
        self.password = password
        self.security_token = security_token
        self.domain = domain

    def __call__(self, config: "TrailwatchConfig") -> Connector:
        return SalesforceConnector(
            config,
            self.username,
            self.password,
            self.security_token,
            self.domain,
        )
