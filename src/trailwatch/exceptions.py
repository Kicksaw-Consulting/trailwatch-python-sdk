class TrailwatchError(Exception):
    """Base exception for all trailwatch exceptions"""


class NotConfiguredError(TrailwatchError):
    """Exception raised when trailwatch is not configured"""


class ExecutionTimeoutError(TrailwatchError):
    """Exception raised when an execution times out"""


class PartialSuccessError(TrailwatchError):
    """Exception raised when an execution was partially successful"""
