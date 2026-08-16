"""Add an operational in-hall carry camera without changing PR-004 authority."""
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import unreal

VERSION = os.environ.get("LB_PR004_CARRY_CONTEXT_VERSION", "v114").lower()
if VERSION not in ("v114", "v115", "v116"):
    raise RuntimeError(f"Unsupported carry-context version {VERSION}")
MAP = f"/Game/LineBoss/Maps/LB_PressShop_PR004CarryContextCandidate_{VERSION}"
OUT = Path(unreal.Paths.project_saved_dir()) / f"Audits/press_shop_pr004_carry_context_candidate_{VERSION}.json"
LABEL = f"LB_PR004_{VERSION.upper()}_CAM_TraceCarryInstalledContext"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label() == LABEL:
        actors.destroy_actor(actor)

if VERSION == "v116":
    # High, longer-lens oblique view of the live carried-coil centre.  The
    # distance keeps storage coils out of the foreground and the lateral
    # offset exposes the C-hook/load relationship.
    location = unreal.Vector(-2950.0, -650.0, 1260.0)
    target = unreal.Vector(-5050.0, -2000.0, 755.0)
    fov = 38.0
    exposure_bias = -0.45
elif VERSION == "v115":
    location = unreal.Vector(-3900.0, -1850.0, 950.0)
    target = unreal.Vector(-5050.0, -2000.0, 761.0)
    fov = 46.0
    exposure_bias = -0.45
else:
    location = unreal.Vector(-3850.0, -650.0, 800.0)
    target = unreal.Vector(-5050.0, -1950.0, 430.0)
    fov = 35.0
    exposure_bias = -0.72
camera = actors.spawn_actor_from_class(unreal.CameraActor, location, unreal.Rotator())
camera.set_actor_label(LABEL)
camera.tags = [unreal.Name(x) for x in (
    "LB.Camera.Validation", f"LB.Camera.Fixed.Traceability.{VERSION}",
    f"LB.Asset.Candidate.{VERSION}", "LB.Asset.CandidateNotPromoted")]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
camera.camera_component.set_editor_properties({
    "field_of_view": fov, "aspect_ratio": 16.0 / 9.0,
    "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0})
settings = camera.camera_component.get_editor_property("post_process_settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0,
    "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": exposure_bias})
camera.camera_component.set_editor_property("post_process_settings", settings)
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": f"cairnwell/audit/press-shop-pr004-carry-context-candidate-{VERSION}/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "INSTALLED_CONTEXT_CARRY_CAMERA_AUTHORED__EARLY_FRESH_VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_v113",
    "map": MAP, "camera": LABEL,
    "location_cm": [location.x, location.y, location.z],
    "target_cm": [target.x, target.y, target.z],
    "field_of_view": fov, "exposure_bias": exposure_bias,
    "geometry_changed": False, "materials_changed": False,
    "lighting_changed": False, "authority_changed": False,
    "production_map_changed": False, "promotion_authorized": False
}, indent=2), encoding="utf-8")
unreal.log(f"CAIRNWELL_PR004_CARRY_CONTEXT_{VERSION.upper()}_BUILD_PASS")
unreal.SystemLibrary.quit_editor()
