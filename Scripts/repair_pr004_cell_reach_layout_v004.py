"""Correct the PR-004 v004 candidate layout against the locked cell drawing.

This is deliberately candidate-only.  It fixes the inherited assembly error
that put the long guarded tool rack across the robot-to-coil route and placed
the film dewrapper on the wrong side of the robot.  Promotion still requires
swept-collision, animation and fixed-camera visual gates.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v004"
AUDIT = ROOT / "Saved/Audits/pr004_cell_reach_layout_repair_v004.json"

ROBOT_BASE = "LB_PR004_robot_v002_base"
ROBOT_J1 = "LB_PR004_robot_v002_j1"
FILM_ROOT = "LB_PR004_film_dewrap_v004_static"
FILM_GUARDS = "LB_PR004_film_dewrap_v004_guards"

# Locked process datums in the isolated candidate map (centimetres).
COIL_CENTER = (-280.0, 120.0, 130.5)
ROBOT_BASE_TARGET = (-40.0, 70.0, 0.0)
ROBOT_J1_PIVOT_Z = 72.0
FILM_ROOT_TARGET = (330.0, -250.0, 0.0)
FILM_TAB_RELATIVE = (-96.0, 222.0, 131.0)

# The drawing puts the four-dock rack behind the robot, not between the robot
# and coil.  Rotating the existing modular rack back to its authored X-axis
# arrangement keeps all four docks visible and reachable without changing the
# fixed cell envelope.
RACK_ROOT_TARGETS = {
    "LB_PR004_robot_v002_tool_rack": ((-70.0, -220.0, 0.0), 0.0),
    "LB_PR004_robot_v002_band_tool": ((-205.0, -187.0, 108.0), 0.0),
    "LB_PR004_robot_v002_wrap_tool": ((-115.0, -187.0, 108.0), 0.0),
    "LB_PR004_robot_v002_edge_tool": ((-25.0, -187.0, 108.0), 0.0),
    "LB_PR004_robot_v002_inspection_tool": ((65.0, -187.0, 108.0), 0.0),
}

WORKING_RADIUS_CM = 350.0
LONGEST_TOOL_TIP_REACH_CM = 345.0
SAFE_HOME_WORLD_YAW = 90.0


def distance_2d(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def distance_3d(a, b):
    return math.sqrt(sum((b[index] - a[index]) ** 2 for index in range(3)))


def boxes_overlap_2d(a, b):
    return not (
        a[1] <= b[0] or b[1] <= a[0]
        or a[3] <= b[2] or b[3] <= a[2]
    )


def segment_intersects_box_2d(start, end, box):
    """Liang-Barsky segment/AABB test used for the blocking-route audit."""
    x0, y0 = start
    x1, y1 = end
    xmin, xmax, ymin, ymax = box
    dx = x1 - x0
    dy = y1 - y0
    p = (-dx, dx, -dy, dy)
    q = (x0 - xmin, xmax - x0, y0 - ymin, ymax - y0)
    lower = 0.0
    upper = 1.0
    for pi, qi in zip(p, q):
        if abs(pi) < 1.0e-9:
            if qi < 0.0:
                return False
            continue
        ratio = qi / pi
        if pi < 0.0:
            lower = max(lower, ratio)
        else:
            upper = min(upper, ratio)
        if lower > upper:
            return False
    return True


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

actors = {actor.get_actor_label(): actor for actor in actor_subsystem.get_all_level_actors()}
required = [ROBOT_BASE, ROBOT_J1, FILM_ROOT, FILM_GUARDS, *RACK_ROOT_TARGETS]
missing = [label for label in required if label not in actors]
if missing:
    raise RuntimeError(f"Missing required candidate actors: {missing}")

packaging_count = sum(label.startswith("LB_PR004_packaging_v004_") for label in actors)
robot_count = sum(label.startswith("LB_PR004_robot_v002_") for label in actors)
film_count = sum(label.startswith("LB_PR004_film_dewrap_v004_") for label in actors)
if packaging_count != 43 or robot_count != 28 or film_count != 11:
    raise RuntimeError(
        "Candidate composition mismatch: "
        f"packaging={packaging_count}/43 robot={robot_count}/28 film={film_count}/11"
    )


def actor_state(actor):
    return {
        "location_cm": list(actor.get_actor_location().to_tuple()),
        "rotation_deg": list(actor.get_actor_rotation().to_tuple()),
    }


before = {label: actor_state(actors[label]) for label in required}

# Moving the attached roots preserves every articulated child transform.
robot_base = actors[ROBOT_BASE]
robot_base.set_actor_location(unreal.Vector(*ROBOT_BASE_TARGET), False, False)

film_root = actors[FILM_ROOT]
film_root.set_actor_location(unreal.Vector(*FILM_ROOT_TARGET), False, False)

# The v003 assembler omitted this otherwise-static sibling from its attachment
# contract, which left an empty fence behind when the dewrapper moved.  Keep it
# registered as local nip/compactor guarding; it is not the cell perimeter.
film_guards = actors[FILM_GUARDS]
film_guards.set_actor_location(unreal.Vector(*FILM_ROOT_TARGET), False, False)
film_guards.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=-90.0), False)
film_guards.attach_to_actor(
    film_root,
    unreal.Name(""),
    unreal.AttachmentRule.KEEP_WORLD,
    unreal.AttachmentRule.KEEP_WORLD,
    unreal.AttachmentRule.KEEP_WORLD,
    False,
)

for label, (location, yaw) in RACK_ROOT_TARGETS.items():
    actor = actors[label]
    actor.set_actor_location(unreal.Vector(*location), False, False)
    actor.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw), False)

# Keep the unanimated validation pose in a clear home sector.  A prior visual
# aid aimed the straight rest chain directly at the coil and caused an obvious
# mesh intersection.  Reach is proved below from the authored pivot/targets;
# operational joint poses remain behind the swept-collision gate.
rest_world_yaw = -90.0
j1_delta = ((SAFE_HOME_WORLD_YAW - rest_world_yaw + 180.0) % 360.0) - 180.0
if not -185.0 <= j1_delta <= 185.0:
    raise RuntimeError(f"J1 target {j1_delta:.3f} deg exceeds documented limits")
j1 = actors[ROBOT_J1]
j1_rotation = j1.get_actor_rotation()
j1.set_actor_rotation(
    unreal.Rotator(
        roll=j1_rotation.roll,
        pitch=j1_rotation.pitch,
        yaw=SAFE_HOME_WORLD_YAW,
    ),
    False,
)

# Retarget only the fixed validation cameras affected by the corrected layout.
camera_targets = {
    "LB_PR004_CAM_Overview_SW": (-20.0, -45.0, 120.0),
    "LB_PR004_CAM_Overview_NE": (-20.0, -45.0, 120.0),
    "LB_PR004_CAM_RobotTools": (-40.0, -65.0, 135.0),
    "LB_PR004_CAM_FilmDewrap": (330.0, -250.0, 125.0),
}
for label, target in camera_targets.items():
    camera = actors.get(label)
    if camera is None:
        raise RuntimeError(f"Missing fixed validation camera {label}")
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)),
        False,
    )

after = {label: actor_state(actors[label]) for label in required}

# Independent numeric reach checks use the actual authored pivot and target
# heights, rather than judging reach from the camera image.
robot_pivot = (ROBOT_BASE_TARGET[0], ROBOT_BASE_TARGET[1], ROBOT_J1_PIVOT_Z)
film_tab = (
    FILM_ROOT_TARGET[0] + FILM_TAB_RELATIVE[0],
    FILM_ROOT_TARGET[1] + FILM_TAB_RELATIVE[1],
    FILM_TAB_RELATIVE[2],
)
tool_targets = {
    label: location for label, (location, _yaw) in RACK_ROOT_TARGETS.items()
    if not label.endswith("tool_rack")
}
reach_targets = {
    "packaged_coil_centre": COIL_CENTER,
    "film_start_tab_handoff": film_tab,
    **{label.rsplit("_", 2)[-2] + "_tool_dock": location for label, location in tool_targets.items()},
}
reach_results = {}
for name, target in reach_targets.items():
    horizontal = distance_2d(robot_pivot, target)
    spatial = distance_3d(robot_pivot, target)
    reach_results[name] = {
        "target_cm": list(target),
        "horizontal_distance_cm": round(horizontal, 3),
        "pivot_to_target_distance_cm": round(spatial, 3),
        "within_345_cm_longest_tool_tip_reach": spatial <= LONGEST_TOOL_TIP_REACH_CM,
        "within_350_cm_working_radius": spatial <= WORKING_RADIUS_CM,
    }
if not all(item["within_345_cm_longest_tool_tip_reach"] for item in reach_results.values()):
    raise RuntimeError(f"Corrected layout still fails reach: {reach_results}")

# Conservative XY footprints from the authored source manifests after the
# validated rotations.  Touching counts as clear; overlap is forbidden.
footprints = {
    "cradle": (-410.0, -150.0, -52.0, 292.0),
    "robot_base": (-104.0, 24.0, 6.0, 134.0),
    "tool_rack": (-278.0, 138.0, -269.0, -171.0),
    "film_dewrapper": (184.0, 476.0, -529.249, 29.249),
}
overlaps = []
names = list(footprints)
for index, first in enumerate(names):
    for second in names[index + 1:]:
        if boxes_overlap_2d(footprints[first], footprints[second]):
            overlaps.append([first, second])
if overlaps:
    raise RuntimeError(f"Corrected static footprints overlap: {overlaps}")

old_robot = (150.0, -40.0)
old_rack_box = (-134.0, -36.0, -248.0, 168.0)
new_robot = ROBOT_BASE_TARGET[:2]
new_rack_box = footprints["tool_rack"]
route_audit = {
    "old_robot_to_coil_intersected_tool_rack": segment_intersects_box_2d(
        old_robot, COIL_CENTER[:2], old_rack_box
    ),
    "new_robot_to_coil_intersects_tool_rack": segment_intersects_box_2d(
        new_robot, COIL_CENTER[:2], new_rack_box
    ),
    "new_robot_to_film_tab_intersects_tool_rack": segment_intersects_box_2d(
        new_robot, film_tab[:2], new_rack_box
    ),
}
if (
    not route_audit["old_robot_to_coil_intersected_tool_rack"]
    or route_audit["new_robot_to_coil_intersects_tool_rack"]
    or route_audit["new_robot_to_film_tab_intersects_tool_rack"]
):
    raise RuntimeError(f"Tool-rack route repair did not prove clean: {route_audit}")

if not levels.save_current_level():
    raise RuntimeError("Could not save the corrected v004 candidate map")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/pr004-cell-reach-layout-repair-v004/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CANDIDATE_REACH_AND_STATIC_CLEARANCE_PASS__SWEPT_COLLISION_AND_VISUAL_GATE_REQUIRED",
    "map": MAP,
    "drawing_basis": [
        "Docs/References/PR004_Robotic_Depackaging_Cell/v002/PR004A_Realistic_Robotic_Coil_Destrapping_Dewrapping_Cell_v002.jpg",
        "Docs/References/PR004_Robotic_Depackaging_Cell/v002/PR004_Powered_Coil_Wrap_Dewinding_Compaction_Module_RevA.jpg",
    ],
    "locked_cell_envelope_cm": [1240.0, 1440.0, 450.0],
    "before_base_to_coil_centre_horizontal_cm": round(distance_2d(old_robot, COIL_CENTER), 3),
    "robot_contract": {
        "working_radius_cm": WORKING_RADIUS_CM,
        "longest_candidate_tool_tip_reach_cm": LONGEST_TOOL_TIP_REACH_CM,
        "j1_delta_from_authored_rest_deg": round(j1_delta, 3),
        "validation_pose": "CLEAR_HOME_SECTOR_NOT_A_PROCESS_POSE",
    },
    "composition": {
        "packaging_v004_actors": packaging_count,
        "robot_v002_actors": robot_count,
        "film_dewrap_v004_actors": film_count,
    },
    "reach_results": reach_results,
    "static_footprints_xy_cm": {name: list(box) for name, box in footprints.items()},
    "static_overlap_pairs": overlaps,
    "working_route_audit": route_audit,
    "before": before,
    "after": after,
    "remaining_gates": [
        "articulated swept collision over the full 14-step sequence",
        "robot-to-tool docking pose validation",
        "cradle/robot/dewrapper interlock simulation",
        "fresh fixed-camera visual comparison against both Pro references",
    ],
    "promotion_supported": False,
}, indent=2), encoding="utf-8")
unreal.log(
    "LINE_BOSS_PR004_REACH_LAYOUT_V004_PASS "
    f"coil={reach_results['packaged_coil_centre']['pivot_to_target_distance_cm']}cm "
    f"film_tab={reach_results['film_start_tab_handoff']['pivot_to_target_distance_cm']}cm "
    f"audit={AUDIT}"
)
