from typing import Protocol, Optional, Any

class ProgressCallback(Protocol):
    """Protocol for reporting progress updates."""
    
    def on_start(self, total: int, description: str) -> None:
        """Called when a long-running operation starts."""
        ...

    def on_update(self, advance: int = 1, message: Optional[str] = None) -> None:
        """Called to advance the progress."""
        ...

    def on_complete(self) -> None:
        """Called when operation is complete."""
        ...


class NoOpProgressCallback(ProgressCallback):
    """A progress callback that does nothing (for silent mode/API)."""
    
    def on_start(self, total: int, description: str) -> None:
        pass

    def on_update(self, advance: int = 1, message: Optional[str] = None) -> None:
        pass

    def on_complete(self) -> None:
        pass


class TqdmProgressCallback(ProgressCallback):
    """Progress callback using TQDM for CLI usage."""
    
    def __init__(self, unit: str = "it"):
        self.unit = unit
        self.pbar: Any = None

    def on_start(self, total: int, description: str) -> None:
        try:
            from tqdm import tqdm
            self.pbar = tqdm(total=total, desc=description, unit=self.unit)
        except ImportError:
            pass

    def on_update(self, advance: int = 1, message: Optional[str] = None) -> None:
        if self.pbar:
            if message:
                self.pbar.set_description(message)
            self.pbar.update(advance)

    def on_complete(self) -> None:
        if self.pbar:
            self.pbar.close()
            self.pbar = None
