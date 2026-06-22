"""Typed errors so the pipeline can fail clearly at each stage."""


class RecapError(Exception):
    """Base class for all recap pipeline errors."""


class InputValidationError(RecapError):
    """Raised when the event input is missing, malformed, or incomplete."""


class AssetError(RecapError):
    """Raised when an image asset is missing or unreadable."""


class StoryboardValidationError(RecapError):
    """Raised when a generated storyboard violates the storyboard contract."""


class StoryboardGenerationError(RecapError):
    """Raised when a storyboard provider fails to produce a usable storyboard."""


class RenderError(RecapError):
    """Raised when video rendering or export fails."""
