"""Import exact v002 detail source into a fresh isolated Unreal v009 candidate."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v002"
MANIFEST_PATH = SOURCE / "PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_v002.json"
SOURCE_VALIDATION = SOURCE / "PRESS_TRAIN_A_ASSEMBLY_STUDY_VALIDATION_v002.json"
AUTHORED_STAGING = ROOT / "Saved/ImportStaging/PressTrainAAssemblyDetail_v009"
AUTHORED_RECEIPT = ROOT / "Saved/Audits/PressTrains/press_train_a_assembly_detail_staging_v009.json"
DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyDetail_v009"
MODULE_DEST = DEST + "/Modules"
AUTHORED_DEST = DEST + "/Authored"
MATERIAL_DEST = DEST + "/Materials"
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyVisualCandidate_v008"
MAP = "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyDetailCandidate_v009"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_assembly_detail_build_v009.json"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
source_validation = json.loads(SOURCE_VALIDATION.read_text(encoding="utf-8"))
authored_receipt = json.loads(AUTHORED_RECEIPT.read_text(encoding="utf-8"))
if not source_validation.get("status", "").startswith("PASS") or not authored_receipt.get("status", "").startswith("PASS"):
    raise RuntimeError("v002 source validation or v009 staging is not PASS")
if library.does_asset_exist(MAP) or library.does_directory_exist(DEST) or OUT.exists():
    raise RuntimeError("Refusing to overwrite AssemblyStudyDetail v009")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def import_mesh(path, destination, name):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(path), "destination_path": destination, "destination_name": name,
        "automated": True, "replace_existing": False, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False, "import_materials": False,
        "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "transform_vertex_to_absolute": False, "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": True, "auto_generate_collision": False,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    tools.import_asset_tasks([task])
    asset = library.load_asset(f"{destination}/{name}")
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Import failed: {path}")
    return asset


# Duplicate the exact retained shared module assets; import only newly staged
# local-pivot authored geometry. No v005/v008 asset is modified.
module_stems = sorted({Path(row["source_fbx"]).stem for row in manifest["instances"]
                       if not str(row["source_fbx"]).startswith("ASSEMBLY_STUDY")})
module_assets = {}
for stem in module_stems:
    source_asset = f"/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v005/Modules/{stem}"
    target_asset = f"{MODULE_DEST}/{stem}_v009"
    if not library.duplicate_asset(source_asset, target_asset):
        raise RuntimeError(f"Could not duplicate retained module asset: {stem}")
    module_assets[stem] = library.load_asset(target_asset)

authored_assets = {}
for row in authored_receipt["assets"]:
    authored_assets[row["asset"]] = import_mesh(AUTHORED_STAGING / row["file"], AUTHORED_DEST, row["asset"])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

roles = ("Charcoal", "Foundation", "WorkedSteel", "Green", "SafetyYellow", "TrainABlue", "DarkRubber",
         "LabelIvory", "HydraulicRed", "PneumaticBlue", "ElectricalOrange", "InspectionWhite", "PanelSteel", "BlankSteel")
materials = {}
for role in roles:
    source_material = f"/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v005/Materials/M_CA_MW_PTA_{role}_Integration_v005"
    target_material = f"{MATERIAL_DEST}/M_CA_MW_PTA_{role}_Detail_v009"
    if not library.duplicate_asset(source_material, target_material):
        raise RuntimeError(f"Could not duplicate retained material: {role}")
    materials[role] = library.load_asset(target_material)


def slot_names(mesh):
    return [str(row.get_editor_property("material_slot_name")) for row in mesh.get_editor_property("static_materials")]


def role_for(slot):
    key = slot.lower()
    tests = (
        ("foundation", "Foundation"), ("inspectionwhite", "InspectionWhite"),
        ("inspectionglass", "TrainABlue"), ("blanksteel", "BlankSteel"),
        ("panelsteel", "PanelSteel"), ("yellow", "SafetyYellow"),
        ("traina", "TrainABlue"), ("hydraulic", "HydraulicRed"),
        ("pneumatic", "PneumaticBlue"), ("electrical", "ElectricalOrange"),
        ("rubber", "DarkRubber"), ("ivory", "LabelIvory"), ("green", "Green"),
    )
    for token, role in tests:
        if token in key:
            return role
    if "worked" in key or "steel" in key or "metal" in key:
        return "WorkedSteel"
    return "Charcoal"


all_assets = {**module_assets, **authored_assets}
material_rows = []
for name, mesh in all_assets.items():
    for index, slot in enumerate(slot_names(mesh)):
        role = role_for(slot)
        mesh.set_material(index, materials[role])
        material_rows.append({"asset": name, "slot": slot, "role": role})
    library.save_loaded_asset(mesh, only_if_is_dirty=False)

if not levels.new_level_from_template(MAP, SOURCE_MAP):
    raise RuntimeError(f"Could not create v009 from v008 validation environment: {MAP}")


def tags(actor):
    return {str(value) for value in actor.tags}


old_presentation = [actor for actor in actors_api.get_all_level_actors()
                    if isinstance(actor, unreal.StaticMeshActor)
                    and "LB.PressTrain.TrainA.AssemblyIntegration.v005" in tags(actor)
                    and any(value.startswith("LB.PressTrain.Role.") for value in tags(actor))]
if len(old_presentation) != 163:
    raise RuntimeError(f"Expected 163 inherited v005 presentation actors, found {len(old_presentation)}")
actors_api.destroy_actors(old_presentation)

COMMON = (
    "LB.PressTrain.TrainA.AssemblyDetail.v009", "LB.Asset.Candidate.v009",
    "LB.Asset.CandidateNotPromoted", "LB.Authority.WorldPlacement.TBCNotInvented",
    "LB.Scope.IsolatedLocalOrigin", "LB.Runtime.Authority.NotImplemented",
)


def add_tags(actor, *extra):
    values = [str(value) for value in actor.tags]
    for value in (*COMMON, *extra):
        if value not in values:
            values.append(value)
    actor.set_editor_property("tags", [unreal.Name(value) for value in values])


# Retain the validated v008 visual environment, collision proxies and nav-authoring
# witness while clearly marking them as inherited non-production context.
environment_count = 0
for actor in actors_api.get_all_level_actors():
    actor_tags = tags(actor)
    if "LB.PressTrain.TrainA.AssemblyIntegration.v005" in actor_tags:
        add_tags(actor, "LB.Validation.EnvironmentInherited.v008")
        environment_count += 1

authored_map = {row["object"]: row["asset"] for row in authored_receipt["instances"]}
placed = []
for record in manifest["instances"]:
    source_ref = str(record["source_fbx"])
    if source_ref.startswith("ASSEMBLY_STUDY"):
        mesh = authored_assets[authored_map[record["name"]]]
    else:
        mesh = module_assets[Path(source_ref).stem]
    loc = record["location_mm"]
    rot = record["rotation_deg"]
    actor = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(*(value / 10.0 for value in loc)),
        unreal.Rotator(pitch=rot[1], yaw=rot[2], roll=rot[0]),
    )
    actor.set_actor_label(record["name"] + "_UEv009")
    add_tags(actor, f"LB.PressTrain.Stage.{record['stage']}", f"LB.PressTrain.Role.{record['role']}",
             "LB.PressTrain.ProcessDirection.PositiveY")
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(*record["scale"]))
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    for index, slot in enumerate(slot_names(mesh)):
        actor.static_mesh_component.set_material(index, materials[role_for(slot)])
    placed.append(actor)


def one(label):
    matches = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"expected one {label}, found {len(matches)}")
    return matches[0]


def set_camera(old_label, new_label, location, target, fov, roll=0.0):
    camera = one(old_label)
    rotation = unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*location), unreal.Vector(*target))
    rotation.roll = roll
    camera.set_actor_location(unreal.Vector(*location), False, False)
    camera.set_actor_rotation(rotation, False)
    camera.set_actor_label(new_label)
    camera.camera_component.set_editor_property("field_of_view", fov)
    add_tags(camera, "LB.Camera.Fixed.v009")


set_camera("CA_MW_PTA_CAM_Hero_v008", "CA_MW_PTA_CAM_Hero_v009", (-3800, -2500, 2200), (0, 2250, 450), 42)
set_camera("CA_MW_PTA_CAM_OperatorSide_v008", "CA_MW_PTA_CAM_OperatorSide_v009", (3900, 2250, 1450), (0, 2250, 480), 42)
set_camera("CA_MW_PTA_CAM_Overhead_v008", "CA_MW_PTA_CAM_Overhead_v009", (0, 2250, 7200), (0, 2250, 0), 44, 90)
set_camera("CA_MW_PTA_CAM_S01_v008", "CA_MW_PTA_CAM_S01_v009", (-3200, -1750, 1450), (0, -100, 420), 46)
set_camera("CA_MW_PTA_CAM_S07_v008", "CA_MW_PTA_CAM_S07_v009", (-3200, 6250, 1450), (-500, 4650, 420), 46)
set_camera("CA_MW_PTA_CAM_LoadedCart_v008", "CA_MW_PTA_CAM_LoadedCart_v009", (-2850, 1700, 1150), (-400, 2200, 260), 44)
set_camera("CA_MW_PTA_CAM_Mechanics_v008", "CA_MW_PTA_CAM_Mechanics_v009", (3300, 2550, 1650), (250, 2550, 430), 40)

identity = one("CA_MW_PTA_IsolationAuthorityText_v005")
identity.set_actor_label("CA_MW_PTA_IsolationAuthorityText_v009")
identity.text_render.set_text("CAIRNWELL AUTOMOTIVE | MOORCROSS WORKS\nPRESS TRAIN A | DETAIL STUDY v009 | TBC_NOT_INVENTED")
add_tags(identity, "LB.Validation.NonProductionLabel")

if not levels.save_current_level():
    raise RuntimeError("Map save failed")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

minimum = unreal.Vector(1e12, 1e12, 1e12)
maximum = unreal.Vector(-1e12, -1e12, -1e12)
for actor in placed:
    origin, extent = actor.get_actor_bounds(False, False)
    minimum.x = min(minimum.x, origin.x - extent.x); minimum.y = min(minimum.y, origin.y - extent.y); minimum.z = min(minimum.z, origin.z - extent.z)
    maximum.x = max(maximum.x, origin.x + extent.x); maximum.y = max(maximum.y, origin.y + extent.y); maximum.z = max(maximum.z, origin.z + extent.z)
bounds_mm = [round((maximum.x - minimum.x) * 10, 3), round((maximum.y - minimum.y) * 10, 3), round((maximum.z - minimum.z) * 10, 3)]
report = {
    "$schema": "cairnwell/audit/press-train-a-assembly-detail-build-v009/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__EXACT_V002_MANIFEST_RECONSTRUCTION_IN_V008_VALIDATION_ENVIRONMENT__STATIC_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "source_map": SOURCE_MAP,
    "map": MAP,
    "asset_destination": DEST,
    "source_manifest_sha256": sha(MANIFEST_PATH),
    "source_blend_sha256": sha(SOURCE / "CA_MW_PressTrainA_AssemblyStudy_v002.blend"),
    "world_placement": "TBC_NOT_INVENTED",
    "removed_v005_presentation_actor_count": len(old_presentation),
    "placed_manifest_actor_count": len(placed),
    "aggregate_actor_bounds_mm": bounds_mm,
    "module_asset_count": len(module_assets),
    "deduplicated_authored_asset_count": len(authored_assets),
    "material_asset_count": len(materials),
    "material_assignment_count": len(material_rows),
    "inherited_validation_environment_actor_count": environment_count,
    "fixed_camera_count": 7,
    "runtime_machine_authority": False,
    "animation_implemented": False,
    "production_map_changed": False,
    "protected_assets_modified": [],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
