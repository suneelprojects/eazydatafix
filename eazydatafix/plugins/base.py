"""
Base class for EazyDataFix plugins.

This class provides optional metadata for plugins.
Existing plugins are NOT required to inherit from this class.
The registry will always use getattr() when reading metadata.
"""


class Plugin:
    """
    Optional base class for EazyDataFix plugins.

    Plugin authors may inherit from this class to obtain
    sensible metadata defaults, but inheritance is not required.
    """

    name = ""

    version = "0.0.0"

    author = ""

    description = ""
