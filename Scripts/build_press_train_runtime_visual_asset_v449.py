"""Bake the accepted v438 aggregate material overrides into a reusable runtime visual mesh."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
MAP_SHA = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
SOURCE = "/Game/LineBoss/Candidates/PressTrains/TrainA/ProDetailVisual_v354/SM_CA_MW_PressTrainA_ProDetailUnrealAggregate_v049"
DEST_DIR = "/Game/LineBoss/PressTrains/RuntimeVisual_v449"
DEST_NAME = "SM_CA_MW_PressTrain_CompleteRuntimeVisual_v449"
DEST = f"{DEST_DIR}/{DEST_NAME}"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_complete_runtime_visual_build_v449.json"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


lib = unreal.EditorAssetLibrary
if sha(MAP_FILE) != MAP_SHA:
    raise RuntimeError("v438 hash drift")
if lib.does_asset_exist(DEST) or OUT.exists():
    raise RuntimeError("refusing to overwrite v449")
unreal.EditorLoadingAndSavingUtils.load_map(MAP)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
instances = []
for actor in api.get_all_level_actors():
    if isinstance(actor, unreal.StaticMeshActor):
        mesh = actor.static_mesh_component.static_mesh
        if mesh and mesh.get_path_name().split(".", 1)[0] == SOURCE:
            instances.append(actor)
if len(instances) != 4:
    raise RuntimeError(f"expected four accepted aggregate instances, found {len(instances)}")
source_actor = next((a for a in instances if "TrainA" in a.get_actor_label() or "PTA" in a.get_actor_label()), instances[0])
source_comp = source_actor.static_mesh_component
source_mesh = source_comp.static_mesh
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
runtime_mesh = asset_tools.duplicate_asset(DEST_NAME, DEST_DIR, source_mesh)
if not isinstance(runtime_mesh, unreal.StaticMesh):
    raise RuntimeError("runtime visual mesh duplication failed")
materials = []
for index in range(source_comp.get_num_materials()):
    material = source_comp.get_material(index)
    if not material:
        raise RuntimeError(f"accepted visual has empty material slot {index}")
    runtime_mesh.set_material(index, material)
    materials.append(material.get_path_name())
runtime_mesh.set_editor_property("customized_collision", False)
lib.save_loaded_asset(runtime_mesh, False)
runtime_file = ROOT / "Content/LineBoss/PressTrains/RuntimeVisual_v449" / f"{DEST_NAME}.uasset"
if not runtime_file.exists():
    raise RuntimeError("runtime visual asset file missing after save")

payload = {
    "$schema": "cairnwell/audit/press-train-complete-runtime-visual-build-v449/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ACCEPTED_V438_MATERIAL_OVERRIDES_BAKED_TO_REUSABLE_RUNTIME_VISUAL__NOT_PROMOTED",
    "source_map": MAP,
    "source_map_sha256": sha(MAP_FILE),
    "source_mesh": SOURCE,
    "runtime_mesh": DEST,
    "runtime_mesh_sha256": sha(runtime_file),
    "material_slot_count": len(materials),
    "materials": materials,
    "required_component_policy": "NoCollision; navigation-neutral; scale 100; local location X=9.25 Y=2367.5 Z=0 relative to train authority",
    "source_map_saved": False,
    "promotion_authorized": False
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in payload.items() if k != "materials"}, indent=2))
unreal.SystemLibrary.quit_editor()
