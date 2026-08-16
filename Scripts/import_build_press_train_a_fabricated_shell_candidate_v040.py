"""Import v015 fabricated shell into a fresh collision-safe isolated Train A child."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/PresentationShell_v015/FBX/SM_CA_MW_PTA_PresentationShell_v015.fbx"
SOURCE_MANIFEST = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/PresentationShell_v015/PRESS_TRAIN_A_PRESENTATION_SHELL_MANIFEST_v015.json"
BASE = "/Game/LineBoss/Maps/LB_PressTrainAFabricationCollisionSafeCandidate_v034"
MAP = "/Game/LineBoss/Maps/LB_PressTrainAFabricatedShellCandidate_v040"
DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/FabricatedShell_v040"
ASSET = DEST + "/SM_CA_MW_PTA_PresentationShell_v015"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainAFabricationCollisionSafeCandidate_v034.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainAFabricatedShellCandidate_v040.umap"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_fabricated_shell_build_v040.json"
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest().upper()

manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
if manifest.get("status") != "SOURCE_ONLY_FABRICATED_SHELL__UNREAL_INTAKE_REQUIRED__NOT_PROMOTED":
    raise RuntimeError("unexpected v015 source status")
if lib.does_directory_exist(DEST) or lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite v040")
base_hash = sha(BASE_FILE)
task = unreal.AssetImportTask(); task.set_editor_properties({"filename": str(SOURCE), "destination_path": DEST, "destination_name": "SM_CA_MW_PTA_PresentationShell_v015", "automated": True, "replace_existing": False, "save": True})
options = unreal.FbxImportUI(); options.set_editor_properties({"import_mesh": True, "import_as_skeletal": False, "import_materials": True, "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH})
data = options.get_editor_property("static_mesh_import_data"); data.set_editor_properties({"combine_meshes": True, "convert_scene": True, "convert_scene_unit": True, "transform_vertex_to_absolute": False, "bake_pivot_in_vertex": False, "generate_lightmap_u_vs": True, "auto_generate_collision": False, "remove_degenerates": True})
task.set_editor_property("options", options)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]); unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh = lib.load_asset(ASSET)
if not isinstance(mesh, unreal.StaticMesh): raise RuntimeError("v015 shell import missing")
if not levels.new_level_from_template(MAP, BASE): raise RuntimeError("fresh v034 child failed")
actor = api.spawn_actor_from_object(mesh, unreal.Vector(), unreal.Rotator(), False)
actor.set_actor_label("CA_MW_PTA_FabricatedShell_v015_FIXED")
actor.set_actor_scale3d(unreal.Vector(100, -100, 100))
actor.tags = [unreal.Name(x) for x in ("LB.PressTrain.PresentationShell.v015", "LB.PressTrain.TrainA", "LB.Asset.Candidate.v040", "LB.Asset.CandidateNotPromoted", "LB.Collision.NoCollision")]
component = actor.static_mesh_component; component.set_collision_profile_name(unreal.Name("NoCollision"), True); component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); component.set_editor_property("generate_overlap_events", False); component.set_editor_property("can_ever_affect_navigation", False); component.set_editor_property("cast_shadow", True)
all_actors = api.get_all_level_actors()
train = [a for a in all_actors if isinstance(a, unreal.StaticMeshActor) and "LB.PressTrain.ProcessDirection.PositiveY" in {str(t) for t in a.tags}]
stations = [a for a in all_actors if a.get_class().get_name() == "LBPressTrainAStation"]
origin, extent = actor.get_actor_bounds(False, False)
bounds = {"origin_cm": [origin.x, origin.y, origin.z], "extent_cm": [extent.x, extent.y, extent.z], "size_cm": [extent.x * 2, extent.y * 2, extent.z * 2]}
failures = []
if len(train) != 336: failures.append(f"retained train actors {len(train)} != 336")
if len(stations) != 1: failures.append(f"native station count {len(stations)} != 1")
if not (90 <= bounds["size_cm"][0] <= 100 and 3550 <= bounds["size_cm"][1] <= 3650 and 1030 <= bounds["size_cm"][2] <= 1045): failures.append(f"unexpected scaled bounds {bounds['size_cm']}")
if str(component.get_collision_profile_name()) != "NoCollision" or component.get_editor_property("can_ever_affect_navigation"): failures.append("collision/navigation contract invalid")
if len(mesh.get_editor_property("static_materials")) != 5: failures.append(f"material slots {len(mesh.get_editor_property('static_materials'))} != 5")
if not levels.save_current_level(): failures.append("save failed")
if sha(BASE_FILE) != base_hash: failures.append("protected v034 changed")
payload = {"$schema": "cairnwell/audit/press-train-a-fabricated-shell-build-v040/v1", "generated_utc": datetime.now(timezone.utc).isoformat(), "status": "PASS__V015_FABRICATED_SHELL_ISOLATED_INTAKE__MATERIAL_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V040_NOT_A_PARENT", "base": BASE, "map": MAP, "base_sha256": base_hash, "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None, "source_fbx_sha256": sha(SOURCE), "shell_asset": ASSET, "actor_scale": [100, -100, 100], "shell_world_bounds": bounds, "shell_material_slots": [str(x.material_slot_name) for x in mesh.get_editor_property("static_materials")], "shell_collision": "NoCollision", "shell_affects_navigation": False, "retained_train_actor_count": len(train), "native_station_count": len(stations), "promotion_authorized": False, "failures": failures}
OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8"); print(json.dumps(payload, indent=2))
if failures: raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
