"""Repair the rejected first v030 label, fill-light and span-camera pass."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v030"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_crane_visual_repair_v030.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

all_actors = list(actors.get_all_level_actors())

# Pull the first-pass label 16 cm back from the rim while retaining the
# improved 1.90 m face offset and clear hook bore.
label_inboard_shift = unreal.Vector(-16.0, 0.0, 0.0)
shifted = []
for actor in all_actors:
    label = actor.get_actor_label()
    if label.startswith("LB_COIL_LABEL_V026_") or label.startswith("LB_COIL_TEXT_V026_"):
        actor.set_actor_location(actor.get_actor_location() + label_inboard_shift, False, False)
        shifted.append(label)

station = next((actor for actor in all_actors
                if actor.get_actor_label() == "LB_INT_PR004_V024_InteractiveUnpackageStation"), None)
if station is None:
    raise RuntimeError("Missing PR-004 native station")
static_components = {component.get_name(): component
                     for component in station.get_components_by_class(unreal.StaticMeshComponent)}
text_components = {component.get_name(): component
                   for component in station.get_components_by_class(unreal.TextRenderComponent)}
for name in ("PR004_WrappedCoilLabelVisual",):
    component = static_components.get(name)
    if component is None:
        raise RuntimeError(f"Missing {name}")
    location = component.get_world_location()
    component.set_world_location(location + label_inboard_shift, False, False)
for name in ("PR004_WrappedCoilLabelHeading", "PR004_WrappedCoilLabelDetail"):
    component = text_components.get(name)
    if component is None:
        raise RuntimeError(f"Missing {name}")
    location = component.get_world_location()
    component.set_world_location(location + label_inboard_shift, False, False)

# The lower-face clipping persists without needing the candidate fill. Disable
# it for the fresh gate and retain the authored production lighting only.
service_fill = next((actor for actor in all_actors
                     if actor.get_actor_label() == "LB_PR004_V028_CraneServiceFill"), None)
if service_fill is None:
    raise RuntimeError("Missing inherited crane service fill")
service_fill.point_light_component.set_editor_property("intensity", 0.0)

# The rejected camera was just outside the west shell. Move it 10 m inside the
# west bay, below the 19 m roof liner, while keeping enough distance for the
# complete 62.1 m bridge in a non-fisheye frame.
camera = next((actor for actor in all_actors
               if actor.get_actor_label() == "LB_PR004_V030_CAM_CraneFullSpanWest"), None)
if camera is None:
    raise RuntimeError("Missing v030 west span camera")
camera.set_actor_location(unreal.Vector(-10150.0, -2415.0, 1120.0), False, False)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    camera.get_actor_location(), unreal.Vector(-5050.0, -2415.0, 1480.0)), False)
camera.camera_component.set_editor_property("field_of_view", 72.0)

if not levels.save_current_level():
    raise RuntimeError(f"Could not save repaired {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-crane-visual-repair-v030/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FIRST_SPAN_FRAME_REJECTED__INBOARD_LABEL_AND_INTERIOR_CAMERA_REPAIRED__REGATE_REQUIRED",
    "map": MAP,
    "rejected_first_span_reason": "camera outside west shell produced blank frame",
    "shifted_external_label_actor_count": len(shifted),
    "label_inboard_shift_cm": -16.0,
    "candidate_service_fill_intensity": 0.0,
    "camera_location_cm": [-10150.0, -2415.0, 1120.0],
    "runtime_gate_after_repair": "OPEN",
    "visual_gate": "OPEN",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_CRANE_VISUAL_V030_REPAIR_PASS labels={len(shifted)}")
unreal.SystemLibrary.quit_editor()
