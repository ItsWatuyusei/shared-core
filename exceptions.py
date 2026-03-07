class SharedCoreError(Exception):
    """Base exception for all shared_core errors."""
    pass

class DatabaseConfigurationError(SharedCoreError):
    """Raised when database configuration is invalid or driver is missing."""
    def __init__(self, message: str, details: str = None):
        super().__init__(message)
        self.details = details
