"""Native Unreal import of the verified coil-free Meshy press candidate."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
FBX = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "HeroPressCell_MeshyNoCoil_v001" / "Runtime" / "SM_LB_PS_HeroPressCell_MeshyNoCoil_v001.fbx"
DESTINATION = "/Game/LineBoss/Candidates/PressShop/HeroPressCellNoCoil_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "hero_press_cell_nocoil_v001_native_import.json"


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


if not FBX.is_file() or not PROTECTED.is_file() or not V002.is_file():
    raise RuntimeError("Required source or protected evidence file missing")
if unreal.EditorAssetLibrary.list_assets(DESTINATION, recursive=True, include_folder=False):
    raise RuntimeError("Refusing to overwrite existing native import candidate")
fbx_before, protected_before, v002_before = digest(FBX), digest(PROTECTED), digest(V002)
options = unreal.FbxImportUI()
options.set_editor_property("import_mesh", True)
options.set_editor_property("import_as_skeletal", False)
options.set_editor_property("automated_import_should_detect_type", False)
static_data = options.get_editor_property("static_mesh_import_data")
static_data.set_editor_property("combine_meshes", False)
static_data.set_editor_property("generate_lightmap_u_vs", True)
static_data.set_editor_property("auto_generate_collision", False)
task = unreal.AssetImportTask()
task.set_editor_property("filename", str(FBX))
task.set_editor_property("destination_path", DESTINATION)
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", False)
task.set_editor_property("save", True)
task.set_editor_property("options", options)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
imported = list(task.get_editor_property("imported_object_paths"))
meshes = []
for path in imported:
    asset = unreal.load_asset(path)
    if isinstance(asset, unreal.StaticMesh):
        meshes.append(asset)
if len(meshes) != 2:
    raise RuntimeError("Expected native body and rollers static meshes, found %d" % len(meshes))
for mesh in meshes:
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
fbx_after, protected_after, v002_after = digest(FBX), digest(PROTECTED), digest(V002)
if fbx_before != fbx_after or protected_before != protected_after or v002_before != v002_after:
    raise RuntimeError("Source asset or protected map changed during native import")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__NATIVE_UNREAL_IMPORT_CANDIDATE_ONLY",
    "fbx": str(FBX),
    "fbx_sha256_before": fbx_before,
    "fbx_sha256_after": fbx_after,
    "destination": DESTINATION,
    "imported_objects": imported,
    "static_meshes": [{"path": mesh.get_path_name(), "materials": mesh.get_static_materials().__len__()} for mesh in meshes],
    "collision": "not auto-generated; candidate needs explicit collision decision",
    "v002_sha256_before": v002_before,
    "v002_sha256_after": v002_after,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_HERO_NOCOIL_V001_NATIVE_IMPORT_PASS")
