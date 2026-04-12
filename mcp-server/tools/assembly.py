"""Component, assembly, and joint tools.

Tools: create_component, list_components, delete_component, check_interference,
       move_component, rotate_component, create_revolute_joint, create_slider_joint,
       set_joint_angle, set_joint_distance
"""

from ipc import send_fusion_command
from mcp.server.fastmcp import FastMCP
from validation import validate_axis

router = FastMCP("assembly")


@router.tool()
def create_component(name: str = None) -> dict:
    """Convert the most recent body into a new component for assembly."""
    params = {}
    if name:
        params["name"] = name
    return send_fusion_command("create_component", params)


@router.tool()
def list_components() -> dict:
    """List all components with names, positions, and bounding boxes."""
    return send_fusion_command("list_components", {})


@router.tool()
def delete_component(name: str = None, index: int = None) -> dict:
    """Delete a component by name or index."""
    params = {}
    if name:
        params["name"] = name
    if index is not None:
        params["index"] = index
    return send_fusion_command("delete_component", params)


@router.tool()
def check_interference() -> dict:
    """Check if any components overlap (bounding box collision detection)."""
    return send_fusion_command("check_interference", {})


@router.tool()
def move_component(
    x: float = 0, y: float = 0, z: float = 0, index: int = None, name: str = None, absolute: bool = True
) -> dict:
    """Move a component to a new position (units: cm).

    Args:
        x, y, z: Target position or offset
        index: Component index (from list_components)
        name: Component name (alternative to index)
        absolute: If True, set absolute position. If False, move by offset.

    CRITICAL: Use this to position components after creation to avoid overlaps.
    """
    params = {"x": x, "y": y, "z": z, "absolute": absolute}
    if index is not None:
        params["index"] = index
    if name is not None:
        params["name"] = name
    return send_fusion_command("move_component", params)


@router.tool()
def rotate_component(
    angle: float,
    axis: str = "Z",
    index: int = None,
    name: str = None,
    origin_x: float = 0,
    origin_y: float = 0,
    origin_z: float = 0,
) -> dict:
    """Rotate a component around an axis (angle in degrees).

    Args:
        angle: Rotation angle in degrees
        axis: Rotation axis - "X", "Y", or "Z" (default "Z")
        index: Component index (from list_components)
        name: Component name (alternative to index)
        origin_x, origin_y, origin_z: Rotation origin point (cm)
    """
    validate_axis(axis)
    params = {"angle": angle, "axis": axis, "origin_x": origin_x, "origin_y": origin_y, "origin_z": origin_z}
    if index is not None:
        params["index"] = index
    if name is not None:
        params["name"] = name
    return send_fusion_command("rotate_component", params)


@router.tool()
def create_revolute_joint(
    component1_index: int = None,
    component2_index: int = None,
    x: float = 0,
    y: float = 0,
    z: float = 0,
    axis_x: float = 0,
    axis_y: float = 0,
    axis_z: float = 1,
    min_angle: float = None,
    max_angle: float = None,
    flip: bool = False,
) -> dict:
    """Create a revolute (rotating) joint between two components."""
    params = {"x": x, "y": y, "z": z, "axis_x": axis_x, "axis_y": axis_y, "axis_z": axis_z, "flip": flip}
    if component1_index is not None:
        params["component1_index"] = component1_index
    if component2_index is not None:
        params["component2_index"] = component2_index
    if min_angle is not None:
        params["min_angle"] = min_angle
    if max_angle is not None:
        params["max_angle"] = max_angle
    return send_fusion_command("create_revolute_joint", params)


@router.tool()
def create_slider_joint(
    component1_index: int = None,
    component2_index: int = None,
    x: float = 0,
    y: float = 0,
    z: float = 0,
    axis_x: float = 1,
    axis_y: float = 0,
    axis_z: float = 0,
    min_distance: float = None,
    max_distance: float = None,
) -> dict:
    """Create a slider (linear) joint between two components."""
    params = {"x": x, "y": y, "z": z, "axis_x": axis_x, "axis_y": axis_y, "axis_z": axis_z}
    if component1_index is not None:
        params["component1_index"] = component1_index
    if component2_index is not None:
        params["component2_index"] = component2_index
    if min_distance is not None:
        params["min_distance"] = min_distance
    if max_distance is not None:
        params["max_distance"] = max_distance
    return send_fusion_command("create_slider_joint", params)


@router.tool()
def set_joint_angle(angle: float, joint_index: int = None) -> dict:
    """Animate a revolute joint to a specific angle (degrees)."""
    params = {"angle": angle}
    if joint_index is not None:
        params["joint_index"] = joint_index
    return send_fusion_command("set_joint_angle", params)


@router.tool()
def set_joint_distance(distance: float, joint_index: int = None) -> dict:
    """Animate a slider joint to a specific distance (cm)."""
    params = {"distance": distance}
    if joint_index is not None:
        params["joint_index"] = joint_index
    return send_fusion_command("set_joint_distance", params)
