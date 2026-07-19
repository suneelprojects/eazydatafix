from dataclasses import dataclass


@dataclass(slots=True)
class Recommendation:
    """
    Represents a recommendation to improve dataset quality.
    """

    title: str
    description: str
    priority: str
    category: str
    auto_fix_available: bool
