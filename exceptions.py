"""Custom exception classes for Monitor IO Dashboard"""

class MonitorIOError(Exception):
    """Base exception for monitor-io related errors"""
    pass

class DataFetchError(MonitorIOError):
    """Raised when data fetching fails"""
    pass

class DataProcessingError(MonitorIOError):
    """Raised when data processing fails"""
    pass

class ValidationError(MonitorIOError):
    """Raised when input validation fails"""
    pass

class ConnectionError(MonitorIOError):
    """Raised when connection to monitor-io device fails"""
    pass

class ConfigurationError(MonitorIOError):
    """Raised when configuration is invalid"""
    pass