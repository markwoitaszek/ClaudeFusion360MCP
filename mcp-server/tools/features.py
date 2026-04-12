"""3D feature operations, patterns, and boolean tools.

Tools: extrude, revolve, fillet, chamfer, shell, draft, combine,
       pattern_rectangular, pattern_circular, mirror
"""

from ipc import send_fusion_command
from mcp.server.fastmcp import FastMCP
from validation import validate_axis, validate_count, validate_enum, validate_plane, validate_positive

router = FastMCP("features")


@router.tool()
def extrude(distance: float, profile_index: int = 0, taper_angle: float = 0) -> dict:
    """Extrude the most recent sketch profile (units: cm).

    Args:
        distance: Extrusion distance (positive or negative)
        profile_index: Which profile if multiple exist (default 0)
        taper_angle: Draft angle during extrusion in degrees (default 0)
    """
    return send_fusion_command(
        "extrude", {"distance": distance, "profile_index": profile_index, "taper_angle": taper_angle}
    )


@router.tool()
def revolve(angle: float) -> dict:
    """Revolve the most recent sketch profile around an axis (degrees)."""
    return send_fusion_command("revolve", {"angle": angle})


@router.tool()
def fillet(radius: float, edges: list = None, body_index: int = None) -> dict:
    """Add fillets to edges of a body (units: cm).

    Args:
        radius: Fillet radius
        edges: Optional list of edge indices. If None, fillets all edges.
        body_index: Which body (default: most recent)

    Use get_body_info() to see available edge indices.
    """
    validate_positive(radius, "radius")
    params = {"radius": radius}
    if edges is not None:
        params["edges"] = edges
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("fillet", params)


@router.tool()
def chamfer(distance: float, edges: list = None, body_index: int = None) -> dict:
    """Add chamfers to edges of a body (units: cm).

    Args:
        distance: Chamfer distance
        edges: Optional list of edge indices. If None, chamfers all edges.
        body_index: Which body (default: most recent)

    Use get_body_info() to see available edge indices.
    """
    validate_positive(distance, "distance")
    params = {"distance": distance}
    if edges is not None:
        params["edges"] = edges
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("chamfer", params)


@router.tool()
def shell(thickness: float, faces_to_remove: list = None, body_index: int = None) -> dict:
    """Create a hollow shell from a solid body (units: cm).

    Args:
        thickness: Wall thickness
        faces_to_remove: List of face indices to remove (create openings). Default: closed shell.
        body_index: Which body (default: most recent)

    Examples:
        shell(thickness=0.2)                        # 2mm closed shell
        shell(thickness=0.15, faces_to_remove=[0])  # Open-top container

    Use get_body_info() to see available face indices.
    """
    validate_positive(thickness, "thickness")
    params = {"thickness": thickness}
    if faces_to_remove is not None:
        params["faces_to_remove"] = faces_to_remove
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("shell", params)


@router.tool()
def draft(
    angle: float,
    faces: list = None,
    body_index: int = None,
    pull_x: float = 0,
    pull_y: float = 0,
    pull_z: float = 1,
) -> dict:
    """Apply draft angles to faces for injection molding (angle in degrees).

    Args:
        angle: Draft angle (typically 0.5-3 degrees)
        faces: List of face indices. If None, drafts all faces.
        body_index: Which body (default: most recent)
        pull_x, pull_y, pull_z: Pull direction vector (default: +Z)
    """
    validate_positive(angle, "angle")
    params = {"angle": angle, "pull_x": pull_x, "pull_y": pull_y, "pull_z": pull_z}
    if faces is not None:
        params["faces"] = faces
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("draft", params)


@router.tool()
def combine(target_body: int, tool_bodies: list, operation: str = "cut", keep_tools: bool = False) -> dict:
    """Boolean operations: cut, join, or intersect bodies.

    Args:
        target_body: Index of body to modify (0 = first body)
        tool_bodies: List of body indices to use as tools
        operation: "cut" (subtract), "join" (add), or "intersect"
        keep_tools: If True, keep tool bodies after operation

    Examples:
        combine(target_body=0, tool_bodies=[1], operation="cut")    # Cut body1 from body0
        combine(target_body=0, tool_bodies=[1,2], operation="join")  # Merge 3 bodies

    Use get_body_info() to verify body indices before combining.
    """
    validate_enum(operation, ["cut", "join", "intersect"], "operation")
    return send_fusion_command(
        "combine",
        {"target_body": target_body, "tool_bodies": tool_bodies, "operation": operation, "keep_tools": keep_tools},
    )


@router.tool()
def pattern_rectangular(
    x_count: int, x_spacing: float, y_count: int = 1, y_spacing: float = 0, body_index: int = None
) -> dict:
    """Create a rectangular (linear) pattern of a body (spacing in cm).

    Args:
        x_count: Number of instances in X direction
        x_spacing: Spacing between instances in X
        y_count: Number of instances in Y direction (default 1)
        y_spacing: Spacing between instances in Y
        body_index: Which body (default: most recent)

    Example:
        pattern_rectangular(x_count=4, x_spacing=2.5, y_count=3, y_spacing=2.5)
    """
    validate_count(x_count, 2, "x_count")
    validate_positive(x_spacing, "x_spacing")
    if y_count > 1:
        validate_positive(y_spacing, "y_spacing")
    elif y_spacing and y_spacing > 0:
        raise ValueError("y_spacing is non-zero but y_count is 1; set y_count >= 2 to use Y direction")
    params = {"x_count": x_count, "x_spacing": x_spacing, "y_count": y_count, "y_spacing": y_spacing}
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("pattern_rectangular", params)


@router.tool()
def pattern_circular(count: int, angle: float = 360, axis: str = "Z", body_index: int = None) -> dict:
    """Create a circular (radial) pattern of a body.

    Args:
        count: Number of instances
        angle: Total angle in degrees (default 360 for full circle)
        axis: Rotation axis - "X", "Y", or "Z" (default "Z")
        body_index: Which body (default: most recent)
    """
    validate_count(count, 2, "count")
    validate_axis(axis)
    params = {"count": count, "angle": angle, "axis": axis}
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("pattern_circular", params)


@router.tool()
def mirror(plane: str = "YZ", body_index: int = None) -> dict:
    """Create a mirrored copy of a body.

    Args:
        plane: Mirror plane - "XY", "XZ", or "YZ" (default "YZ" for left-right symmetry)
        body_index: Which body (default: most recent)
    """
    validate_plane(plane)
    params = {"plane": plane}
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("mirror", params)
