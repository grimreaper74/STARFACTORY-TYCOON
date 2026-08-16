"""Validate PR-004 v009 reach, cutter contact and cell clearances.

This is a technical candidate gate only.  It deliberately cannot promote the
cell; fresh visual and runtime reviews remain mandatory.
"""

import json
import math
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v009"
OUT = PROJECT / "Saved/Audits/pr004_v009_reach_clearance_validation.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def location(actor):
    value = actor.get_actor_location()
    return (value.x, value.y, value.z)


def bounds(actor):
    origin, extent = actor.get_actor_bounds(False)
    return (
        (origin.x - extent.x, origin.y - extent.y, origin.z - extent.z),
        (origin.x + extent.x, origin.y + extent.y, origin.z + extent.z),
    )


try:
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")
    by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}

    required = {
        "base": "LB_PR004_robot_v002_base",
        "cutter": "LB_PR004_robot_v002_band_cutter",
        "coil": "LB_PR004_packaging_v004_PR004-PACK-BARE-COIL-v004",
        "rack": "LB_PR004_robot_v002_tool_rack",
    }
    missing = [label for label in required.values() if label not in by_label]
    if missing:
        raise RuntimeError(f"Missing validation actors: {missing}")

    base = location(by_label[required["base"]])
    cutter = location(by_label[required["cutter"]])
    coil = location(by_label[required["coil"]])
    rack_min, rack_max = bounds(by_label[required["rack"]])

    coil_radius_cm = 95.0
    coil_half_width_cm = 75.0
    declared_tool_tip_reach_cm = 345.0
    centre_distance_xy = math.hypot(coil[0] - base[0], coil[1] - base[1])
    nearest_coil_surface_xy = centre_distance_xy - coil_radius_cm
    cutter_radial_xz = math.hypot(cutter[0] - coil[0], cutter[2] - coil[2])
    cutter_surface_error = abs(cutter_radial_xz - coil_radius_cm)
    cutter_axial_offset = abs(cutter[1] - coil[1])

    working_labels = [
        label for label in by_label
        if label.startswith("LB_PR004_robot_v002_")
        and "tool_rack" not in label
        and not any(token in label for token in ("wrap_", "edge_", "inspection_"))
    ]
    working_bounds = [bounds(by_label[label]) for label in working_labels]
    work_min_y = min(item[0][1] for item in working_bounds)
    work_max_y = max(item[1][1] for item in working_bounds)
    rack_clearance_cm = rack_min[1] - work_max_y

    # v009's authoritative fitted envelope is 11.5 x 12.0 m.  A small inset
    # prevents accepting geometry that merely touches the fence plane.
    cell_half_x = 575.0
    cell_half_y = 600.0
    inset = 5.0
    core_labels = working_labels + [required["coil"], required["rack"]]
    containment = {}
    for label in core_labels:
        lower, upper = bounds(by_label[label])
        containment[label] = (
            lower[0] >= -cell_half_x + inset
            and upper[0] <= cell_half_x - inset
            and lower[1] >= -cell_half_y + inset
            and upper[1] <= cell_half_y - inset
            and lower[2] >= -1.0
        )

    scales = {}
    for label in core_labels:
        scale = by_label[label].get_actor_scale3d()
        scales[label] = [round(scale.x, 6), round(scale.y, 6), round(scale.z, 6)]

    checks = {
        "coil_near_surface_within_declared_tool_reach": nearest_coil_surface_xy <= declared_tool_tip_reach_cm,
        "cutter_is_on_coil_outer_surface_band": cutter_surface_error <= 15.0,
        "cutter_is_within_coil_width": cutter_axial_offset <= coil_half_width_cm,
        "rear_tool_rack_clear_of_working_pose_by_200cm": rack_clearance_cm >= 200.0,
        "core_equipment_inside_1150x1200cm_fence_envelope": all(containment.values()),
        "all_validated_actors_unscaled": all(value == [1.0, 1.0, 1.0] for value in scales.values()),
    }

    result = {
        "$schema": "line-boss/audit/pr004-v009-reach-clearance/v1",
        "map": MAP,
        "status": "TECHNICAL_PASS__VISUAL_AND_RUNTIME_REVIEW_REQUIRED" if all(checks.values()) else "TECHNICAL_FAIL",
        "measurements_cm": {
            "robot_base_to_coil_centre_xy": round(centre_distance_xy, 3),
            "robot_base_to_nearest_coil_surface_xy": round(nearest_coil_surface_xy, 3),
            "declared_longest_tool_tip_reach": declared_tool_tip_reach_cm,
            "cutter_radial_distance_from_coil_axis_xz": round(cutter_radial_xz, 3),
            "cutter_surface_error": round(cutter_surface_error, 3),
            "cutter_axial_offset": round(cutter_axial_offset, 3),
            "working_pose_to_rear_rack_clearance": round(rack_clearance_cm, 3),
        },
        "checks": checks,
        "containment": containment,
        "actor_scales": scales,
        "promotion_supported": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if not all(checks.values()):
        raise RuntimeError(f"PR-004 v009 reach/clearance gate failed: {checks}")
    unreal.log(f"LINE_BOSS_PR004_V009_REACH_CLEARANCE_PASS audit={OUT}")
finally:
    unreal.SystemLibrary.quit_editor()
