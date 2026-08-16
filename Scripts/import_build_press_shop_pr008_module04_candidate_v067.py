"""Import detailed Pro PR-008 Module 04 into isolated candidate v067."""
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/PR008/ServoBlankingLine/Detailed_v001"
RECORDS = json.loads((SOURCE / "pr008_module04_telescopic_support_manifest_v001.json").read_text(encoding="utf-8"))
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module03Candidate_v066"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008Module04Candidate_v067"
DEST = "/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Module04"
MAT = "/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Materials"
PREFIX = "LB_PR008_V067_"
DATUM = unreal.Vector(-500.0, -2000.0, 0.0)
YAW = -90.0
OUT = ROOT / "Saved/Audits/press_shop_pr008_module04_candidate_v067.json"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

materials = {
    key: library.load_asset(f"{MAT}/{name}") for key, name in {
        "charcoal": "M_CA_MW_PR008_FoundryCharcoal_v001", "green": "M_CA_MW_PR008_CairnwellGreen_v001",
        "yellow": "M_CA_MW_PR008_SafetyYellow_v001", "steel": "M_CA_MW_PR008_GroundSteel_v001",
        "galv": "M_CA_MW_PR008_Galvanised_v001", "rubber": "M_CA_MW_PR008_Rubber_v001",
        "sensor": "M_CA_MW_PR008_SensorGlass_v001", "white": "M_CA_MW_PR008_LabelPlate_v001",
        "red": "M_CA_MW_PR008_EStopRed_v001",
    }.items()
}
if any(asset is None for asset in materials.values()):
    raise RuntimeError("Missing shared detailed PR-008 material assets from Module 01")

blue_path = f"{MAT}/M_CA_MW_PR008_DriveBlue_v001"
blue = library.load_asset(blue_path)
if blue is None:
    blue = tools.create_asset("M_CA_MW_PR008_DriveBlue_v001", MAT, unreal.Material, unreal.MaterialFactoryNew())
    editing = unreal.MaterialEditingLibrary
    base = editing.create_material_expression(blue, unreal.MaterialExpressionConstant3Vector, -340, -70)
    base.set_editor_property("constant", unreal.LinearColor(0.015, 0.11, 0.19, 1.0))
    metal = editing.create_material_expression(blue, unreal.MaterialExpressionConstant, -340, 45)
    metal.set_editor_property("r", 0.52)
    rough = editing.create_material_expression(blue, unreal.MaterialExpressionConstant, -340, 150)
    rough.set_editor_property("r", 0.36)
    editing.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    editing.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    editing.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    editing.recompile_material(blue)
    library.save_loaded_asset(blue, only_if_is_dirty=False)
materials["blue"] = blue


def choose_material(slot_name):
    value = slot_name.lower()
    if "driveblue" in value: return materials["blue"]
    if "green" in value: return materials["green"]
    if "yellow" in value: return materials["yellow"]
    if "groundsteel" in value or "steel" in value: return materials["steel"]
    if "galvan" in value: return materials["galv"]
    if "rubber" in value: return materials["rubber"]
    if "sensor" in value: return materials["sensor"]
    if "label" in value: return materials["white"]
    if "red" in value: return materials["red"]
    return materials["charcoal"]


