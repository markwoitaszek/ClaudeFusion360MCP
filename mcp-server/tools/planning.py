"""Offline design brief and batch estimation tools.

These tools do NOT require a live Fusion 360 connection. They help
Claude structure design intent before executing CAD operations.

Architecture note: This is the first tool module that does not use IPC.
Offline tools bypass the IPC validation boundary, so they MUST import
and use validators from validation.py directly (MUST constraint #5).

All dimensions follow the centimeter convention (ADR-D003).
"""

from mcp.server.fastmcp import FastMCP
from validation import validate_enum

router = FastMCP("planning")

# Valid manufacturing processes for design brief generation
_MANUFACTURING_PROCESSES = [
    "fdm_3d_print",
    "sla_3d_print",
    "cnc_milling",
    "injection_molding",
    "sheet_metal",
    "casting",
    "general",
]

# Valid operation types for batch estimation
_BATCH_OPERATIONS = [
    "sketch",
    "extrude",
    "revolve",
    "sweep",
    "fillet",
    "chamfer",
    "shell",
    "pattern_rectangular",
    "pattern_circular",
    "mirror",
    "move_component",
    "rotate_component",
    "boolean",
]


@router.tool()
def plan_design(description: str, manufacturing_process: str = "general") -> dict:
    """Generate a structured design brief for a part or assembly. offline_safe

    Use this BEFORE starting CAD operations to plan the design approach.
    Works without a live Fusion 360 connection.

    Args:
        description: Natural language description of the desired part/assembly.
            Must be non-empty (max 2000 characters).
        manufacturing_process: Target manufacturing method. One of:
            fdm_3d_print, sla_3d_print, cnc_milling, injection_molding,
            sheet_metal, casting, general (default: general).

    Returns:
        Structured design brief with recommended approach, operations,
        and manufacturing constraints. All dimensions in centimeters.
    """
    if not description or not description.strip():
        raise ValueError("description cannot be empty")
    if len(description) > 2000:
        raise ValueError("description exceeds maximum length of 2000 characters")
    validate_enum(manufacturing_process, _MANUFACTURING_PROCESSES, "manufacturing_process")

    # Manufacturing-specific constraints
    process_constraints = {
        "fdm_3d_print": {
            "min_wall_thickness_cm": 0.08,
            "min_feature_size_cm": 0.04,
            "max_overhang_angle_deg": 45,
            "supports_required": True,
            "notes": "Design with flat base for bed adhesion. Avoid overhangs >45°.",
        },
        "sla_3d_print": {
            "min_wall_thickness_cm": 0.05,
            "min_feature_size_cm": 0.025,
            "max_overhang_angle_deg": 30,
            "supports_required": True,
            "notes": "Higher resolution than FDM. Requires post-curing.",
        },
        "cnc_milling": {
            "min_wall_thickness_cm": 0.1,
            "min_feature_size_cm": 0.05,
            "max_overhang_angle_deg": None,
            "supports_required": False,
            "notes": "Consider tool access. Internal corners need fillet radius >= tool radius.",
        },
        "injection_molding": {
            "min_wall_thickness_cm": 0.1,
            "min_feature_size_cm": 0.05,
            "max_overhang_angle_deg": None,
            "supports_required": False,
            "notes": "Uniform wall thickness. Add draft angles (1-3°). Design for mold release.",
        },
        "sheet_metal": {
            "min_wall_thickness_cm": 0.05,
            "min_feature_size_cm": 0.1,
            "max_overhang_angle_deg": None,
            "supports_required": False,
            "notes": "Design with bend radii >= material thickness. K-factor considerations.",
        },
        "casting": {
            "min_wall_thickness_cm": 0.3,
            "min_feature_size_cm": 0.2,
            "max_overhang_angle_deg": None,
            "supports_required": False,
            "notes": "Avoid sharp internal corners. Add draft angles for mold extraction.",
        },
        "general": {
            "min_wall_thickness_cm": None,
            "min_feature_size_cm": None,
            "max_overhang_angle_deg": None,
            "supports_required": False,
            "notes": "No manufacturing-specific constraints applied.",
        },
    }

    return {
        "success": True,
        "design_brief": {
            "description": description.strip(),
            "manufacturing_process": manufacturing_process,
            "unit": "cm",
            "constraints": process_constraints.get(manufacturing_process, process_constraints["general"]),
            "recommended_workflow": [
                "1. Create base sketch on appropriate plane",
                "2. Extrude or revolve to create primary body",
                "3. Add secondary features (fillets, chamfers, holes)",
                "4. Apply manufacturing-specific features (draft, shell)",
                "5. Verify dimensions with measure() tool",
                "6. Export in appropriate format",
            ],
        },
    }


@router.tool()
def estimate_batch_sequence(operations: str) -> dict:
    """Validate and estimate a batch of Fusion 360 operations. offline_safe

    Use this to pre-validate a sequence of operations before executing them.
    Works without a live Fusion 360 connection.

    Args:
        operations: Comma-separated list of operation names in execution order.
            Valid operations: sketch, extrude, revolve, sweep, fillet, chamfer,
            shell, pattern_rectangular, pattern_circular, mirror,
            move_component, rotate_component, boolean.

    Returns:
        Validation result with operation sequence, dependency warnings,
        and estimated complexity.
    """
    if not operations or not operations.strip():
        raise ValueError("operations cannot be empty")

    op_list = [op.strip().lower() for op in operations.split(",") if op.strip()]
    if not op_list:
        raise ValueError("operations must contain at least one valid operation")
    if len(op_list) > 50:
        raise ValueError("operations list exceeds maximum of 50 operations")

    # Validate each operation
    invalid = [op for op in op_list if op not in _BATCH_OPERATIONS]
    if invalid:
        raise ValueError(
            f"Invalid operations: {', '.join(invalid)}. " f"Valid operations: {', '.join(_BATCH_OPERATIONS)}"
        )

    # Dependency analysis
    warnings = []
    has_sketch = False
    has_body = False

    for i, op in enumerate(op_list):
        if op == "sketch":
            has_sketch = True
        elif op in ("extrude", "revolve", "sweep"):
            if not has_sketch:
                warnings.append(f"Step {i + 1} ({op}): requires a sketch — add 'sketch' before this operation.")
            has_body = True
        elif op in ("fillet", "chamfer", "shell", "pattern_rectangular", "pattern_circular", "mirror", "boolean"):
            if not has_body:
                warnings.append(f"Step {i + 1} ({op}): requires a body — add an extrude/revolve/sweep first.")
        elif op in ("move_component", "rotate_component"):
            if not has_body:
                warnings.append(f"Step {i + 1} ({op}): requires a component body to position.")

    return {
        "success": True,
        "batch_estimate": {
            "operations": op_list,
            "operation_count": len(op_list),
            "warnings": warnings,
            "is_valid": len(warnings) == 0,
            "estimated_complexity": ("low" if len(op_list) <= 5 else "medium" if len(op_list) <= 15 else "high"),
        },
    }
