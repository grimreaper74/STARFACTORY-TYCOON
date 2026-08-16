"""Import and assemble the isolated PR-008 Pro-authority envelope candidate v062."""
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/PR008/ServoBlankingLine/ProEnvelope_v001"
RECORDS = json.loads((SOURCE / "pr008_pro_envelope_module_manifest_v001.json").read_text(encoding="utf-8"))
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008ProEnvelopeCandidate_v062"
DEST = "/Game/LineBoss/Stations/Press/PR008/ProEnvelope_v001"
MAT = DEST + "/Materials"
PREFIX = "LB_PR008_V062_"
DATUM = unreal.Vector(-500.0, -2000.0, 0.0)
YAW = -90.0
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_pro_envelope_candidate_v062.json"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material_editing = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def make_material(name, colour, metallic, roughness):
    path = f"{MAT}/{name}"
    asset = library.load_asset(path) if library.does_asset_exist(path) else asset_tools.create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    material_editing.delete_all_material_expressions(asset)
    base = material_editing.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -340, -70)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = material_editing.create_material_expression(asset, unreal.MaterialExpressionConstant, -340, 45)
    metal.set_editor_property("r", metallic)
    rough = material_editing.create_material_expression(asset, unreal.MaterialExpressionConstant, -340, 150)
    rough.set_editor_property("r", roughness)
    material_editing.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    material_editing.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    material_editing.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    material_editing.recompile_material(asset)
    library.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


materials = {
    "green": make_material("M_CA_MW_PR008_ENV_CairnwellGreen", (0.014, 0.070, 0.058), 0.55, 0.44),
    "yellow": make_material("M_CA_MW_PR008_ENV_SafetyYellow", (0.888, 0.533, 0.0), 0.30, 0.48),
    "charcoal": make_material("M_CA_MW_PR008_ENV_FoundryCharcoal", (0.014, 0.018, 0.022), 0.75, 0.42),
    "steel": make_material("M_CA_MW_PR008_ENV_WorkedSteel", (0.267, 0.298, 0.318), 0.90, 0.32),
    "white": make_material("M_CA_MW_PR008_ENV_FixedAuthority", (0.70, 0.73, 0.75), 0.15, 0.58),
}
module_material = {
    "00": "white", "01": "green", "02": "yellow", "03": "charcoal", "04": "steel",
    "05": "green", "06": "charcoal", "07": "steel", "08": "green", "09": "charcoal",
    "10": "yellow", "11": "steel",
}

tasks = []
for record in RECORDS:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE / record["fbx"]),
        "destination_path": DEST,
        "destination_name": record["asset_name"],
        "automated": True,
        "replace_existing": True,
        "replace_existing_settings": True,
        "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": False,
        "import_materials": False,
        "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    static_data = options.get_editor_property("static_mesh_import_data")
    static_data.set_editor_properties({
        "combine_meshes": True,
        "convert_scene": True,
        "convert_scene_unit": True,
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": False,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    tasks.append(task)

asset_tools.import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR008ProEnvelopeCandidate_v062.umap"
if not map_file.exists():
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError("Could not duplicate v061 to v062")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not save prepared v062 map")
    unreal.log("LINE_BOSS_PR008_V062_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors_api.destroy_actor(actor)

# Preserve all inherited assets but suppress the superseded PR-008 visuals in this
# derivative. Native PR-008 and PR-006 authority actors remain present.
hidden_old = []
for actor in list(actors_api.get_all_level_actors()):
    label = actor.get_actor_label()
    should_hide = label.startswith("LB_PR008_V058_") or label.startswith("LB_PR008_V059_")
    should_hide = should_hide or label.startswith("LB_PR008_V060_HMI_")
    if should_hide:
        actor.set_actor_hidden_in_game(True)
        for component in actor.get_components_by_class(unreal.SceneComponent):
            component.set_visibility(False, True)
        hidden_old.append(label)


def local_mm_to_world(local_mm):
    # Station yaw -90: local +Y -> world +X; local +X -> world -Y.
    local_x, local_y, local_z = local_mm
    return DATUM + unreal.Vector(local_y / 10.0, -local_x / 10.0, local_z / 10.0)


created = []
positions = []
planning_actor = None
for record in RECORDS:
    mesh_path = f"{DEST}/{record['asset_name']}"
    mesh = library.load_asset(mesh_path)
    if not mesh:
        raise RuntimeError(f"Missing imported Pro-envelope mesh {mesh_path}")
    world = local_mm_to_world(record["resolved_blockout_centre_mm"])
    actor = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor, world, unreal.Rotator(yaw=YAW))
    actor.set_actor_label(PREFIX + record["module_id"] + "_" + record["module_name"])
    actor.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v062", "LB.Asset.CandidateNotPromoted", "LB.Asset.EngineeringEnvelope",
        "LB.Station.PR008", "LB.Authority.CairnwellRemainingMachineryPack.v1")]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_material(0, materials[module_material[record["module_id"]]])
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    created.append(actor)
    positions.append({
        "module_id": record["module_id"],
        "actor": actor.get_actor_label(),
        "resolved_local_centre_mm": record["resolved_blockout_centre_mm"],
        "world_location_cm": [world.x, world.y, world.z],
        "world_yaw_degrees": YAW,
        "z_resolution": record["z_resolution"],
    })
    if record["module_id"] == "00":
        planning_actor = actor

