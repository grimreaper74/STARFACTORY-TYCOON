"""Import the untouched approved S03 Walker GLB as a non-Nanite comparison asset."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import unreal

root = Path(unreal.Paths.project_dir()).resolve()
protected = root / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
expected = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
source = root / "SourceAssets/Candidate/PressTrains/Shared/UserApprovedS03Walker_v20260809_v001/HighResolutionRuntime_v957/Cairnwell_S03_Walker_HighResolution_v957.glb"
destination = "/Game/LineBoss/Developer/Validation/BlenderApproved_v957/S03WalkerHighResolution"
output = root / "Saved/Audits/PressTrains/s03_walker_highres_import_v957.json"
library = unreal.EditorAssetLibrary

def protected_hash():
    return hashlib.sha256(protected.read_bytes()).hexdigest().upper()

if protected_hash() != expected:
    raise RuntimeError("protected v438 mismatch before import")
if not source.is_file():
    raise RuntimeError(str(source))
if library.does_directory_exist(destination):
    raise RuntimeError("refusing to overwrite v957")

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(source),
    "destination_path": destination,
    "automated": True,
    "replace_existing": False,
    "replace_existing_settings": False,
    "save": True,
})
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

assets = library.list_assets(destination, recursive=True, include_folder=False)
meshes = []
textures = []
materials = []
for path in assets:
    asset = unreal.load_asset(path)
    if isinstance(asset, unreal.StaticMesh):
        asset.set_editor_property("nanite_settings", unreal.MeshNaniteSettings(enabled=False))
        library.save_loaded_asset(asset, only_if_is_dirty=False)
        meshes.append(path)
    elif isinstance(asset, unreal.Texture2D):
        textures.append(path)
    elif isinstance(asset, (unreal.Material, unreal.MaterialInstance, unreal.MaterialInstanceConstant)):
        materials.append(path)
if len(meshes) != 1 or len(textures) < 3 or len(materials) < 1:
    raise RuntimeError(f"unexpected import meshes={len(meshes)} textures={len(textures)} materials={len(materials)}")
mesh = unreal.load_asset(meshes[0])
box = mesh.get_bounding_box()
size = box.max - box.min
if protected_hash() != expected:
    raise RuntimeError("protected v438 changed")
payload = {
    "revision": "v957",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__UNTOUCHED_APPROVED_HIGH_RES_PRESS__NANITE_DISABLED__ISOLATED_VALIDATION_ONLY",
    "source": str(source),
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest().upper(),
    "destination": destination,
    "static_mesh": meshes[0],
    "materials": materials,
    "textures": textures,
    "bounds_cm": [size.x, size.y, size.z],
    "nanite": False,
    "source_polygon_count_blender": 1986042,
    "meshy_credits_used_by_codex": 0,
    "protected_sha256": protected_hash(),
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_S03_WALKER_HIGHRES_V957_PASS")
