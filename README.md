<p align="center">
  <a href="https://github.com/Kicksaw-Consulting/trailwatch-python-sdk/actions/workflows/test.yml?query=event%3Apush+branch%3Amain" target="_blank">
      <img src="https://github.com/Kicksaw-Consulting/trailwatch-python-sdk/actions/workflows/test.yml/badge.svg?branch=main&event=push" alt="Test">
  </a>
  <a href="https://pypi.org/project/trailwatch" target="_blank">
      <img src="https://badge.fury.io/py/trailwatch.svg" alt="PyPI Package">
  </a>
</p>

- [Installation](#installation)
- [Using TrailWatch](#using-trailwatch)
  - [Decorator](#decorator)
  - [Context Manager](#context-manager)
- [Connectors](#connectors)
  - [AWS Connector](#aws-connector)
  - [Salesforce Connector](#salesforce-connector)
- [Control Execution Status](#control-execution-status)
  - [Partial Success](#partial-success)
  - [Timeout](#timeout)
- [Send a File](#send-a-file)
- [Using With Other Decorators](#using-with-other-decorators)

# Installation

Install the SDK (supports AWS server):

```shell
pip install trailwatch
```

Install with Salesforce connector support:

```shell
pip install trailwatch[salesforce]
```

# Using TrailWatch

## Decorator

This is the recommended way to use TrailWatch. Decorator will automatically
assign job name and description based on the function name and docstring.

```python
from trailwatch import configure, watch
from trailwatch.connectors.aws import AwsConnectorFactory

configure(
    project="My project name",
    project_description="My project description",
    environment="production",
    connectors=[
        AWSConnectorFactory(
            url="https://<random>.execute-api.us-west-2.amazonaws.com",
            api_key="my_key",
        )
    ],
    loggers=["__main__", "integration"],
)


@watch()
def handler(event, context):
  # Do your thing
  return
```

## Context Manager

Decorator uses this context manager internally. You can use the context manager
directly if you need more control over the execution or if you want to report a portion
of the execution (code block) as a separate job.

```python
from trailwatch import configure, TrailwatchContext
from trailwatch.connectors.aws import AwsConnectorFactory

configure(
    project="My project name",
    project_description="My project description",
    environment="production",
    connectors=[
        AWSConnectorFactory(
            url="https://<random>.execute-api.us-west-2.amazonaws.com",
            api_key="my_key",
        )
    ],
    loggers=["__main__", "integration"],
)


def handler(event, context):
    # Other code
    with TrailwatchContext(
        job="My Job",
        job_description="My job description",
    ) as execution:
        # Do your thing
        return
    # Other code
```

# Connectors

TwailWatch SDK works by attaching connectors to the execution context. Connectors
are responsible for tracking execution flow and for creating a record in their
respective systems. Connectors should be configured using the `configure` function
by provividing a list of connector factories in the `connectors` argument.

## AWS Connector

AWS connector is used to send execution information to AWS TrailWatch service deployed
in client's AWS account. To use AWS connector, you will need to deploy the TrailWatch
service first and then obtain URL and API key from the service.

```python
from trailwatch.connectors.aws import AwsConnectorFactory

configure(
    # Other configuration parameters
    connectors=[
        AWSConnectorFactory(
            url="url",
            api_key="key",
        )
    ],
)
```

## Salesforce Connector

Salesforce connector is used to send execution information to Kicksaw Integration App
deployed to client's Salesforce org. To use Salesforce connector, you will need to
deploy the Kicksaw Integration App first and then obtain credentials required to sign
in to the Salesforce org.

```python
from trailwatch.connectors.salesforce import SalesforceConnectorFactory

configure(
    # Other configuration parameters
    connectors=[
        SalesforceConnectorFactory(
            username="username",
            password="password",
            security_token="token",
            domain="domain",
        )
    ],
)
```

# Control Execution Status

## Partial Success

Raise a `PartialSuccess` exception to indicate that the execution was partially
successful. This exception is handled by TrailWatch to set execution status to `partial`
and will not be propagated to the caller.

```python
from trailwatch.exceptions import PartialSuccessError


@watch()
def handler(event, context):
    # Do your thing
    # You find out that only a subset of the work was successful
    # Log information about the failure normally using the logger
    raise PartialSuccessError
```

## Timeout

You can set timeout on a function to force it to stop after a certain amount of time.
This will raise `TimeoutError` and set the execution status to `timeout`.

> :warning: When using timeout inside AWS Lambda or Azure Function you will need to
> set the TrailWatch timeout to a value lower than the timeout you set on the cloud
> function. Otherwise, function can timeout before TrailWatch has a chance to set the
> status.

```python
@watch(timeout=10)
def handler(event, context):
    # Do something that takes more than 10 seconds
    ...
```

Or using the context manager:

```python
def handler(event, context):
    with TrailwatchContext(
        job="My Job",
        job_description="My job description",
        timeout=10,
    ) as execution:
        # Do something that takes more than 10 seconds
        ...
```

# Send a File

Some connectors support attaching (sending) files to be associated with the execution.
To send a file, use the `send_file` method on the `TrailwatchContext` object.
Three methods are available to send a file:

- `send_file` - send a file from the local filesystem
- `send_fileobj` - send a file-like object (stream or open file object)
- `send_file_content` - send a file content as a string or bytes

```python
def handler(event, context):
    with TrailwatchContext(
        job="My Job",
        job_description="My job description",
    ) as execution:
        execution.send_file("my_file.txt", "/path/to/my_file.txt")
        execution.send_fileobj("my_file.txt", open("my_file.txt", "rb"))
        execution.send_file_content("my_file.txt", "Hello from file!")
```

When using the decorator, you will need to add an extra argument
`trailwatch_execution_context` to the function you are decorating
to receive the `TrailwatchContext` object.

```python
from trailwatch import TrailwatchContext

@watch()
def handler(event, context, trailwatch_execution_context: TrailwatchContext):
    trailwatch_execution_context.send_file("my_file.txt", "/path/to/my_file.txt")
```

Connectors supporting sending files:

- AWS Connector

# Using With Other Decorators

When using TrailWatch with other decorators, make sure that TrailWatch decorator
is the innermost decorator. This is because TrailWatch decorator may inject
the context argument into the function and other decorators (like FastAPI) can
get confused by this argument.

```python
from fastapi import FastAPI, Path
from pydantic import BaseModel

app = FastAPI()


class Model(BaseModel):
    name: str


@app.post("/my_endpoint/{resource_id}")
@watch()
def my_endpoint(
    trailwatch_execution_context: TrailwatchContext
    model: Model,
    resource_id: str = Path(..., title="The ID of the resource to get"),
):
    # Do your thing
    return
```
