import re
from pathlib import Path


def safe_artifact_path(
    output_directory: Path,
    relative_path: str | Path,
) -> Path:
    """
    Resolve an internal artifact path inside the requested output directory.

    Args:
        output_directory: Validated report output directory.
        relative_path: Library-controlled relative artifact path.

    Returns:
        Resolved artifact path.

    Raises:
        ValueError: If the artifact path escapes the output directory.
    """
    root = output_directory.resolve()
    target = (root / relative_path).resolve()

    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("Report artifact paths must remain inside the output directory.") from exc

    return target


def filename_slug(value: str) -> str:
    """
    Convert an artifact label into a deterministic safe filename component.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:48].rstrip("-") or "artifact"
