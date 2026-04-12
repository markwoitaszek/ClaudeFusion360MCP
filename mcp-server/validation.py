"""Validation helpers for MCP tool parameters.

Each validator either returns the validated value or raises ValueError
with a descriptive message. FastMCP translates these to MCP error responses.
"""

from pathlib import Path

# Safe directories for export/import operations (pre-resolved at startup).
SAFE_EXPORT_DIRS = [
    (Path.home() / "Desktop").resolve(),
    (Path.home() / "Downloads").resolve(),
    (Path.home() / "Documents").resolve(),
]


def validate_filepath(filepath: str, allowed_extensions: list[str] | None = None) -> Path:
    """Validate that a filepath is within safe directories and has an allowed extension.

    Args:
        filepath: The user-provided filepath string.
        allowed_extensions: Optional list of allowed extensions (e.g., ['.stl', '.step']).

    Returns:
        The resolved Path if validation passes.

    Raises:
        ValueError: If the path is outside safe directories or has a disallowed extension.
    """
    if not filepath or not filepath.strip():
        raise ValueError("Filepath cannot be empty")

    if "\x00" in filepath:
        raise ValueError("Filepath contains null bytes")

    resolved = Path(filepath).expanduser().resolve()

    is_safe = any(resolved.is_relative_to(safe_dir) for safe_dir in SAFE_EXPORT_DIRS)
    if not is_safe:
        safe_names = ", ".join(f"~/{d.name}" for d in SAFE_EXPORT_DIRS)
        raise ValueError(f"Filepath is outside allowed directories. Allowed: {safe_names}")

    if allowed_extensions:
        ext = resolved.suffix.lower()
        if ext not in allowed_extensions:
            raise ValueError(f"File extension '{ext}' not allowed. Allowed extensions: {', '.join(allowed_extensions)}")

    return resolved


def validate_plane(plane: str) -> str:
    """Validate a construction plane name."""
    return validate_enum(plane, ["XY", "XZ", "YZ"], "plane")


def validate_axis(axis: str) -> str:
    """Validate a coordinate axis name."""
    return validate_enum(axis, ["X", "Y", "Z"], "axis")


def validate_enum(value: str, allowed: list[str], param_name: str) -> str:
    """Validate that a value is one of the allowed options."""
    if value not in allowed:
        raise ValueError(f"Invalid {param_name}: '{value}'. Must be one of: {', '.join(allowed)}")
    return value


def validate_positive(value: float, param_name: str) -> float:
    """Validate that a numeric value is positive (> 0)."""
    if value <= 0:
        raise ValueError(f"{param_name} must be positive, got {value}")
    return value


def validate_range(value: float, min_val: float, max_val: float, param_name: str) -> float:
    """Validate that a numeric value is within a range [min_val, max_val]."""
    if value < min_val or value > max_val:
        raise ValueError(f"{param_name} must be between {min_val} and {max_val}, got {value}")
    return value


def validate_count(value: int, min_val: int, param_name: str) -> int:
    """Validate that an integer count meets the minimum."""
    if value < min_val:
        raise ValueError(f"{param_name} must be at least {min_val}, got {value}")
    return value
