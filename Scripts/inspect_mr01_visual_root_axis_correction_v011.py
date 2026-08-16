"""Read-only proof for rotating MR01's imported visual root onto native X-forward authority."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v008"
OUT = ROOT / "Saved/Audits/SupportRobots/mr01_visual_root_axis_correction_v011.json"
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def vec(value):
    return [round(value.x, 4), round(value.y, 4), round(value.z, 4)]


def named(actor, name):
    for item in actor.get_components_by_class(unreal.SceneComponent):
        actual = item.get_name()
        normalized = actual
        for suffix in ("_GEN_VARIABLE", "_0"):
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
        if actual == name or normalized == name:
            return item
    raise RuntimeError("{} missing {}".format(actor.get_actor_label(), name))


def primitive_rows(actor):
    rows = []
    for item in actor.get_components_by_class(unreal.PrimitiveComponent):
        origin, extent, _radius = unreal.SystemLibrary.get_component_bounds(item)
        rows.append(
            {
                "name": item.get_name(),
                "class": item.get_class().get_name(),
                "visible": bool(item.is_visible()),
                "hidden_in_game": bool(item.get_editor_property("hidden_in_game")),
                "origin": origin,
                "extent": extent,
            }
        )
    return rows


def union_x(rows):
    selected = [row for row in rows if row["visible"] and not row["hidden_in_game"]]
    minimum = min(row["origin"].x - row["extent"].x for row in selected)
    maximum = max(row["origin"].x + row["extent"].x for row in selected)
    return round(minimum, 4), round(maximum, 4), round(maximum - minimum, 4)


def component_summary(rows, names):
    by_name = {row["name"]: row for row in rows}
    result = {}
    for name in names:
        row = by_name[name]
        result[name] = {
            "bounds_origin_cm": vec(row["origin"]),
            "bounds_size_cm": vec(row["extent"] * 2.0),
        }
    return result


world = unreal.EditorLevelLibrary.get_editor_world()
current = world.get_outermost().get_name() if world is not None else ""
if current != MAP:
    raise RuntimeError("One-map rule violation: opened {}, expected {}".format(current, MAP))
mr = {actor.get_actor_label(): actor for actor in ACTORS.get_all_level_actors()}.get(
    "LB_DOCK_FIT_MR01_v021_ActualAuthority"
)
if mr is None:
    raise RuntimeError("Docked MR01 authority missing")
visual_root = named(mr, "RobotVisualRoot")
before_rotation = visual_root.get_editor_property("relative_rotation")
before = primitive_rows(mr)

# Child yaw -90 maps the imported visual local-Y length axis onto native local X.
visual_root.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, -90.0))
after_rotation = visual_root.get_editor_property("relative_rotation")
after = primitive_rows(mr)

key_names = [
    "Visual_SM_LB_MR01_BumperFront",
    "Visual_SM_LB_MR01_BumperRear",
    "Visual_SM_LB_MR01_BumperSide_L",
    "Visual_SM_LB_MR01_BumperSide_R",
    "RP01_CollisionRoot",
]
before_union = union_x(before)
after_union = union_x(after)
after_no_arm = union_x([row for row in after if row["name"] != "Visual_MR01_ArmPoseable"])
payload = {
    "$schema": "cairnwell/audit/mr01-visual-root-axis-correction-v011/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__TRANSIENT_VISUAL_ROOT_AXIS_CORRECTION_MEASURED__FRESH_SUCCESSOR_REQUIRED__NOT_PROMOTED",
    "source_map_loaded_not_saved": MAP,
    "actor": mr.get_actor_label(),
    "actor_rotation_roll_pitch_yaw_deg": [
        mr.get_actor_rotation().roll,
        mr.get_actor_rotation().pitch,
        mr.get_actor_rotation().yaw,
    ],
    "visual_root_rotation_before_roll_pitch_yaw_deg": [
        before_rotation.roll, before_rotation.pitch, before_rotation.yaw
    ],
    "visual_root_rotation_after_roll_pitch_yaw_deg": [
        after_rotation.roll, after_rotation.pitch, after_rotation.yaw
    ],
    "visible_union_world_x_before_cm": list(before_union),
    "visible_union_world_x_after_cm": list(after_union),
    "visible_union_without_arm_world_x_after_cm": list(after_no_arm),
    "portal_width_cm": 126.0,
    "body_without_arm_lateral_clearance_after_cm": round(126.0 - after_no_arm[2], 4),
    "components_before": component_summary(before, key_names),
    "components_after": component_summary(after, key_names),
    "map_saved": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_MR01_VISUAL_ROOT_AXIS_V011 {}".format(payload["status"]))
