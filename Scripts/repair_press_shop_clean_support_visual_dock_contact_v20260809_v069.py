"""Bring the four standalone visual dock faces to a believable parked-robot gap."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetRuntimeFloorFix_v20260809_v059"
MAP = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetDockContactFix_v20260809_v069"
OUT = ROOT / "Saved/Audits/PressShopIntegration/clean_support_visual_dock_contact_fix_v20260809_v069.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
DOCKS = {
    "LB_CLEAN_Dock_CR01_01", "LB_CLEAN_Dock_CR01_02",
    "LB_CLEAN_Dock_MR01_01", "LB_CLEAN_Dock_MR01_02",
}

sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()
before = sha(PROTECTED)
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if before != EXPECTED or lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("fresh/protected invariant")
if not levels.new_level_from_template(MAP, SOURCE):
    raise RuntimeError("map child failed")

actor_by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
missing = sorted(DOCKS - set(actor_by_label))
if missing:
    raise RuntimeError("missing visual docks: " + ", ".join(missing))

moved = []
for label in sorted(DOCKS):
    actor = actor_by_label[label]
    old = actor.get_actor_location()
    old_origin, old_extent = actor.get_actor_bounds(False)
    actor.set_actor_location(unreal.Vector(old.x, old.y + 100.0, old.z), False, False)
    new = actor.get_actor_location()
    new_origin, new_extent = actor.get_actor_bounds(False)
    unit_suffix = label.replace("LB_CLEAN_Dock_", "")
    robot = actor_by_label["LB_CLEAN_Robot_" + unit_suffix]
    robot_origin, robot_extent = robot.get_actor_bounds(False)
    visual_gap_y = (robot_origin.y - robot_extent.y) - (new_origin.y + new_extent.y)
    moved.append({
        "label": label,
        "before_cm": [old.x, old.y, old.z],
        "after_cm": [new.x, new.y, new.z],
        "before_face_y_cm": old_origin.y + old_extent.y,
        "after_face_y_cm": new_origin.y + new_extent.y,
        "robot_rear_y_cm": robot_origin.y - robot_extent.y,
        "resulting_visual_gap_y_cm": visual_gap_y,
    })

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
if not levels.save_current_level():
    raise RuntimeError("save failed")
after = sha(PROTECTED)
if after != before:
    raise RuntimeError("protected map changed")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetDockContactFix_v20260809_v069.umap"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS_BUILD__FOUR_VISUAL_DOCKS_MOVED_FORWARD_100CM__24CM_CR01_AND_22_5CM_MR01_VISUAL_GAPS__RUNTIME_REGRESSION_REQUIRED__NOT_PROMOTED",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "source": SOURCE,
    "map": MAP,
    "map_sha256": sha(map_file),
    "moved": moved,
    "unchanged": ["robot roots", "native service dock runtime targets", "paint bays", "fleet controller", "routes"],
    "meshy_credits_used": 0,
    "protected_v438_before": before,
    "protected_v438_after": after,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_CLEAN_SUPPORT_VISUAL_DOCK_CONTACT_V069_PASS")
