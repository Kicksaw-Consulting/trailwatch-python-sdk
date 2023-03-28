<p align="center">
  <a href="https://github.com/Kicksaw-Consulting/trailwatch-python-sdk/actions/workflows/test.yml?query=event%3Apush+branch%3Amain" target="_blank">
      <img src="https://github.com/Kicksaw-Consulting/trailwatch-python-sdk/actions/workflows/test.yml/badge.svg?branch=main&event=push" alt="Test">
  </a>
  <a href="https://pypi.org/project/trailwatch" target="_blank">
      <img src="https://badge.fury.io/py/trailwatch.svg" alt="PyPI Package">
  </a>
</p>

- [Installation](#installation)
- [Getting Started](#getting-started)
- [Partial Success](#partial-success)

# Installation

```shell
pip install trailwatch
```

# Getting Started

```python
from trailwatch import configure, watch

configure(
  project="my-project",
  trailwatch_url="https://<random>.execute-api.us-west-2.amazonaws.com",
)

@watch()
def handler(event, context):
  # Do your thing
  return
```

# Partial Success

Raise a `PartialSuccess` exception to indicate that the execution was partially
successful. This exception is handled by Trailwatch to set execution status to `partial`
and will not be propagated to the caller.

```python
from trailwatch import configure, watch
from trailwatch.exceptions import PartialSuccessError

configure(
  project="my-project",
  trailwatch_url="https://<random>.execute-api.us-west-2.amazonaws.com",
)

@watch()
def handler(event, context):
  # Do your thing
  # You find out that only a subset of the work was successful
  # Log information about the failure normally using the logger
  raise PartialSuccessError
```
