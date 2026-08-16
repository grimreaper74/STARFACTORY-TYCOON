"""Measure the v074 PR-008 discharge against any authored PR-009 receiving datum."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008NativeRuntimeCandidate_v074"
OUT = ROOT / "Saved/Audits/press_shop_pr008_pr009_interface_v074.json"
EXPECTED_PR008_DISCHARGE_END_X_CM = -17.5
EXPECTED_STRIP_CENTRE_Y_CM = -2000.0

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")


def bounds_row(actor):
    origin, extent = actor.get_actor_bounds(False, False)
    # UE 5.8 does not expose AActor::IsHidden as actor.is_hidden() in Python.
    # Read the reflected bHidden property instead so this remains a read-only audit.
    hidden_in_game = bool(actor.get_editor_property("hidden"))
    return {
        "actor": actor.get_actor_label(),
        "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        "bounds_min_cm": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
        "bounds_max_cm": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
        "hidden_in_game": hidden_in_game,
        "tags": [str(tag) for tag in actor.tags],
    }


actors = list(actors_api.get_all_level_actors())
discharge = [bounds_row(actor) for actor in actors
             if actor.get_actor_label().startswith("LB_PR008_V070_SM_CA_MW_PR008_Discharge")]
pr009 = [bounds_row(actor) for actor in actors if "PR009" in actor.get_actor_label().upper()
         and "CAM" not in actor.get_actor_label().upper()]

discharge_end_x = max((row["bounds_max_cm"][0] for row in discharge), default=None)
receiving_start_x = min((row["bounds_min_cm"][0] for row in pr009), default=None)
gap_cm = receiving_start_x - discharge_end_x if discharge_end_x is not None and receiving_start_x is not None else None
centreline_errors = [abs(row["location_cm"][1] - EXPECTED_STRIP_CENTRE_Y_CM) for row in discharge]
primary_process_tokens = (
    "DischargeFrame", "DischargeRoll", "DischargeBearings", "DischargeGuides",
    "DischargeSensors", "DischargeBlank", "DischargeOpenMesh", "DischargeLightCurtain",
)
primary_process_rows = [
    row for row in discharge if any(token in row["actor"] for token in primary_process_tokens)
]
primary_centreline_errors = [
    abs(row["location_cm"][1] - EXPECTED_STRIP_CENTRE_Y_CM) for row in primary_process_rows
]

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-pr009-interface-v074/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "flow_axis": "world +X (authoritative PR-008 local +Y at -90 degree yaw)",
    "expected_pr008_discharge_end_x_cm": EXPECTED_PR008_DISCHARGE_END_X_CM,
    "expected_strip_centre_y_cm": EXPECTED_STRIP_CENTRE_Y_CM,
    "measured_discharge_end_x_cm": discharge_end_x,
    "discharge_end_error_cm": abs(discharge_end_x - EXPECTED_PR008_DISCHARGE_END_X_CM)
        if discharge_end_x is not None else None,
    "maximum_primary_process_centreline_error_cm": max(primary_centreline_errors)
        if primary_centreline_errors else None,
    "maximum_all_discharge_actor_centreline_offset_cm": max(centreline_errors)
        if centreline_errors else None,
    "centreline_note": "Primary process metric excludes deliberately side-mounted drive, services, identity and E-stop hardware.",
    "pr009_receiving_start_x_cm": receiving_start_x,
    "measured_physical_gap_cm": gap_cm,
    "discharge_actor_count": len(discharge),
    "pr009_actor_count": len(pr009),
    "discharge_actors": discharge,
    "pr009_actors": pr009,
    "status": "INTERFACE_DATUM_MEASURED__PR009_RECEIVER_PRESENT" if pr009 else
              "PR008_DISCHARGE_DATUM_MEASURED__PR009_RECEIVER_NOT_YET_AUTHORED__NOT_PROMOTED",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR008_PR009_V074_INTERFACE_AUDIT discharge={len(discharge)} pr009={len(pr009)} gap={gap_cm}")
unreal.SystemLibrary.quit_editor()
