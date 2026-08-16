"""Import the modular PR-006 leveller and assemble an unpromoted v054 integration candidate."""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

PROJECT = Path(unreal.Paths.project_dir())
SOURCE = PROJECT / "SourceAssets/PR006/PrecisionCassetteLeveller/Candidate_v001"
MANIFEST = SOURCE / "pr006_precision_leveller_module_manifest_v001.json"
BASE_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR006LevellerCandidate_v054"
DEST = "/Game/LineBoss/Stations/Press/PR006/Candidate_v001"
MAT_DEST = DEST + "/Materials"
AUDIT = PROJECT / "Saved/Audits/press_shop_pr006_leveller_candidate_v054.json"
DATUM = unreal.Vector(-1700.0, -2000.0, 0.0)
PREFIX = "LB_PR006_V054_"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mel = unreal.MaterialEditingLibrary


def material(name, colour, metallic, roughness):
    path = f"{MAT_DEST}/{name}"
    asset = library.load_asset(path) if library.does_asset_exist(path) else None
    if asset is None:
        asset = tools.create_asset(name, MAT_DEST, unreal.Material, unreal.MaterialFactoryNew())
    if asset is None:
        raise RuntimeError(f"Could not create {path}")
    mel.delete_all_material_expressions(asset)
    base = mel.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -360, -80)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -360, 45)
    metal.set_editor_property("r", metallic)
    rough = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -360, 155)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(asset)
    library.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


materials = {
    "frame": material("M_PR006_CharcoalFrame_v001", (0.045, 0.055, 0.062), 0.72, 0.40),
    "panel": material("M_PR006_WarmGreyPanel_v001", (0.22, 0.235, 0.235), 0.56, 0.46),
    "yellow": material("M_PR006_SafetyYellow_v001", (0.74, 0.39, 0.018), 0.34, 0.47),
    "steel": material("M_PR006_RollSteel_v001", (0.30, 0.325, 0.34), 0.90, 0.28),
    "blue": material("M_PR006_HydraulicBlue_v001", (0.025, 0.12, 0.24), 0.58, 0.41),
    "white": material("M_PR006_ServiceWhite_v001", (0.68, 0.70, 0.68), 0.14, 0.58),
    "red": material("M_PR006_EStopRed_v001", (0.48, 0.008, 0.004), 0.16, 0.41),
}


def material_for(name):
    lower = name.lower()
    if "estopbutton" in lower:
        return materials["red"]
    if any(token in lower for token in ("roll", "guide", "strip")):
        return materials["steel"]
    if any(token in lower for token in ("motor", "cylinder")):
        return materials["blue"]
    if any(token in lower for token in ("cassetteidplate",)):
        return materials["white"]
    if any(token in lower for token in ("uppercassette", "lift", "guard", "sensor", "coupling", "estopstation")):
        return materials["yellow"]
    if any(token in lower for token in ("frameoperator", "framedrive")):
        return materials["panel"]
    return materials["frame"]


records = json.loads(MANIFEST.read_text(encoding="utf-8"))
tasks = []
for record in records:
    if record["name"] in ("PR006_Identity", "PR006_CassetteLabel"):
        continue
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE / record["fbx"]), "destination_path": DEST,
        "destination_name": "SM_" + record["name"], "automated": True,
        "replace_existing": True, "replace_existing_settings": True, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False, "import_materials": False,
        "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "force_front_x_axis": False, "generate_lightmap_u_vs": True,
        "auto_generate_collision": True, "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    tasks.append(task)
tools.import_asset_tasks(tasks)

if not library.does_asset_exist(MAP) and not library.duplicate_asset(BASE_MAP, MAP):
    raise RuntimeError("Could not duplicate v053 to v054")
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for existing in list(actors.get_all_level_actors()):
    if existing.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(existing)