tasks = []
for record in RECORDS:
    task = unreal.AssetImportTask()
    task.set_editor_properties({"filename": str(SOURCE / record["fbx"]), "destination_path": DEST,
        "destination_name": record["name"], "automated": True, "replace_existing": True,
        "replace_existing_settings": True, "save": True})
    options = unreal.FbxImportUI()
    options.set_editor_properties({"import_mesh": True, "import_as_skeletal": False, "import_materials": False,
        "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH})
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({"combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "generate_lightmap_u_vs": True, "auto_generate_collision": record["collision"] == "BlockAll",
        "remove_degenerates": True})
    task.set_editor_property("options", options)
    tasks.append(task)
tools.import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR008Module04Candidate_v067.umap"
if not map_file.exists():
    if not library.duplicate_asset(BASE, MAP) or not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not prepare v067 map")
    unreal.log("LINE_BOSS_PR008_V067_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors_api.destroy_actor(actor)

cage = next((actor for actor in actors_api.get_all_level_actors()
             if actor.get_actor_label() == "LB_PR008_V062_04_TelescopicStripSupport"), None)
if cage is None:
    raise RuntimeError("Missing Pro Module 04 engineering cage")
cage.set_actor_hidden_in_game(True)
for component in cage.get_components_by_class(unreal.SceneComponent):
    component.set_visibility(False, True)


def local_to_world(local_m):
    x, y, z = local_m
    return DATUM + unreal.Vector(y * 100.0, -x * 100.0, z * 100.0)


created, placements = [], []
for record in RECORDS:
    mesh = library.load_asset(f"{DEST}/{record['name']}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing detailed Module 04 mesh {record['name']}")
    world = local_to_world(record["local_location_m"])
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, world, unreal.Rotator(yaw=YAW))
    actor.set_actor_label(PREFIX + record["name"])
    actor.tags = [unreal.Name(value) for value in ("LB.Asset.Candidate.v067", "LB.Asset.CandidateNotPromoted",
        "LB.Station.PR008", "LB.Module.PR008.04.TelescopicSupport", "LB.Authority.CairnwellRemainingMachineryPack.v1")]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_mobility(unreal.ComponentMobility.MOVABLE if record["movable"] else unreal.ComponentMobility.STATIC)
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
        component.set_material(index, choose_material(slot_name))
    no_collision = record["collision"] == "NoCollision"
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION if no_collision else unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_collision_profile_name(unreal.Name("NoCollision" if no_collision else "BlockAll"))
    component.set_editor_property("can_ever_affect_navigation", not no_collision and not record["movable"])
    created.append(actor)
    placements.append({"actor": actor.get_actor_label(), "role": record["role"], "movable": record["movable"],
        "movement": record.get("movement"), "world_location_cm": [world.x, world.y, world.z], "collision": record["collision"]})


def text(label, value, location, size, colour):
    actor = actors_api.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(yaw=180))
    actor.set_actor_label(PREFIX + "TEXT_" + label)
    actor.tags = [unreal.Name("LB.Asset.Candidate.v067"), unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Station.PR008.Identity")]
    component = actor.text_render
    component.set_text(value); component.set_world_size(size); component.set_text_render_color(colour)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


identity = [
    text("Brand", "CAIRNWELL / MOORCROSS", (-683.2, -2000.0, 125.5), 2.7, unreal.Color(45, 130, 105, 255)),
    text("Station", "PR-008  TELESCOPIC SUPPORT", (-683.2, -2000.0, 118.5), 2.8, unreal.Color(35, 38, 40, 255)),
]


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR008.v067"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    return actor


cameras = [
    camera("Module04Inspection", (-900, -2480, 470), (-585, -2000, 95), 44),
    camera("Module04Drive", (-850, -1540, 340), (-585, -2000, 92), 49),
    camera("Module04Elevated", (-1250, -3000, 760), (-585, -2000, 92), 54),
    camera("Module04Connected", (-1750, -3500, 850), (-850, -2000, 110), 59),
]

mins, maxs = [float("inf")] * 3, [float("-inf")] * 3
actor_bounds = []
for actor in created:
    origin, extent = actor.get_actor_bounds(False, False)
    amin, amax = [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z], [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z]
    actor_bounds.append({"actor": actor.get_actor_label(), "min": amin, "max": amax})
    mins, maxs = [min(mins[i], amin[i]) for i in range(3)], [max(maxs[i], amax[i]) for i in range(3)]
expected_min, expected_max = [-685.0, -2120.0, 25.0], [-485.0, -1880.0, 155.0]
within = all(mins[i] >= expected_min[i] - 0.1 and maxs[i] <= expected_max[i] + 0.1 for i in range(3))
if not within:
    worst_x = sorted(actor_bounds, key=lambda item: item["max"][0], reverse=True)[:4]
    worst_min_x = sorted(actor_bounds, key=lambda item: item["min"][0])[:4]
    raise RuntimeError(f"Imported Module 04 exceeds Pro envelope: min={mins} max={maxs} worst_world_x={worst_x} worst_min_world_x={worst_min_x}")

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
payload = {
    "$schema": "line-boss/audit/press-shop-pr008-module04-candidate-v067/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PRO_MODULE04_DETAILED_IMPORT_THREE_STAGE_PIVOT_AND_ENVELOPE_CONTAINMENT_PASS__RUNTIME_COLLISION_NAVIGATION_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP, "base_map": BASE, "source": str(SOURCE), "module_id": "04",
    "semantic_actor_count": len(created), "moving_actor_count": sum(1 for record in RECORDS if record["movable"]),
    "moving_contract": "three proportional telescope stages share local Y 0-1200 mm command; tip speed 60 mm/s; safe pose retracted", "placements": placements,
    "measured_world_bounds_cm": {"min": mins, "max": maxs},
    "expected_world_envelope_cm": {"min": expected_min, "max": expected_max}, "within_pro_envelope": within,
    "hidden_engineering_cage": cage.get_actor_label(), "identity": [actor.get_actor_label() for actor in identity],
    "fixed_cameras": [actor.get_actor_label() for actor in cameras], "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR008_V067_BUILD_PASS actors={len(created)} moving={payload['moving_actor_count']}")
unreal.SystemLibrary.quit_editor()
