"""Tests for the offline planning tools (mcp-server/tools/planning.py)."""

import pytest
from tools import planning


class TestPlanDesign:
    def test_basic_design_brief(self):
        result = planning.plan_design("Create a 5cm cube", "general")
        assert result["success"] is True
        brief = result["design_brief"]
        assert brief["description"] == "Create a 5cm cube"
        assert brief["manufacturing_process"] == "general"
        assert brief["unit"] == "cm"
        assert "recommended_workflow" in brief
        assert len(brief["recommended_workflow"]) > 0

    def test_fdm_constraints(self):
        result = planning.plan_design("Print a bracket", "fdm_3d_print")
        constraints = result["design_brief"]["constraints"]
        assert constraints["min_wall_thickness_cm"] == 0.08
        assert constraints["supports_required"] is True
        assert constraints["max_overhang_angle_deg"] == 45

    def test_cnc_constraints(self):
        result = planning.plan_design("Mill a housing", "cnc_milling")
        constraints = result["design_brief"]["constraints"]
        assert constraints["min_wall_thickness_cm"] == 0.1
        assert constraints["supports_required"] is False

    def test_general_has_no_specific_constraints(self):
        result = planning.plan_design("Generic part")
        constraints = result["design_brief"]["constraints"]
        assert constraints["min_wall_thickness_cm"] is None
        assert constraints["supports_required"] is False

    def test_empty_description_rejected(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            planning.plan_design("")

    def test_whitespace_only_description_rejected(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            planning.plan_design("   ")

    def test_too_long_description_rejected(self):
        with pytest.raises(ValueError, match="exceeds maximum length"):
            planning.plan_design("x" * 2001)

    def test_invalid_process_rejected(self):
        with pytest.raises(ValueError, match="Invalid manufacturing_process"):
            planning.plan_design("part", "laser_cutting")

    def test_case_insensitive_process(self):
        result = planning.plan_design("test part", "FDM_3D_PRINT")
        assert result["success"] is True
        assert result["design_brief"]["manufacturing_process"] == "fdm_3d_print"

    def test_all_valid_processes(self):
        for process in planning._MANUFACTURING_PROCESSES:
            result = planning.plan_design("test part", process)
            assert result["success"] is True


class TestEstimateBatchSequence:
    def test_simple_sequence(self):
        result = planning.estimate_batch_sequence(["sketch", "extrude", "fillet"])
        assert result["success"] is True
        batch = result["batch_estimate"]
        assert batch["operations"] == ["sketch", "extrude", "fillet"]
        assert batch["operation_count"] == 3
        assert batch["is_valid"] is True
        assert batch["warnings"] == []

    def test_missing_sketch_warning(self):
        result = planning.estimate_batch_sequence(["extrude", "fillet"])
        batch = result["batch_estimate"]
        assert batch["is_valid"] is False
        assert any("requires a sketch" in w for w in batch["warnings"])

    def test_missing_body_warning(self):
        result = planning.estimate_batch_sequence(["sketch", "fillet"])
        batch = result["batch_estimate"]
        assert batch["is_valid"] is False
        assert any("requires a body" in w for w in batch["warnings"])

    def test_valid_full_workflow(self):
        result = planning.estimate_batch_sequence(["sketch", "extrude", "fillet", "chamfer", "shell"])
        assert result["batch_estimate"]["is_valid"] is True
        assert result["batch_estimate"]["estimated_complexity"] == "low"

    def test_medium_complexity(self):
        ops = ["sketch", "extrude"] + ["fillet"] * 8
        result = planning.estimate_batch_sequence(ops)
        assert result["batch_estimate"]["estimated_complexity"] == "medium"

    def test_high_complexity(self):
        ops = ["sketch", "extrude"] + ["fillet"] * 20
        result = planning.estimate_batch_sequence(ops)
        assert result["batch_estimate"]["estimated_complexity"] == "high"

    def test_empty_operations_rejected(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            planning.estimate_batch_sequence([])

    def test_invalid_operation_rejected(self):
        with pytest.raises(ValueError, match="Invalid operations"):
            planning.estimate_batch_sequence(["sketch", "teleport"])

    def test_too_many_operations_rejected(self):
        ops = ["sketch"] * 51
        with pytest.raises(ValueError, match="exceeds maximum"):
            planning.estimate_batch_sequence(ops)

    def test_whitespace_handling(self):
        result = planning.estimate_batch_sequence([" sketch ", " extrude ", " fillet "])
        assert result["batch_estimate"]["operations"] == ["sketch", "extrude", "fillet"]

    def test_case_insensitive(self):
        result = planning.estimate_batch_sequence(["SKETCH", "Extrude", "fillet"])
        assert result["batch_estimate"]["operations"] == ["sketch", "extrude", "fillet"]

    def test_sweep_rejected(self):
        with pytest.raises(ValueError, match="Invalid operations.*sweep"):
            planning.estimate_batch_sequence(["sketch", "sweep"])
