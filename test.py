import logging

from trailwatch import AwsConnector, configure, watch

logger = logging.getLogger("integration")
logger.setLevel(logging.DEBUG)


configure(
    project="symphony-careport-sync",
    project_description=(
        "Synchronize appointments between Careport and Symphony Care's Salesforce"
    ),
    environment="staging",
    connectors=[
        # AwsConnector(
        #     url="http://host.docker.internal:8000",
        #     api_key="test",
        # ),
        AwsConnector(
            url="https://nb569mjiu7.execute-api.us-west-2.amazonaws.com",
            api_key="zYdZ4u7rguAA2QnXenOra4Jr5ENK1FeL",
        ),
    ],
    loggers=["integration"],
    execution_ttl=3600 * 24 * 7,
    log_ttl=3600 * 24 * 7,
    error_ttl=3600 * 24 * 7,
)


@watch(job_description="Receive appointment from Careport")
def receive_appointments():
    logger.debug("Received appointment")
    logger.info("Sent appointment to SQS")


@watch()
def upsert_appointments():
    """Upsert appointments to Salesforce."""
    logger.info("Hello from %s", __file__)
    raise ValueError("BAM!!!")


if __name__ == "__main__":
    receive_appointments()
    upsert_appointments()
