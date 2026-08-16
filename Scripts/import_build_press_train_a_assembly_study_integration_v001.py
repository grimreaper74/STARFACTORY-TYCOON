"""First isolated UE 5.8 import/integration study of retained Train A AssemblyStudy_v001."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v001"
MANIFEST_PATH = SOURCE / "PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_v001.json"
VALIDATION_PATH = SOURCE / "PRESS_TRAIN_A_ASSEMBLY_STUDY_VALIDATION_v001.json"
REVIEW_PATH = SOURCE / "PRESS_TRAIN_A_ASSEMBLY_STUDY_VISUAL_REVIEW_v001.md"
ASSEMBLY_FBX = SOURCE / "FBX/SM_CA_MW_PTA_SevenStageAssemblyStudy_v001.fbx"
DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v001"
GEOMETRY_DEST = DEST + "/Geometry"
MODULE_DEST = DEST + "/Modules"
MATERIAL_DEST = DEST + "/Materials"
MAP = "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyIntegrationCandidate_v001"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_assembly_integration_build_v001.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mel = unreal.MaterialEditingLibrary


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
validation = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
if validation.get("status") != "PASS":
    raise RuntimeError("Assembly source validation is not PASS")
if manifest.get("world_placement") != "TBC_NOT_INVENTED":
    raise RuntimeError("Assembly source no longer preserves TBC world placement")
if sha(ASSEMBLY_FBX) != manifest["assembly_fbx"]["sha256"]:
    raise RuntimeError("Assembly FBX hash differs from retained manifest")
for record in manifest["source_files"]:
    source_file = ROOT / record["path"]
    if not source_file.exists() or sha(source_file) != record["sha256"]:
        raise RuntimeError(f"Immutable shared input missing or changed: {record['path']}")

protected = {
    "/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053",
    "/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v063",
    "/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v069",
    "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107",
    "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006",
    "/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_v113",
}
if MAP in protected:
    raise RuntimeError("Target map collides with protected scope")
resume_own_partial = library.does_directory_exist(DEST) and not library.does_asset_exist(MAP) and not OUT.exists()
if library.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError(f"Refusing to overwrite existing candidate or receipt: {MAP} / {DEST}")


def import_static(filename, destination_path, destination_name, combine):
    expected = f"{destination_path}/{destination_name}"
    existing = library.load_asset(expected)
    if resume_own_partial and isinstance(existing, unreal.StaticMesh):
        return existing, [expected + "." + destination_name]
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(filename), "destination_path": destination_path,
        "destination_name": destination_name, "automated": True,
        "replace_existing": False, "replace_existing_settings": False, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False,
        "import_materials": False, "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": combine, "convert_scene": True, "convert_scene_unit": True,
        "force_front_x_axis": False, "transform_vertex_to_absolute": False,
        "bake_pivot_in_vertex": False, "import_uniform_scale": 1.0,
        "generate_lightmap_u_vs": True, "auto_generate_collision": False,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    asset_tools.import_asset_tasks([task])
    imported = [str(value) for value in task.get_editor_property("imported_object_paths")]
    if not imported:
        raise RuntimeError(f"FBX import produced no asset: {filename}")
    asset = library.load_asset(expected)
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Expected static mesh not found: {expected}; imported={imported}")
    return asset, imported


def material_slot_names(mesh):
    return [str(value.get_editor_property("material_slot_name"))
            for value in mesh.get_editor_property("static_materials")]


assembly_mesh, assembly_import_paths = import_static(
    ASSEMBLY_FBX, GEOMETRY_DEST, "SM_CA_MW_PTA_AssemblyStudy_v001", True)
module_assets = {}
module_import_paths = []
for record in manifest["source_files"]:
    path = ROOT / record["path"]
    name = path.stem
    mesh, imported = import_static(path, MODULE_DEST, name, True)
    module_assets[name] = mesh
    module_import_paths.extend(imported)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()


PALETTE = {
    "Charcoal": ((0.018, 0.024, 0.027, 1), 0.38, 0.05, False),
    "Foundation": ((0.10, 0.115, 0.12, 1), 0.78, 0.02, False),
    "WorkedSteel": ((0.22, 0.25, 0.26, 1), 0.34, 0.82, False),
    "Green": ((0.018, 0.145, 0.105, 1), 0.44, 0.18, False),
    "SafetyYellow": ((0.90, 0.55, 0.008, 1), 0.40, 0.08, False),
    "TrainABlue": ((0.035, 0.22, 0.52, 1), 0.38, 0.12, False),
    "DarkRubber": ((0.008, 0.010, 0.011, 1), 0.82, 0.00, False),
    "LabelIvory": ((0.72, 0.76, 0.72, 1), 0.48, 0.03, False),
    "HydraulicRed": ((0.26, 0.035, 0.020, 1), 0.48, 0.24, False),
    "PneumaticBlue": ((0.015, 0.25, 0.48, 1), 0.40, 0.18, False),
    "ElectricalOrange": ((0.58, 0.16, 0.025, 1), 0.42, 0.12, False),
    "InspectionWhite": ((0.75, 0.82, 0.78, 1), 0.30, 0.05, True),
    "PanelSteel": ((0.10, 0.17, 0.21, 1), 0.32, 0.70, False),
    "BlankSteel": ((0.36, 0.40, 0.41, 1), 0.28, 0.88, False),
}


def make_material(role, values):
    colour, roughness, metallic, emissive = values
    name = f"M_CA_MW_PTA_{role}_Integration_v001"
    path = f"{MATERIAL_DEST}/{name}"
    asset = library.load_asset(path)
    if resume_own_partial and isinstance(asset, unreal.Material):
        return asset
    asset = asset_tools.create_asset(name, MATERIAL_DEST, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(asset, unreal.Material):
        raise RuntimeError(f"Could not create material: {name}")
    base = mel.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -340, -80)
    base.set_editor_property("constant", unreal.LinearColor(*colour))
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -340, 80)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    metal = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -340, 180)
    metal.set_editor_property("r", metallic)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive:
        mel.connect_material_property(base, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(asset)
    library.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


materials = {role: make_material(role, values) for role, values in PALETTE.items()}


def role_for(slot):
    key = str(slot).lower()
    if "foundation" in key:
        return "Foundation"
    if "inspectionwhite" in key:
        return "InspectionWhite"
    if "blanksteel" in key:
        return "BlankSteel"
    if "panelsteel" in key:
        return "PanelSteel"
    if "yellow" in key:
        return "SafetyYellow"
    if "traina" in key:
        return "TrainABlue"
    if "hydraulic" in key:
        return "HydraulicRed"
    if "pneumatic" in key:
        return "PneumaticBlue"
    if "electrical" in key:
        return "ElectricalOrange"
    if "rubber" in key:
        return "DarkRubber"
    if "ivory" in key:
        return "LabelIvory"
    if "green" in key:
        return "Green"
    if "worked" in key or "steel" in key or "metal" in key:
        return "WorkedSteel"
    return "Charcoal"


material_assignments = []
for index, slot in enumerate(material_slot_names(assembly_mesh)):
    role = role_for(slot)
    assembly_mesh.set_material(index, materials[role])
    material_assignments.append({"index": index, "source_slot": str(slot), "role": role,
                                 "material": materials[role].get_path_name()})

nanite_result = {"requested": True, "enabled": False, "error": None}
try:
    settings = assembly_mesh.get_editor_property("nanite_settings")
    settings.set_editor_property("enabled", True)
    assembly_mesh.set_editor_property("nanite_settings", settings)
    nanite_result["enabled"] = bool(assembly_mesh.get_editor_property("nanite_settings").get_editor_property("enabled"))
except Exception as exc:
    nanite_result["error"] = str(exc)
library.save_loaded_asset(assembly_mesh, only_if_is_dirty=False)

if not levels.new_level(MAP):
    raise RuntimeError(f"Could not create isolated map: {MAP}")

COMMON_TAGS = (
    "LB.PressTrain.TrainA.AssemblyIntegration.v001", "LB.Asset.Candidate.v001",
    "LB.Asset.CandidateNotPromoted", "LB.Authority.WorldPlacement.TBCNotInvented",
    "LB.Scope.IsolatedLocalOrigin", "LB.Runtime.Authority.NotImplemented",
)


def set_tags(actor, *extra):
    actor.tags = [unreal.Name(value) for value in (*COMMON_TAGS, *extra)]


assembly_actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator())
assembly_actor.set_actor_label("CA_MW_PTA_AssemblyStudyIntegration_v001")
set_tags(assembly_actor, "LB.PressTrain.PresentationAggregate", "LB.PressTrain.ProcessDirection.PositiveY")
assembly_actor.static_mesh_component.set_static_mesh(assembly_mesh)
assembly_actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
assembly_actor.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
assembly_actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
for index, row in enumerate(material_assignments):
    assembly_actor.static_mesh_component.set_material(index, materials[row["role"]])

cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
if not isinstance(cube, unreal.StaticMesh):
    raise RuntimeError("Engine cube missing")


def cube_actor(label, location, dimensions_cm, material, collision, hidden, *tags):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    set_tags(actor, *tags)
    actor.static_mesh_component.set_static_mesh(cube)
    actor.set_actor_scale3d(unreal.Vector(*(value / 100.0 for value in dimensions_cm)))
    actor.static_mesh_component.set_material(0, material)
    actor.static_mesh_component.set_collision_enabled(
        unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll" if collision else "NoCollision"))
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", collision)
    actor.set_actor_hidden_in_game(hidden)
    return actor


floor = cube_actor("CA_MW_PTA_IsolationFloor_v001", (0, 2250, -20), (1800, 6500, 40),
                   materials["Foundation"], True, False, "LB.Validation.Environment", "LB.Collision.WalkableFloor")

stage_specs = [
    ("S01", 0, 650, 700, 650), ("S02", 750, 700, 700, 1100),
    ("S03", 1500, 650, 700, 950), ("S04", 2250, 650, 700, 900),
    ("S05", 3000, 650, 700, 850), ("S06", 3750, 650, 700, 900),
    ("S07", 4500, 900, 700, 700),
]
collision_proxies = []
for stage, y, width, length, height in stage_specs:
    proxy = cube_actor(f"CA_MW_PTA_{stage}_SimpleCollision_v001", (0, y, height / 2),
                       (width, length, height), materials["Foundation"], True, True,
                       "LB.Collision.SimpleProxy", f"LB.PressTrain.Stage.{stage}")
    collision_proxies.append(proxy)

nav = actors.spawn_actor_from_class(unreal.NavMeshBoundsVolume, unreal.Vector(0, 2250, 350), unreal.Rotator())
nav.set_actor_label("CA_MW_PTA_IsolationNavBounds_v001")
set_tags(nav, "LB.Navigation.IsolationEvidenceOnly")
nav.set_actor_scale3d(unreal.Vector(18, 65, 7))

sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(), unreal.Rotator())
sky.set_actor_label("CA_MW_PTA_IsolationSky_v001")
set_tags(sky, "LB.Validation.Lighting")
sky.get_editor_property("light_component").set_editor_property("intensity", 0.55)

directional = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(), unreal.Rotator(pitch=-48, yaw=-32))
directional.set_actor_label("CA_MW_PTA_IsolationKey_v001")
set_tags(directional, "LB.Validation.Lighting")
directional.get_editor_property("directional_light_component").set_editor_property("intensity", 4.0)

for index, y in enumerate((-250, 750, 1750, 2750, 3750, 4750), start=1):
    light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(900, y, 1450), unreal.Rotator(pitch=-42, yaw=180))
    light.set_actor_label(f"CA_MW_PTA_IsolationFill_{index:02d}_v001")
    set_tags(light, "LB.Validation.Lighting")
    component = light.get_editor_property("rect_light_component")
    component.set_editor_property("intensity", 3200.0)
    component.set_editor_property("source_width", 900.0)
    component.set_editor_property("source_height", 220.0)
    component.set_light_color(unreal.LinearColor(0.72, 0.82, 0.78, 1.0))

post = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
post.set_actor_label("CA_MW_PTA_IsolationExposure_v001")
set_tags(post, "LB.Validation.Lighting")
post.set_editor_property("unbound", True)
settings = post.get_editor_property("settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True, "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True, "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True, "auto_exposure_bias": 0.15,
})
post.set_editor_property("settings", settings)


def camera(label, location, target, fov, semantic, roll=0.0):
    rotation = unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*location), unreal.Vector(*target))
    rotation.roll = roll
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), rotation)
    actor.set_actor_label(label)
    set_tags(actor, "LB.Camera.Fixed", semantic)
    actor.camera_component.set_editor_property("field_of_view", fov)
    return actor


cameras = [
    camera("CA_MW_PTA_CAM_Hero_v001", (-2900, -2500, 1900), (0, 2250, 390), 48, "LB.Camera.PressTrainA.Hero"),
    camera("CA_MW_PTA_CAM_OperatorSide_v001", (2350, 2250, 820), (0, 2250, 380), 50, "LB.Camera.PressTrainA.OperatorSide"),
    camera("CA_MW_PTA_CAM_Overhead_v001", (0, 2250, 6600), (0, 2250, 0), 46, "LB.Camera.PressTrainA.Overhead", 90),
    camera("CA_MW_PTA_CAM_S01_v001", (1450, -1150, 720), (0, -180, 250), 46, "LB.Camera.PressTrainA.S01"),
    camera("CA_MW_PTA_CAM_S07_v001", (1450, 5750, 720), (0, 4660, 250), 46, "LB.Camera.PressTrainA.S07"),
    camera("CA_MW_PTA_CAM_LoadedCart_v001", (-1650, 1700, 600), (-360, 2200, 155), 48, "LB.Camera.PressTrainA.LoadedCart"),
    camera("CA_MW_PTA_CAM_Mechanics_v001", (1650, 2550, 900), (330, 2550, 260), 50, "LB.Camera.PressTrainA.Mechanics"),
]

identity = actors.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(-780, -480, 120), unreal.Rotator(yaw=90))
identity.set_actor_label("CA_MW_PTA_IsolationAuthorityText_v001")
set_tags(identity, "LB.Brand.CairnwellAutomotive", "LB.Site.MoorcrossWorks", "LB.Validation.NonProductionLabel")
identity.text_render.set_text("CAIRNWELL AUTOMOTIVE | MOORCROSS WORKS\nPRESS TRAIN A | ISOLATED STUDY | TBC_NOT_INVENTED")
identity.text_render.set_world_size(30.0)
identity.text_render.set_text_render_color(unreal.Color(205, 220, 212, 255))
identity.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
identity.text_render.set_editor_property("can_ever_affect_navigation", False)

if not levels.save_current_level():
    raise RuntimeError("Could not save isolated AssemblyStudy integration map")
for path in (DEST,):
    library.save_directory(path, only_if_is_dirty=False, recursive=True)

source_slot_names = material_slot_names(assembly_mesh)
bounds = assembly_mesh.get_bounds()
dims_mm = [round(bounds.box_extent.x * 20, 3), round(bounds.box_extent.y * 20, 3), round(bounds.box_extent.z * 20, 3)]
module_rows = []
for name, mesh in sorted(module_assets.items()):
    b = mesh.get_bounds()
    module_rows.append({
        "asset": mesh.get_path_name(), "source_name": name,
        "dimensions_mm": [round(b.box_extent.x * 20, 3), round(b.box_extent.y * 20, 3), round(b.box_extent.z * 20, 3)],
        "bounds_origin_cm": [round(b.origin.x, 4), round(b.origin.y, 4), round(b.origin.z, 4)],
        "lod_count": mesh.get_num_lods(), "vertices_lod0": mesh.get_num_vertices(0),
        "triangles_lod0": mesh.get_num_triangles(0),
        "material_slots": material_slot_names(mesh),
    })

handoff_reads = []
for relative in ("Docs/PROJECT_HANDOFF.md", "Docs/NEW_CHAT_HANDOVER_2026-08-03.md"):
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    handoff_reads.append({"path": relative, "bytes": path.stat().st_size, "lines": len(text.splitlines()),
                          "sha256": sha(path), "section_count": sum(line.startswith("## ") for line in text.splitlines()),
                          "read_to_eof": True})

report = {
    "$schema": "cairnwell/audit/press-train-a-assembly-integration-build-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FIRST_ISOLATED_ASSEMBLYSTUDY_V001_UNREAL_IMPORT_AND_PRESENTATION_MAP__STATIC_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP, "asset_destination": DEST,
    "source": {"assembly_fbx": str(ASSEMBLY_FBX.relative_to(ROOT)).replace("\\", "/"),
               "sha256": sha(ASSEMBLY_FBX), "manifest": str(MANIFEST_PATH.relative_to(ROOT)).replace("\\", "/"),
               "validation": str(VALIDATION_PATH.relative_to(ROOT)).replace("\\", "/"),
               "review": str(REVIEW_PATH.relative_to(ROOT)).replace("\\", "/")},
    "authority_reads": handoff_reads,
    "aggregate_import": {"asset": assembly_mesh.get_path_name(), "imported_paths": assembly_import_paths,
                         "dimensions_mm": dims_mm, "pivot_policy": "FBX scene origin; transform_vertex_to_absolute=false; bake_pivot_in_vertex=false",
                         "source_material_slots": source_slot_names, "material_assignments": material_assignments,
                         "lod_count": assembly_mesh.get_num_lods(), "vertices_lod0": assembly_mesh.get_num_vertices(0),
                         "triangles_lod0": assembly_mesh.get_num_triangles(0), "nanite": nanite_result},
    "modular_imports": {"count": len(module_rows), "imported_paths": module_import_paths, "assets": module_rows},
    "presentation": {"aggregate_actor": assembly_actor.get_actor_label(), "fixed_camera_count": len(cameras),
                     "simple_collision_proxy_count": len(collision_proxies), "navigation_bounds": nav.get_actor_label(),
                     "lighting": "isolated neutral calibrated evidence rig", "world_placement": "TBC_NOT_INVENTED"},
    "resumed_own_partial_import": resume_own_partial,
    "protected_assets_modified": [], "production_content_modified": False,
    "runtime_machine_authority": False, "animation_implemented": False,
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
