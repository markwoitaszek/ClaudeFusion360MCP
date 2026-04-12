"""Export/import, inspection, and measurement tools.

Tools: export_stl, export_step, export_3mf, import_mesh,
       get_design_info, get_body_info, measure, fit_view
"""

from ipc import send_fusion_command
from mcp.server.fastmcp import FastMCP
from validation import validate_enum, validate_filepath

router = FastMCP("io")


@router.tool()
def fit_view() -> dict:
    """Fit the viewport to show all geometry."""
    return send_fusion_command("fit_view", {})


@router.tool()
def get_design_info() -> dict:
    """Get information about the current design (name, body count, sketch count, component count, active sketch status)."""
    return send_fusion_command("get_design_info", {})


@router.tool()
def get_body_info(body_index: int = None) -> dict:
    """Get detailed information about a body including all edges and faces.

    Args:
        body_index: Which body (default: most recent)

    Returns edge indices with lengths, face indices with areas.
    Use this to find indices for selective fillet, chamfer, shell, or draft.
    """
    params = {}
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("get_body_info", params)


@router.tool()
def measure(
    measurement_type: str = "body", body_index: int = None, edge_index: int = None, face_index: int = None
) -> dict:
    """Measure dimensions of bodies, edges, or faces.

    Args:
        measurement_type: What to measure - "body", "edge", or "face"
        body_index: Which body (default: most recent)
        edge_index: Edge index (for measurement_type="edge")
        face_index: Face index (for measurement_type="face")

    Returns:
        body: volume, surface_area, bounding_box with size
        edge: length
        face: area
    """
    validate_enum(measurement_type, ["body", "edge", "face"], "measurement_type")
    params = {"type": measurement_type}
    if body_index is not None:
        params["body_index"] = body_index
    if edge_index is not None:
        params["edge_index"] = edge_index
    if face_index is not None:
        params["face_index"] = face_index
    return send_fusion_command("measure", params)


@router.tool()
def export_stl(filepath: str) -> dict:
    """Export the design as STL file for 3D printing.
    Filepath must be within allowed directories (~/Desktop, ~/Downloads, ~/Documents)."""
    validated = validate_filepath(filepath, allowed_extensions=[".stl"])
    return send_fusion_command("export_stl", {"filepath": str(validated)})


@router.tool()
def export_step(filepath: str) -> dict:
    """Export the design as STEP file (CAD standard).
    Filepath must be within allowed directories (~/Desktop, ~/Downloads, ~/Documents)."""
    validated = validate_filepath(filepath, allowed_extensions=[".step", ".stp"])
    return send_fusion_command("export_step", {"filepath": str(validated)})


@router.tool()
def export_3mf(filepath: str) -> dict:
    """Export the design as 3MF file (modern 3D printing format).
    Filepath must be within allowed directories (~/Desktop, ~/Downloads, ~/Documents)."""
    validated = validate_filepath(filepath, allowed_extensions=[".3mf"])
    return send_fusion_command("export_3mf", {"filepath": str(validated)})


@router.tool()
def import_mesh(filepath: str, unit: str = "mm") -> dict:
    """Import STL, OBJ, or 3MF mesh file. Units: mm, cm, or in.
    Filepath must be within allowed directories (~/Desktop, ~/Downloads, ~/Documents)."""
    validated = validate_filepath(filepath, allowed_extensions=[".stl", ".obj", ".3mf"])
    validate_enum(unit, ["mm", "cm", "in"], "unit")
    return send_fusion_command("import_mesh", {"filepath": str(validated), "unit": unit})
