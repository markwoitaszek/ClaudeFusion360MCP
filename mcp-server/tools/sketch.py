"""Sketch creation and geometry tools.

Tools: batch, create_sketch, finish_sketch, draw_rectangle, draw_circle,
       draw_line, draw_arc, draw_polygon, undo, delete_body, delete_sketch
"""

from ipc import send_fusion_command
from mcp.server.fastmcp import FastMCP
from validation import validate_count, validate_plane, validate_positive

router = FastMCP("sketch")


@router.tool()
def batch(commands: list) -> dict:
    """Execute multiple Fusion commands in a single call (all dimensions in cm).

    MUCH faster for complex operations — sends 5-10 commands in one round-trip.

    Example: batch([
        {"name": "create_sketch", "params": {"plane": "XY"}},
        {"name": "draw_rectangle", "params": {"x1": -5, "y1": -5, "x2": 5, "y2": 5}},
        {"name": "finish_sketch", "params": {}},
        {"name": "extrude", "params": {"distance": 3}}
    ])

    Stops on first error and returns partial results.
    """
    return send_fusion_command("batch", {"commands": commands})


@router.tool()
def create_sketch(plane: str, offset: float = 0) -> dict:
    """Create a new sketch on a construction plane (XY, XZ, or YZ) and enter edit mode.

    Args:
        plane: "XY" (horizontal), "XZ" (vertical front), or "YZ" (side)
        offset: Distance to offset sketch plane from origin (cm). Default 0.

    Examples:
        create_sketch(plane="XY")           # Horizontal at origin
        create_sketch(plane="XZ", offset=5) # Vertical, 5cm forward
    """
    validate_plane(plane)
    return send_fusion_command("create_sketch", {"plane": plane, "offset": offset})


@router.tool()
def finish_sketch() -> dict:
    """Exit sketch editing mode."""
    return send_fusion_command("finish_sketch", {})


@router.tool()
def draw_rectangle(x1: float, y1: float, x2: float, y2: float) -> dict:
    """Draw a rectangle in the active sketch (units: cm)."""
    return send_fusion_command("draw_rectangle", {"x1": x1, "y1": y1, "x2": x2, "y2": y2})


@router.tool()
def draw_circle(center_x: float, center_y: float, radius: float) -> dict:
    """Draw a circle in the active sketch (units: cm)."""
    validate_positive(radius, "radius")
    return send_fusion_command("draw_circle", {"center_x": center_x, "center_y": center_y, "radius": radius})


@router.tool()
def draw_line(x1: float, y1: float, x2: float, y2: float) -> dict:
    """Draw a straight line in the active sketch (units: cm)."""
    return send_fusion_command("draw_line", {"x1": x1, "y1": y1, "x2": x2, "y2": y2})


@router.tool()
def draw_arc(center_x: float, center_y: float, start_x: float, start_y: float, end_x: float, end_y: float) -> dict:
    """Draw an arc in the active sketch (units: cm)."""
    return send_fusion_command(
        "draw_arc",
        {
            "center_x": center_x,
            "center_y": center_y,
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
        },
    )


@router.tool()
def draw_polygon(center_x: float, center_y: float, radius: float, sides: int = 6) -> dict:
    """Draw a regular polygon in the active sketch (units: cm). Default is hexagon."""
    validate_positive(radius, "radius")
    validate_count(sides, 3, "sides")
    return send_fusion_command(
        "draw_polygon", {"center_x": center_x, "center_y": center_y, "radius": radius, "sides": sides}
    )


@router.tool()
def undo(count: int = 1) -> dict:
    """Undo recent operations.

    Args:
        count: Number of operations to undo (default 1)
    """
    validate_count(count, 1, "count")
    return send_fusion_command("undo", {"count": count})


@router.tool()
def delete_body(body_index: int = None) -> dict:
    """Delete a body by index.

    Args:
        body_index: Index of body to delete (default: most recent body)

    Use get_design_info() to see body count, get_body_info() for details.
    """
    params = {}
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("delete_body", params)


@router.tool()
def delete_sketch(sketch_index: int = None) -> dict:
    """Delete a sketch by index.

    Args:
        sketch_index: Index of sketch to delete (default: most recent sketch)

    Use get_design_info() to see sketch count.
    """
    params = {}
    if sketch_index is not None:
        params["sketch_index"] = sketch_index
    return send_fusion_command("delete_sketch", params)
