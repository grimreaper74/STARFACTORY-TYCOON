"""Create isolated v004 seated composition/light refinement from v003.

The authored 1.12 m eye datum stays fixed.  This pass changes the seated
camera setback, aim and FOV to the 120 degree Pro-reference envelope so the
console displays no longer dominate the overview wall.  It also keeps every
source/candidate asset intact and corrects the failed elevated evidence view.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_SeatedVisualCandidate_v003"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_SeatedCompositionCandidate_v004"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_seated_composition_build_v004.json"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP}")

actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
failures = []

# The source luminaires remain visible geometry.  Unreal lights are deliberately
# soft fill plus four localized task lights, avoiding the washed-out v003 wall.
for label, actor in list(actors.items()):
    if label.startswith("LB_MCR_V003_CeilingLight_"):
        actor.set_actor_label(label.replace("V003", "V004"))
        component = actor.get_component_by_class(unreal.RectLightComponent)
        if component is None:
            failures.append(f"missing RectLightComponent: {label}")
            continue
        component.set_editor_properties({
            "intensity": 38.0,
            "attenuation_radius": 500.0,
            "source_width": 145.0,
            "source_height": 24.0,
            "cast_shadows": False,
        })
        actor.tags = [unreal.Name("LB.ControlRoom.v004"), unreal.Name("LB.ControlRoom.Lighting.Ambient"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    elif label.startswith("LB_MCR_V003_TaskLight_"):
        actor.set_actor_label(label.replace("V003", "V004"))
        component = actor.get_component_by_class(unreal.RectLightComponent)
        if component is None:
            failures.append(f"missing RectLightComponent: {label}")
            continue
        component.set_editor_properties({
            "intensity": 82.0,
            "attenuation_radius": 430.0,
            "cast_shadows": True,
        })
        actor.tags = [unreal.Name("LB.ControlRoom.v004"), unreal.Name("LB.ControlRoom.Lighting.Task"), unreal.Name("LB.Asset.CandidateNotPromoted")]

exposure = actors.get("LB_MCR_V003_Exposure")
if exposure is None:
    failures.append("missing v003 exposure volume")
else:
    exposure.set_actor_label("LB_MCR_V004_Exposure")
    settings = exposure.get_editor_property("settings")
    settings.set_editor_property("auto_exposure_bias", -1.45)
    exposure.set_editor_property("settings", settings)
    exposure.tags = [unreal.Name("LB.ControlRoom.v004"), unreal.Name("LB.Asset.CandidateNotPromoted")]

# Sheet 05 specifies a fixed 112 cm eye height and 120 degree horizontal cone.
# 112 degrees is used here because UE stores vertical FOV for this 16:9 camera;
# it yields approximately the authored 120-degree horizontal coverage without
# excessive fisheye distortion.
camera_specs = {
    "SeatedPlayer": (unreal.Vector(0, 82, 112), unreal.Vector(0, -335, 190), 112.0),
    "Front": (unreal.Vector(0, 350, 185), unreal.Vector(0, -100, 155), 76.0),
    "Elevated": (unreal.Vector(610, 515, 295), unreal.Vector(0, -25, 125), 70.0),
    "SystemsWall": (unreal.Vector(0, -205, 205), unreal.Vector(0, 275, 150), 76.0),
}
for name, (location, target, fov) in camera_specs.items():
    actor = actors.get(f"LB_MCR_V003_CAM_{name}")
    if actor is None:
        failures.append(f"missing v003 camera: {name}")
        continue
    actor.set_actor_label(f"LB_MCR_V004_CAM_{name}")
    actor.set_actor_location(location, False, False)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    actor.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    actor.tags = [unreal.Name("LB.ControlRoom.v004"), unreal.Name(f"LB.ControlRoom.Camera.{name}"), unreal.Name("LB.Asset.CandidateNotPromoted")]

for actor in actors_api.get_all_level_actors():
    if any(str(tag) == "LB.ControlRoom.v003" for tag in actor.tags):
        actor.tags = [unreal.Name("LB.ControlRoom.v004" if str(tag) == "LB.ControlRoom.v003" else str(tag)) for tag in actor.tags]

levels.save_current_level()
payload = {
    "$schema": "cairnwell/audit/main-control-room-seated-composition-build-v004/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__SEATED_COMPOSITION_LIGHTING_AND_EVIDENCE_CAMERA_REFINED__VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_V004_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "fixed_seated_eye_height_cm": 112.0,
    "seated_camera_y_cm": 82.0,
    "seated_camera_fov_deg": 112.0,
    "screen_mesh_geometry_changed": False,
    "screen_face_orientation_retained_from_v003": True,
    "promotion_authorized": False,
    "gameplay_wired": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))

