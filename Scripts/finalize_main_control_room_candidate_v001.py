"""Repair/finalize the retained v001 control-room map after import succeeded."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
DEST = "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v001"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_IntegrationCandidate_v001"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_import_build_v001.json"
CATEGORIES = (
    "Architecture", "Consoles", "Systems", "Furniture", "Interaction",
    "Service", "Identity", "State_Restored", "State_Mothballed",
)

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)


def all_by_label():
    return {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}


def set_tags(actor, *values):
    actor.tags = [unreal.Name(value) for value in values]


labels = all_by_label()
assembly = []
failures = []
for category in CATEGORIES:
    label = f"LB_MCR_V001_{category}"
    actor = labels.get(label)
    if actor is None:
        mesh_path = f"{DEST}/Meshes/SM_CA_MW_MCR_{category}_v001"
        mesh = library.load_asset(mesh_path)
        if not isinstance(mesh, unreal.StaticMesh):
            failures.append(f"missing mesh {mesh_path}")
            continue
        actor = actors_api.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        actor.set_actor_label(label)
    set_tags(actor, "LB.ControlRoom.v001", f"LB.ControlRoom.Category.{category}", "LB.Asset.CandidateNotPromoted")
    actor.set_actor_hidden_in_game(category == "State_Mothballed")
    actor.set_is_temporarily_hidden_in_editor(category == "State_Mothballed")
    assembly.append(label)

labels = all_by_label()
lights = []
for row, y in enumerate((-235.0, 35.0, 235.0), start=1):
    for column, x in enumerate((-570.0, -380.0, -190.0, 0.0, 190.0, 380.0, 570.0), start=1):
        label = f"LB_MCR_V001_CeilingLight_{row:02d}_{column:02d}"
        light = labels.get(label)
        if light is None:
            light = actors_api.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x, y, 345.0), unreal.Rotator(-90, 0, 0))
            light.set_actor_label(label)
        component = light.get_component_by_class(unreal.RectLightComponent)
        component.set_editor_properties({
            "intensity": 850.0,
            "source_width": 110.0,
            "source_height": 18.0,
            "attenuation_radius": 520.0,
            "light_color": unreal.Color(214, 229, 226, 255),
            "cast_shadows": True,
        })
        set_tags(light, "LB.ControlRoom.v001", "LB.ControlRoom.Lighting.Restored", "LB.Asset.CandidateNotPromoted")
        lights.append(label)

labels = all_by_label()
cameras = []
camera_specs = {
    "SeatedPlayer": (unreal.Vector(0, -38, 112), unreal.Vector(0, 330, 180), 82.0),
    "Front": (unreal.Vector(0, -315, 175), unreal.Vector(0, 90, 155), 70.0),
    "Elevated": (unreal.Vector(650, -560, 520), unreal.Vector(0, 0, 120), 58.0),
    "SystemsWall": (unreal.Vector(0, 175, 205), unreal.Vector(0, -270, 150), 70.0),
}
for name, (location, target, fov) in camera_specs.items():
    label = f"LB_MCR_V001_CAM_{name}"
    camera = labels.get(label)
    rotation = unreal.MathLibrary.find_look_at_rotation(location, target)
    if camera is None:
        camera = actors_api.spawn_actor_from_class(unreal.CameraActor, location, rotation)
        camera.set_actor_label(label)
    else:
        camera.set_actor_location(location, False, False)
        camera.set_actor_rotation(rotation, False)
    camera.camera_component.set_editor_properties({
        "field_of_view": fov,
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })
    set_tags(camera, "LB.ControlRoom.v001", f"LB.ControlRoom.Camera.{name}", "LB.Asset.CandidateNotPromoted")
    cameras.append(label)

levels.save_current_level()
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

labels = all_by_label()
bounds = {}
for category in CATEGORIES:
    actor = labels.get(f"LB_MCR_V001_{category}")
    if actor is None:
        continue
    _origin, extent = actor.get_actor_bounds(False)
    bounds[category] = [round(extent.x * 2, 3), round(extent.y * 2, 3), round(extent.z * 2, 3)]
architecture = bounds.get("Architecture", [0, 0, 0])
horizontal = sorted(architecture[:2])
if not (760.0 <= horizontal[0] <= 820.0 and 1400.0 <= horizontal[1] <= 1480.0):
    failures.append(f"architecture horizontal envelope mismatch cm: {architecture}")

payload = {
    "$schema": "cairnwell/audit/main-control-room-import-build-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_UNREAL_CONTROL_ROOM_CANDIDATE_BUILT__VISUAL_RUNTIME_GAMEPLAY_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_IMPORT_BUILD__NOT_PROMOTED",
    "source_release": "SourceAssets/ControlRoom/MainControlRoom_v004/RELEASE.json",
    "map": MAP,
    "destination": DEST,
    "assembly_actors": assembly,
    "lights": lights,
    "cameras": cameras,
    "combined_mesh_bounds_cm": bounds,
    "source_import_warning": "FBX import logged missing smoothing-group information on multiple source nodes; source re-export gate remains open.",
    "source_promoted": True,
    "unreal_promoted": False,
    "gameplay_wired": False,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))

