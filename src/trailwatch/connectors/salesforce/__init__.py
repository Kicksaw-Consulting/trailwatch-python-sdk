__all__ = [
    "SalesforceConnector",
]

try:
    from .connector import SalesforceConnector
except ImportError as error:
    raise ImportError(
        "You must install the 'salesforce' extra to use the Salesforce connector: "
        "pip install trailwatch[salesforce]"
    ) from error
