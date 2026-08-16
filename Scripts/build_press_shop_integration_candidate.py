"""Compose the Press Shop foundation with PR-005 at master-plan coordinates."""

import json
import math
from pathlib import Path

import unreal


FOUNDATION = "/Game/LineBoss/Maps/LB_PressShop_Foundation"
MAP = "/Game/LineBoss/Maps/LB_PressShop_IntegrationCandidate_v002"
ROOT = Path(unreal.Paths.project_dir())
PLACEMENTS = ROOT / "Content/LineBoss/Data/press_shop_station_placements_v001.json"
GAMEPLAY_CONTRACT = ROOT / "SourceAssets/PR005/pr005_gameplay_contract_v001.json"
IMPORT_AUDIT = ROOT / "Saved/Audits/pr005_modular_unreal_import_v001.json"
OUTPUT = ROOT / "Saved/Audits/press_shop_integration_candidate_v002.json"
PREFIX = "LB_INT_PR005_"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
    raise RuntimeError(
        "Integration map is missing; run prepare_press_shop_integration_candidate.py "
        "in a separate Unreal commandlet session first"
    )
if not levels.get_current_level().get_path_name().startswith(MAP + "."):
    levels.load_level(MAP)

for actor in actors.get_all_level_actors():
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)

# The production camera uses a cutaway building.  Roof steel remains available
# in the editor and in exterior shots, but must not obscure machinery during
# normal elevated management play.
hidden_cutaway_actors = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith("LB_PRESS_RoofBeam_"):
        actor.set_actor_hidden_in_game(True)
        hidden_cutaway_actors.append(label)

placement = next(
    item for item in json.loads(PLACEMENTS.read_text(encoding="utf-8"))["stations"]
    if item["id"] == "PR-005"
)
records = json.loads(IMPORT_AUDIT.read_text(encoding="utf-8"))["records"]
gameplay_contract = json.loads(GAMEPLAY_CONTRACT.read_text(encoding="utf-8"))
origin = placement["world_origin_cm"]
yaw = math.radians(float(placement["yaw_degrees"]))
cos_yaw, sin_yaw = math.cos(yaw), math.sin(yaw)


def local_import_position(pivot):
    return [float(pivot[0]) * 100.0, -float(pivot[1]) * 100.0, float(pivot[2]) * 100.0]


def to_world(local):
    return unreal.Vector(
        origin[0] + local[0] * cos_yaw - local[1] * sin_yaw,
        origin[1] + local[0] * sin_yaw + local[1] * cos_yaw,
        origin[2] + local[2],
    )


port_world = {
    port["id"]: list(to_world(port["location"]).to_tuple())
    for port in gameplay_contract["ports"]
}
input_x = port_world["PR005-IN-COIL"][0]
strip_output_x = port_world["PR005-OUT-STRIP"][0]
if not input_x < origin[0] < strip_output_x:
    raise RuntimeError(
        "PR-005 orientation is reversed: the coil input must be west/upstream "
        "and the strip output east/downstream in facility world +X flow "
        f"(input_x={input_x}, origin_x={origin[0]}, output_x={strip_output_x})"
    )


created = []
for record in records:
    mesh = unreal.load_asset(record["asset"])
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing PR-005 candidate mesh {record['asset']}")
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor,
        to_world(local_import_position(record["pivot_blender_m"])),
        unreal.Rotator(0.0, 0.0, placement["yaw_degrees"]),
    )
    actor.set_actor_label(f"{PREFIX}{record['module_id']}_{record['semantic_group']}")
    component = actor.get_editor_property("static_mesh_component")
    component.set_static_mesh(mesh)
    component.set_editor_property(
        "mobility",
        unreal.ComponentMobility.MOVABLE if record["is_mover"] else unreal.ComponentMobility.STATIC,
    )
    tags = [
        unreal.Name("LB.Station.PR-005"),
        unreal.Name("LB.Asset.Candidate.v001"),
        unreal.Name("LB.Integration.PressShop"),
        unreal.Name("LB.Motion.Mover" if record["is_mover"] else "LB.Motion.Static"),
    ]
    actor.set_editor_property("tags", tags)
    created.append(actor)

# A station datum allows future streaming/runtime code to load the same local
# assembly without depending on the generated actor labels.
datum = actors.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(*origin), unreal.Rotator())
datum.set_actor_label(PREFIX + "Datum")
datum.set_editor_property("tags", [
    unreal.Name("LB.Station.Datum"), unreal.Name("LB.Station.PR-005"),
    unreal.Name("LB.Streaming.Press.FrontEnd"),
])

# A restrained local lift keeps the dark machinery readable without bleaching
# the concrete floor under the foundation level's existing lighting rig.
for suffix, local_pos, intensity in (
    ("Key", (350.0, 450.0, 650.0), 90.0),
    ("Fill", (-420.0, -120.0, 480.0), 35.0),
):
    light = actors.spawn_actor_from_class(unreal.RectLight, to_world(local_pos), unreal.Rotator())
    light.set_actor_label(PREFIX + "Light_" + suffix)
    light.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(light.get_actor_location(), unreal.Vector(origin[0], origin[1], 110.0)),
        False,
    )
    light.get_editor_property("rect_light_component").set_editor_properties({
        "intensity": intensity,
        "attenuation_radius": 1050.0,
        "source_width": 450.0,
        "source_height": 260.0,
    })

camera = actors.spawn_actor_from_class(unreal.CameraActor, to_world((850.0, 1050.0, 850.0)), unreal.Rotator())
camera.set_actor_label(PREFIX + "CAM_Context")
camera.set_actor_rotation(
    unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(origin[0], origin[1], 105.0)),
    False,
)
camera.get_editor_property("camera_component").set_editor_property("field_of_view", 42.0)

# Approximate normal gameplay framing for the first campaign chapter. The player
# will pan this elevated oblique camera; it intentionally shows the front end at
# a readable scale rather than fitting all 220 metres into every frame.
player_camera = actors.spawn_actor_from_class(
    unreal.CameraActor, unreal.Vector(-9000.0, 2600.0, 3900.0), unreal.Rotator()
)
player_camera.set_actor_label(PREFIX + "CAM_PlayerFrontEnd")
player_camera.set_actor_rotation(
    unreal.MathLibrary.find_look_at_rotation(
        player_camera.get_actor_location(), unreal.Vector(-4200.0, -2000.0, 90.0)
    ),
    False,
)
player_camera.get_editor_property("camera_component").set_editor_property("field_of_view", 47.0)

if not levels.save_current_level():
    raise RuntimeError("Failed saving Press Shop integration candidate")

result = {
    "status": "INTEGRATION_CANDIDATE_NOT_PROMOTED",
    "map": MAP,
    "foundation": FOUNDATION,
    "station": placement,
    "mesh_actor_count": len(created),
    "mover_count": sum(1 for record in records if record["is_mover"]),
    "gameplay_ports_world_cm": port_world,
    "material_flow_orientation_pass": True,
    "cutaway_hidden_actor_count": len(hidden_cutaway_actors),
    "fixed_cameras": [PREFIX + "CAM_PlayerFrontEnd", PREFIX + "CAM_Context"],
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(
    f"LINE_BOSS_PRESS_SHOP_INTEGRATION_BUILD_PASS meshes={len(created)} "
    f"movers={result['mover_count']} map={MAP}"
)
