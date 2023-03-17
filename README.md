- [Installation](#installation)
- [Usage](#usage)

# Installation

```shell
pip install trailwatch
```

# Usage

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
