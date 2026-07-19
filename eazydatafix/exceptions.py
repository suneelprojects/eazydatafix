class EasyDataFixError(Exception):
    """
    Base exception for Easy Data Fix.
    """


class DatasetNotFoundError(EasyDataFixError):
    """
    Raised when the dataset file cannot be found.
    """


class InvalidDatasetError(EasyDataFixError):
    """
    Raised when the dataset cannot be loaded.
    """
