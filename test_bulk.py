import logging
import random
import time

from trailwatch import AwsConnector, configure, watch
from trailwatch.exceptions import PartialSuccessError

logger = logging.getLogger("integration")
logger.setLevel(logging.DEBUG)


def main():
    for project in ["symphony-careport-sync", "ventec-middleware"]:
        for environment in ["staging", "production"]:
            configure(
                project=project,
                project_description=f"{project} description",
                environment=environment,
                connectors=[
                    AwsConnector(
                        url="http://host.docker.internal:8000",
                        api_key="test",
                    ),
                    # AwsConnector(
                    #     url="https://nb569mjiu7.execute-api.us-west-2.amazonaws.com",
                    #     api_key="zYdZ4u7rguAA2QnXenOra4Jr5ENK1FeL",
                    # ),
                ],
                loggers=["integration"],
                execution_ttl=3600 * 24 * 7,
                log_ttl=3600 * 24 * 7,
                error_ttl=3600 * 24 * 7,
            )

            @watch(job_description="Receive appointment via webhook")
            def receive_appointments():
                logger.debug("Received appointment")
                time.sleep(random.random())
                logger.info("Sent appointment to SQS")
                time.sleep(random.random())
                logger.info("Sent appointment to SQS")

            @watch()
            def create_appointments():
                """Create appointments"""
                logger.info("Fetched 100 appointments from Salesforce")
                time.sleep(random.random())
                logger.debug("Creating appointments")
                time.sleep(random.random())
                raise RuntimeError("Client's server is down")

            @watch()
            def upsert_appointments():
                """Upsert appointments to Salesforce."""
                logger.info("Fetched 100 appointments from Salesforce")
                time.sleep(random.random())
                logger.debug("Upserting appointments to Salesforce")
                time.sleep(random.random())
                logger.warning("Some appointments were not upserted")
                raise PartialSuccessError

            try:
                receive_appointments()
            except Exception as e:
                print(e)

            try:
                create_appointments()
            except Exception as e:
                print(e)

            try:
                upsert_appointments()
            except Exception as e:
                print(e)


if __name__ == "__main__":
    main()
