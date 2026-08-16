"""Add stationary, route-safe licensed logistics dressing to PR-005 v053."""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053"
ROOT = "/Game/LineBoss/Vendor/FactoryEnvironment/Logistics/Meshes"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr005_logistics_candidate_v053.json"
PREFIX = "LB_PR005_V053_"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)

yellow = unreal.load_asset(
    "/Game/LineBoss/Stations/Press/PR005/Candidate_v048/Materials/M_PR005_CADRoute_SafetyYellow_v048")
blue = unreal.load_asset(
    "/Game/LineBoss/Stations/Press/PR005/Candidate_v050/Materials/M_PR005_Service_ReturnBlue_v050")
if yellow is None or blue is None:
    raise RuntimeError("Missing retained controlled logistics colours")


def mesh_actor(label, name, location, yaw, overrides=()):
    mesh = unreal.load_asset(f"{ROOT}/{name}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing contained logistics mesh {name}")
    rotation = unreal.Rotator()
    rotation.set_editor_properties({"pitch": 0.0, "yaw": yaw, "roll": 0.0})
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), rotation)
    actor.set_actor_label(PREFIX + label)
    actor.tags = [unreal.Name("LB.Asset.Candidate.v053"), unreal.Name("LB.Asset.CandidateNotPromoted"),
                  unreal.Name("LB.Logistics.StaticDressing"), unreal.Name("LB.Vendor.FactoryEnvironment")]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_mobility(unreal.ComponentMobility.STATIC)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_collision_profile_name(unreal.Name("BlockAll"))
    component.set_editor_property("can_ever_affect_navigation", True)
    for index, material in enumerate(overrides):
        if material is not None:
            component.set_material(index, material)
    return actor


created = [
    mesh_actor("ReturnStillage_Base", "SM_PalletCart", (-3075.0, -3375.0, 63.5), 8.0),
    mesh_actor("ReturnStillage_Open", "SM_PalletCart_PalletBox_open", (-3075.0, -3375.0, 59.0), 8.0),
    mesh_actor("ServicePallet", "SM_PlasticPallet01", (-2780.0, -3340.0, 10.0), -8.0, (blue,)),
]
for index, (x, y, yaw) in enumerate(((-2825.0, -3370.0, -8.0), (-2760.0, -3375.0, -3.0),
                                      (-2795.0, -3310.0, 5.0)), 1):
    created.append(mesh_actor(f"ServiceCrate_{index:02d}", "SM_AssemblyLineCrate01",
                              (x, y, 30.0), yaw, (yellow,)))


def camera(label, location, target, fov):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR005.v053"),
                  unreal.Name("LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True,
    })
    return actor

cameras = [
    camera("LogisticsPlayer", (-2450.0, -3975.0, 190.0), (-2960.0, -3350.0, 75.0), 48.0),
    camera("LogisticsElevated", (-2375.0, -4025.0, 470.0), (-2960.0, -3350.0, 65.0), 50.0),
    camera("LogisticsWholeLine", (-2225.0, -4300.0, 720.0), (-3525.0, -2675.0, 120.0), 58.0),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
payload = {
    "$schema": "line-boss/audit/press-shop-pr005-logistics-candidate-v053/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "STATIONARY_LOGISTICS_DRESSING_BUILT__FULL_RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP, "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceIdentityCandidate_v052",
    "actors": [actor.get_actor_label() for actor in created],
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "source_pack": "Factory Environment Collection", "forklift_included": False,
    "placeholder_worker_included": False, "collision_profile": "BlockAll",
    "affects_navigation": True, "equipment_coordinates_modified": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_LOGISTICS_V053_BUILD_PASS actors={len(created)}")
unreal.SystemLibrary.quit_editor()
