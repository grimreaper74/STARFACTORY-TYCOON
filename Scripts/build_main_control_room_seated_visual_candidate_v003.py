"""Create isolated v003 seated-view/lighting refinement from control-room v002."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_PresentationCandidate_v002"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_SeatedVisualCandidate_v003"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_seated_visual_build_v003.json"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP}")

actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
failures = []
lighting = []
for label, actor in list(actors.items()):
    if not label.startswith("LB_MCR_V002_CeilingLight_"):
        continue
    new_label = label.replace("V002", "V003")
    actor.set_actor_label(new_label)
    component = actor.get_component_by_class(unreal.RectLightComponent)
    if component is None:
        failures.append(f"missing RectLightComponent: {label}")
        continue
    component.set_editor_properties({
        "intensity": 95.0,
        "attenuation_radius": 560.0,
        "source_width": 135.0,
        "source_height": 22.0,
        "cast_shadows": False,
    })
    actor.tags = [unreal.Name("LB.ControlRoom.v003"), unreal.Name("LB.ControlRoom.Lighting.Ambient"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    lighting.append(new_label)

# Four localized shadowed task lights preserve depth without casting 21
# overlapping hard shadow patterns across the overview wall.
for index, (location, target) in enumerate((
    ((-430, 30, 315), (-350, -150, 105)),
    ((430, 30, 315), (350, -150, 105)),
    ((-330, -230, 305), (-260, -255, 125)),
    ((330, -230, 305), (260, -255, 125)),
), start=1):
    light = actors_api.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*location), unreal.Rotator())
    light.set_actor_label(f"LB_MCR_V003_TaskLight_{index:02d}")
    light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(light.get_actor_location(), unreal.Vector(*target)), False)
    component = light.get_component_by_class(unreal.RectLightComponent)
    component.set_editor_properties({
        "intensity": 165.0,
        "attenuation_radius": 480.0,
        "source_width": 95.0,
        "source_height": 20.0,
        "cast_shadows": True,
        "light_color": unreal.Color(205, 224, 220, 255),
    })
    light.tags = [unreal.Name("LB.ControlRoom.v003"), unreal.Name("LB.ControlRoom.Lighting.Task"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    lighting.append(light.get_actor_label())

exposure = actors.get("LB_MCR_V002_Exposure")
if exposure is None:
    failures.append("missing v002 exposure volume")
else:
    exposure.set_actor_label("LB_MCR_V003_Exposure")
    settings = exposure.get_editor_property("settings")
    settings.set_editor_property("auto_exposure_bias", -1.15)
    exposure.set_editor_property("settings", settings)
    exposure.tags = [unreal.Name("LB.ControlRoom.v003"), unreal.Name("LB.Asset.CandidateNotPromoted")]

camera_specs = {
    "SeatedPlayer": (unreal.Vector(0, 38, 112), unreal.Vector(0, -335, 176), 102.0),
    "Front": (unreal.Vector(0, 350, 185), unreal.Vector(0, -95, 150), 76.0),
    "Elevated": (unreal.Vector(650, 560, 520), unreal.Vector(0, 0, 120), 62.0),
    "SystemsWall": (unreal.Vector(0, -205, 205), unreal.Vector(0, 275, 150), 76.0),
}
for name, (location, target, fov) in camera_specs.items():
    actor = actors.get(f"LB_MCR_V002_CAM_{name}")
    if actor is None:
        failures.append(f"missing v002 camera: {name}")
        continue
    actor.set_actor_label(f"LB_MCR_V003_CAM_{name}")
    actor.set_actor_location(location, False, False)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    actor.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    actor.tags = [unreal.Name("LB.ControlRoom.v003"), unreal.Name(f"LB.ControlRoom.Camera.{name}"), unreal.Name("LB.Asset.CandidateNotPromoted")]

for actor in actors_api.get_all_level_actors():
    if any(str(tag) == "LB.ControlRoom.v002" for tag in actor.tags):
        actor.tags = [unreal.Name("LB.ControlRoom.v003" if str(tag) == "LB.ControlRoom.v002" else str(tag)) for tag in actor.tags]

levels.save_current_level()
payload = {
    "$schema": "cairnwell/audit/main-control-room-seated-visual-build-v003/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__SEATED_EYE_DATUM_RETAINED_WIDER_FOV_AND_LAYERED_LIGHTING_BUILT__VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_V003_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "fixed_seated_eye_height_cm": 112.0,
    "seated_horizontal_fov_deg": 102.0,
    "ambient_light_count": 21,
    "task_light_count": 4,
    "promotion_authorized": False,
    "gameplay_wired": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))

