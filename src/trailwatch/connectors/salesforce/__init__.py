__all__ = [
    "SalesforceConnectorFactory",
]

try:
    from .connector import SalesforceConnectorFactory
except ImportError as error:
    raise ImportError(
        "You must install the 'salesforce' extra to use the Salesforce connector: "
        "pip install trailwatch[salesforce]"
    ) from error
