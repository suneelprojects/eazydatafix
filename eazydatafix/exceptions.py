class EazyDataFixError(Exception):
    """
    Base exception for EazyDataFix.
    """


class EasyDataFixError(EazyDataFixError):
    """Backward-compatible spelling for :class:`EazyDataFixError`."""


class DatasetNotFoundError(EazyDataFixError):
    """
    Raised when the dataset file cannot be found.
    """


class InvalidDatasetError(EazyDataFixError):
    """
    Raised when the dataset cannot be loaded.
    """


class ConfigurationError(EazyDataFixError):
    """Raised when a public configuration is invalid."""


class WorkflowError(EazyDataFixError):
    """Raised when a deterministic workflow cannot complete safely."""
