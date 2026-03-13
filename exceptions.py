# ItsWatuyusei
# Copyright © ItsWatuyusei (https://ItsWatuyusei.com)

class SharedCoreError(Exception):

    pass

class DatabaseConfigurationError(SharedCoreError):

    def __init__(self, message: str, details: str = None):
        super().__init__(message)
        self.details = details