created = []
for record in records:
    if record["name"] in ("PR006_Identity", "PR006_CassetteLabel"):
        continue
    mesh = library.load_asset(f"{DEST}/SM_{record['name']}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing imported mesh {record['name']}")
    location = record["location_m"]
    world = DATUM + unreal.Vector(location[0] * 100.0, location[1] * 100.0, location[2] * 100.0)
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, world, unreal.Rotator())
    actor.set_actor_label(PREFIX + record["name"])
    actor.tags = [unreal.Name("LB.Asset.Candidate.v054"), unreal.Name("LB.Asset.CandidateNotPromoted"),
                  unreal.Name("LB.Station.PR006"), unreal.Name("LB.Machine.Modular")]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_mobility(unreal.ComponentMobility.MOVABLE if any(token in record["name"] for token in
        ("Roll_", "UpperCassette", "GapCylinder", "DriveMotor")) else unreal.ComponentMobility.STATIC)
    component.set_material(0, material_for(record["name"]))
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_collision_profile_name(unreal.Name("BlockAll"))
    component.set_editor_property("can_ever_affect_navigation", False)
    created.append(actor)


def text_actor(label, text, location, size, colour):
    actor = actors.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(roll=0.0, pitch=0.0, yaw=-90.0))
    actor.set_actor_label(PREFIX + label)
    actor.tags = [unreal.Name("LB.Asset.Candidate.v054"), unreal.Name("LB.Asset.CandidateNotPromoted"),
                  unreal.Name("LB.Station.PR006.Identity")]
    component = actor.get_editor_property("text_render")
    component.set_text(text)
    component.set_world_size(size)
    component.set_text_render_color(colour)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


identity = [
    text_actor("Identity_Cairnwell", "CAIRNWELL AUTOMOTIVE", (-1608, -2178, 179), 4.0,
               unreal.Color(35, 82, 72, 255)),
    text_actor("Identity_Station", "PR-006  PRECISION LEVELLER", (-1608, -2178, 171), 5.5,
               unreal.Color(24, 29, 31, 255)),
    text_actor("Identity_Cassette", "CASSETTE L-1500 / GAP AUTO", (-1608, -2178, 163), 3.3,
               unreal.Color(38, 43, 45, 255)),
]


def spot(label, location, target, intensity, colour):
    actor = actors.spawn_actor_from_class(unreal.SpotLight, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + label)
    actor.tags = [unreal.Name("LB.Lighting.Candidate"), unreal.Name("LB.Lighting.PR006.Task"),
                  unreal.Name("LB.Asset.Candidate.v054"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.spot_light_component.set_editor_properties({
        "intensity": intensity, "attenuation_radius": 1750.0,
        "inner_cone_angle": 30.0, "outer_cone_angle": 58.0,
        "source_radius": 65.0, "soft_source_radius": 120.0,
        "cast_shadows": False, "light_color": unreal.Color(*colour, 255),
    })
    return actor


lights = [
    spot("OperatorTaskLight", (-2350, -3000, 850), (-1700, -2000, 125), 1050, (224, 233, 244)),
    spot("DriveTaskLight", (-900, -1050, 820), (-1700, -2000, 130), 850, (244, 225, 202)),
]


def camera(label, location, target, fov):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR006.v054"),
                  unreal.Name("LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True,
    })
    return actor


cameras = [
    camera("Operator", (-1100, -2800, 330), (-1700, -2000, 130), 48),
    camera("Drive", (-1050, -1150, 360), (-1700, -2000, 130), 50),
    camera("FrontEnd", (-2700, -3350, 520), (-2650, -2000, 115), 68),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "line-boss/audit/press-shop-pr006-leveller-candidate-v054/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "MODULAR_PR006_LEVELLER_IMPORTED_AND_ASSEMBLED__RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP, "base_map": BASE_MAP, "station_datum_cm": [-1700, -2000, 0],
    "source": str(SOURCE), "module_count": len(created),
    "moving_module_count": sum(1 for actor in created if actor.static_mesh_component.get_editor_property("mobility") == unreal.ComponentMobility.MOVABLE),
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "task_lights": [actor.get_actor_label() for actor in lights],
    "native_identity": [actor.get_actor_label() for actor in identity],
    "hmi_included": False, "guarding_included": False, "runtime_controller_included": False,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR006_V054_IMPORT_BUILD_PASS modules={len(created)}")
unreal.SystemLibrary.quit_editor()
