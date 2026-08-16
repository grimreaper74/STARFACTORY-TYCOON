"""Isolated Unreal visual intake of retained v046, preserving v343 authority/collision."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ProDetailModular_v046/FBX/SM_CA_MW_PressTrainA_ProDetailModular_v046.fbx"
SOURCE_SHA = "6482C68BB53068570B2BE46248B5DAB6F227ABA97F983A3C2888D797E5A28106"
DECISION = ROOT / "Saved/Audits/PressTrains/press_train_a_pro_detail_source_decision_v048.json"
BASE = "/Game/LineBoss/Maps/LB_PressShop_TrainAReleaseIntegrationCandidate_v343"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAReleaseIntegrationCandidate_v343.umap"
BASE_SHA = "7CE2F5B7D627776B4B71C8197255B035A0561B9E49DEED20A354ABFFB7560317"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAProDetailVisualCandidate_v351"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAProDetailVisualCandidate_v351.umap"
DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/ProDetailVisual_v351"
ASSET = DEST + "/SM_CA_MW_PressTrainA_ProDetailModular_v046"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_pro_detail_visual_intake_build_v351.json"

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
decision = json.loads(DECISION.read_text(encoding="utf-8"))
if decision.get("isolated_unreal_visual_intake_authorized") is not True:
    raise RuntimeError("v048 does not authorize isolated visual intake")
for key in ("replacement_authorized", "runtime_authority_authorized", "collision_authorized", "navigation_authorized", "promotion_authorized"):
    if decision.get(key) is not False:
        raise RuntimeError(f"v048 authority contract invalid: {key}")
if sha(SOURCE) != SOURCE_SHA or sha(BASE_FILE) != BASE_SHA:
    raise RuntimeError("protected source or base hash drift")
if lib.does_directory_exist(DEST) or lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite v351")

task = unreal.AssetImportTask()
task.set_editor_properties({"filename": str(SOURCE), "destination_path": DEST,
    "destination_name": "SM_CA_MW_PressTrainA_ProDetailModular_v046", "automated": True,
    "replace_existing": False, "save": True})
options = unreal.FbxImportUI()
options.set_editor_properties({"import_mesh": True, "import_as_skeletal": False,
    "import_materials": True, "import_textures": False,
    "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH})
data = options.get_editor_property("static_mesh_import_data")
data.set_editor_properties({"combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
    "transform_vertex_to_absolute": False, "bake_pivot_in_vertex": False,
    "generate_lightmap_u_vs": True, "auto_generate_collision": False,
    "remove_degenerates": True})
task.set_editor_property("options", options)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh = lib.load_asset(ASSET)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("v046 combined visual mesh missing after import")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh v343 child failed")

native_authorities = []
native_collision_components = 0
old_visuals_hidden = []
for actor in actors_api.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    if actor.get_class().get_name() == "LBPressTrainAStation" and "LB.PressTrain.Installed.TRAIN_A" in tags:
        native_authorities.append(actor)
    if "LB.NativeCollision.PreservedHidden" in tags or "LB.PressTrain.Installed.TRAIN_A" in tags:
        for component in actor.get_components_by_class(unreal.PrimitiveComponent):
            if component.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION:
                native_collision_components += 1
    if "LB.PressTrain.TrainA.ReadableLabelsSource.v040" in tags:
        actor.set_actor_hidden_in_game(True)
        for component in actor.get_components_by_class(unreal.PrimitiveComponent):
            component.set_visibility(False, True)
            component.set_hidden_in_game(True, True)
        old_visuals_hidden.append(actor)

candidate = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator(0, -90, 0))
candidate.static_mesh_component.set_static_mesh(mesh)
candidate.set_actor_label("CA_MW_PTA_v046_PRO_DETAIL_VISUAL_ONLY_v351")
candidate.set_actor_scale3d(unreal.Vector(100, 100, 100))
comp = candidate.static_mesh_component
comp.set_collision_profile_name("NoCollision")
comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
comp.set_editor_property("generate_overlap_events", False)
comp.set_editor_property("can_ever_affect_navigation", False)
candidate.tags = [unreal.Name(value) for value in (
    "LB.PressTrain.TrainA.ProDetailSource.v046", "LB.Asset.Candidate.v351",
    "LB.Asset.CandidateNotPromoted", "LB.NativeAuthority.Preserved",
    "LB.NativeCollision.PreservedHidden", "LB.Collision.NoCollision.VisualOnly",
    "LB.Navigation.None", "LB.RuntimeAuthority.None", "LB.EngineeringValues.TBC")]
origin, extent = candidate.get_actor_bounds(False)
candidate.add_actor_world_offset(unreal.Vector(3850 - origin.x, -4300 - origin.y, -(origin.z - extent.z)), False, False)
origin, extent = candidate.get_actor_bounds(False)
size = [extent.x * 2, extent.y * 2, extent.z * 2]
floor_z = origin.z - extent.z
failures = []
if len(native_authorities) != 1: failures.append(f"native authority count {len(native_authorities)}")
if len(old_visuals_hidden) != 1: failures.append(f"v040 visual count {len(old_visuals_hidden)}")
if native_collision_components < 120: failures.append(f"native collision components {native_collision_components}")
if not (5650 <= size[0] <= 5900): failures.append(f"length {size[0]:.2f}")
if not (1250 <= size[1] <= 1500): failures.append(f"width {size[1]:.2f}")
if not (900 <= size[2] <= 1030): failures.append(f"height {size[2]:.2f}")
if abs(floor_z) > 1.0: failures.append(f"floor {floor_z:.3f}")
if str(comp.get_collision_profile_name()) != "NoCollision" or comp.get_editor_property("can_ever_affect_navigation"):
    failures.append("visual physical policy invalid")
if failures:
    raise RuntimeError("v351 hard gate failed: " + "; ".join(failures))
if not levels.save_current_level():
    raise RuntimeError("v351 save failed")
payload = {"$schema": "cairnwell/audit/press-train-a-pro-detail-visual-intake-v351/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_V046_PRO_DETAIL_VISUAL_INTAKE__FRESH_UNREAL_VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "base": BASE, "base_sha256": BASE_SHA, "map": MAP, "map_sha256": sha(MAP_FILE),
    "source_fbx_sha256": SOURCE_SHA, "asset": ASSET,
    "candidate_bounds_origin_cm": list(origin.to_tuple()), "candidate_world_size_cm": size,
    "candidate_floor_z_cm": floor_z, "native_authority_count": len(native_authorities),
    "native_collision_components_preserved": native_collision_components,
    "hidden_prior_v040_visual_count": len(old_visuals_hidden), "collision": "NoCollision",
    "affects_navigation": False, "runtime_authority": "None", "replacement_authorized": False,
    "promotion_authorized": False, "failures": failures}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
