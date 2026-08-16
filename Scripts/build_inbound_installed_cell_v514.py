"""Import and review the purpose-built inbound installed crane; never modifies v438."""
from pathlib import Path
import hashlib
import json
import unreal

PROJECT = Path(unreal.Paths.project_dir())
SOURCE = PROJECT / "SourceAssets/IndustrialKit/BridgeCrane/InboundInstalledCrane/Candidate_v001/FBX"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/InboundInstalledCrane/Candidate_v001"
MAP = "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v514"
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_installed_crane_import_v514.json"
STATIC_NAME = "SM_CA_MW_InboundCrane_StaticRunwayFrame_v001"
MOVING_NAME = "SM_CA_MW_InboundCrane_MovingBridge_v001"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def import_static(name):
    fbx = SOURCE / f"{name}.fbx"
    if not fbx.is_file():
        raise RuntimeError(f"Missing source FBX: {fbx}")
    path = f"{DEST}/{name}"
    if library.does_asset_exist(path):
        raise RuntimeError(f"Fresh intake path already exists: {path}")
    task = unreal.AssetImportTask()
    task.set_editor_properties({"filename":str(fbx), "destination_path":DEST,
        "destination_name":name, "automated":True, "replace_existing":False,
        "replace_existing_settings":False, "save":True})
    ui = unreal.FbxImportUI()
    ui.set_editor_properties({"import_mesh":True, "import_as_skeletal":False,
        "import_materials":True, "import_textures":False,
        "mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type":False})
    ui.static_mesh_import_data.set_editor_properties({"combine_meshes":True,
        "convert_scene":True, "convert_scene_unit":True, "force_front_x_axis":False,
        "generate_lightmap_u_vs":True, "auto_generate_collision":True,
        "remove_degenerates":True})
    task.options = ui
    asset_tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    mesh = library.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Import failed for {path}: {task.imported_object_paths}")
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    size = mesh.get_bounds().box_extent * 2.0
    return mesh, {"asset":path, "source":str(fbx), "sha256":digest(fbx),
        "bounds_cm":[round(size.x,2),round(size.y,2),round(size.z,2)],
        "material_slots":len(mesh.get_editor_property("static_materials")),
        "body_setup":mesh.get_editor_property("body_setup") is not None}

static_mesh, static_record = import_static(STATIC_NAME)
moving_mesh, moving_record = import_static(MOVING_NAME)

# Broad visual-scale gates only: every engineering dimension remains TBC.
sx, sy, sz = static_record["bounds_cm"]
mx, my, mz = moving_record["bounds_cm"]
failures = []
if not (800 <= max(sx, sy) <= 1500 and 800 <= min(sx, sy) <= 1000 and 700 <= sz <= 800):
    failures.append(f"static runway bounds unexpected {static_record['bounds_cm']}")
if not (800 <= max(mx, my) <= 900 and 150 <= min(mx, my) <= 300 and 120 <= mz <= 220):
    failures.append(f"moving bridge bounds unexpected {moving_record['bounds_cm']}")
if failures:
    raise RuntimeError("; ".join(failures))

# Rebuild the proven v512 layout under a fresh v514 map name.
base_source = (PROJECT / "Scripts/build_inbound_installed_cell_v512.py").read_text(encoding="utf-8")
base_source = base_source.replace("InstalledCell_v512", "InstalledCell_v514")
base_source = base_source.replace("LB_INBOUND_V012_", "LB_INBOUND_V014_")
base_source = base_source.replace("V512", "V514")
exec(compile(base_source, str(PROJECT / "Scripts/build_inbound_installed_cell_v512.py"), "exec"), globals(), globals())

# Remove only the superseded schematic structure and girder. Retain the accepted
# trolley, hoist, powered C-hook and process equipment, then align those modules.
for actor in list(actors.get_all_level_actors()):
    label = actor.get_actor_label()
    if label.endswith("CraneBayStructure") or label.endswith("CraneGirder"):
        actors.destroy_actor(actor)
    elif label.endswith("CraneTrolley"):
        actor.set_actor_location(unreal.Vector(0,740,715), False, False)
    elif label.endswith("HoistBlock"):
        actor.set_actor_location(unreal.Vector(0,740,500), False, False)
    elif label.endswith("PoweredCHook"):
        actor.set_actor_location(unreal.Vector(0,740,315), False, False)

def spawn(label, mesh, location):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    actor.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll"))
    actor.tags = [unreal.Name("LB.Asset.Candidate.InboundInstalledCrane.v001"),
        unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Engineering.Values.TBC")]
    return actor

spawn("LB_INBOUND_V014_StaticRunwayFrame", static_mesh, (0,740,0))
spawn("LB_INBOUND_V014_MovingBridge", moving_mesh, (0,740,652))

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving isolated v514 installed cell")
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({"status":"UNREAL_INTAKE_PASS__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED",
    "map":MAP, "records":[static_record,moving_record], "failures":failures,
    "retained_authority":"/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438",
    "authority_modified":False, "engineering_values":"TBC", "promotion_authorized":False}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_INSTALLED_CELL_V514_BUILD_PASS")
