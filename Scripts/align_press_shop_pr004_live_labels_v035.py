"""Align v035 live Cairnwell identities onto the package's blank main panels."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneFinishCandidate_v035"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_live_label_alignment_v035.json"
SHIFT = unreal.Vector(-85.0, 0.0, 0.0)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

shifted = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith("LB_COIL_LABEL_V026_") or label.startswith("LB_COIL_TEXT_V026_"):
        actor.set_actor_location(actor.get_actor_location() + SHIFT, False, False)
        shifted.append(label)

station = next((actor for actor in actors.get_all_level_actors()
                if actor.get_actor_label() == "LB_INT_PR004_V024_InteractiveUnpackageStation"), None)
if station is None:
    raise RuntimeError("Missing native PR-004 station")
component_names = {
    "PR004_WrappedCoilLabelVisual",
    "PR004_WrappedCoilLabelHeading",
    "PR004_WrappedCoilLabelDetail",
}
native_shifted = []
for component in station.get_components_by_class(unreal.SceneComponent):
    if component.get_name() not in component_names:
        continue
    component.set_world_location(component.get_world_location() + SHIFT, False, False)
    native_shifted.append(component.get_name())

if len(shifted) != 42 or len(native_shifted) != 3:
    raise RuntimeError(f"Unexpected live-label inventory actors={len(shifted)} native={native_shifted}")
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-live-label-alignment-v035/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "LIVE_CAIRNWELL_IDENTITY_ALIGNED_TO_PHYSICAL_MAIN_PANEL__REGATES_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "world_shift_cm": [-85.0, 0.0, 0.0],
    "external_actor_count": len(shifted),
    "native_component_count": len(native_shifted),
    "cs10_attachment_count_unchanged": 3,
    "primary_crane_geometry_changed": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_LABEL_ALIGNMENT_V035_PASS actors={len(shifted)} native={len(native_shifted)}")
unreal.SystemLibrary.quit_editor()