if planning_actor is None:
    raise RuntimeError("Fixed planning-envelope actor was not created")


def text_actor(label, text_value, location, size, colour):
    actor = actors_api.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(yaw=-90))
    actor.set_actor_label(PREFIX + "TEXT_" + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v062", "LB.Asset.CandidateNotPromoted", "LB.Station.PR008.EngineeringLabel")]
    component = actor.text_render
    component.set_text(text_value)
    component.set_world_size(size)
    component.set_text_render_color(colour)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


labels = [
    text_actor("Brand", "CAIRNWELL AUTOMOTIVE / MOORCROSS WORKS", (-500, -2292, 445), 6.0, unreal.Color(60, 150, 125, 255)),
    text_actor("Station", "PR-008  PRO ENGINEERING ENVELOPE", (-500, -2292, 432), 5.2, unreal.Color(235, 238, 232, 255)),
    text_actor("Status", "BLOCKOUT VALIDATION / NOT RELEASE ART", (-500, -2292, 420), 4.0, unreal.Color(242, 195, 0, 255)),
]


def task_light(label, location, target, intensity, colour):
    actor = actors_api.spawn_actor_from_class(unreal.SpotLight, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "LIGHT_" + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v062", "LB.Asset.CandidateNotPromoted", "LB.Lighting.PR008.Envelope")]
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.spot_light_component.set_editor_properties({
        "intensity": intensity, "attenuation_radius": 2100.0,
        "inner_cone_angle": 30.0, "outer_cone_angle": 62.0,
        "source_radius": 80.0, "soft_source_radius": 140.0,
        "cast_shadows": False, "light_color": unreal.Color(*colour, 255),
    })
    return actor


lights = [
    task_light("Operator", (-520, -3450, 1100), (-500, -2000, 170), 1350, (224, 235, 244)),
    task_light("Discharge", (350, -900, 950), (-100, -2000, 160), 950, (244, 225, 202)),
]


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Camera.Validation", "LB.Camera.Fixed.PR008.v062", "LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    return actor


cameras = [
    camera("Operator", (-500, -3400, 650), (-500, -2000, 170), 54),
    camera("Elevated", (-1150, -3500, 1350), (-500, -2000, 155), 58),
    camera("Connected", (-2600, -3800, 1000), (-1050, -2000, 150), 62),
]

origin, extent = planning_actor.get_actor_bounds(False)
measured_dimensions = [extent.x * 2.0, extent.y * 2.0, extent.z * 2.0]
expected_dimensions = [1040.0, 556.0, 449.0]
errors = [abs(measured_dimensions[index] - expected_dimensions[index]) for index in range(3)]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-pro-envelope-candidate-v062/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PRO_AUTHORITY_ENVELOPE_IMPORTED_AND_ASSEMBLED__FIXED_CAMERA_AND_RUNTIME_GATES_REQUIRED__NOT_RELEASE_ART__NOT_PROMOTED",
    "map": MAP,
    "base_map": BASE,
    "station_datum_cm": [-500.0, -2000.0, 0.0],
    "station_yaw_degrees": YAW,
    "axis_mapping": "local +Y -> world +X; local +X -> world -Y",
    "scheduled_module_count": 10,
    "validation_asset_count": len(created),
    "hidden_superseded_pr008_visual_actor_count": len(hidden_old),
    "hidden_superseded_pr008_visual_actors": hidden_old,
    "module_placements": positions,
    "fixed_planning_envelope": {
        "expected_world_dimensions_cm": expected_dimensions,
        "measured_world_dimensions_cm": measured_dimensions,
        "absolute_error_cm": errors,
        "actor_bounds_origin_cm": [origin.x, origin.y, origin.z],
    },
    "floor_base_interpretation_modules": ["08", "09"],
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "identity_labels": [actor.get_actor_label() for actor in labels],
    "task_lights": [actor.get_actor_label() for actor in lights],
    "collision": "NoCollision engineering envelopes; cannot affect navigation",
    "native_pr008_authority_preserved": True,
    "native_pr006_authority_preserved": True,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    "LINE_BOSS_PR008_V062_BUILD_PASS "
    f"assets={len(created)} hidden_old={len(hidden_old)} envelope_error_cm={errors}")
unreal.SystemLibrary.quit_editor()
