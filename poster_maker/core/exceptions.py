class PosterMakerError(Exception):
    """Base exception for Poster Maker application."""
    pass

class MemoryLimitExceededError(PosterMakerError):
    """Raised when estimated memory usage exceeds safe limits."""
    def __init__(self, message: str, estimated_mb: float):
        self.estimated_mb = estimated_mb
        super().__init__(message)
