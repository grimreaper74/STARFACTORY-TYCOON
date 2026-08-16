"""Import source-only v013 Train A fabrication meshes into a new UE directory.

This is an isolated, non-overwriting import receipt.  No level is created or
modified here; the imported asset set must prove its naming/count contract
before a fresh runtime-map child may consume it.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_DIR = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v013"
FBX = SOURCE_DIR / "FBX/SM_CA_MW_PTA_SevenStageAssemblyStudy_v013.fbx"
MANIFEST = SOURCE_DIR / "PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_v013.json"
VALIDATION = SOURCE_DIR / "PRESS_TRAIN_A_ASSEMBLY_STUDY_VALIDATION_v013.json"
DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/Fabrication_v030/Imported"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_fabrication_import_v030.json"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


source_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
source_validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
if source_validation.get("status") != "PASS__V013_SOURCE_GEOMETRY_AND_PBR_REFINEMENT__UNREAL_INTEGRATION_REQUIRED__NOT_PROMOTED":
    raise RuntimeError("v013 source validation is not the expected PASS receipt")
if library.does_directory_exist(DEST) or OUT.exists():
    raise RuntimeError("refusing to overwrite v030 fabrication import")

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(FBX),
    "destination_path": DEST,
    "automated": True,
    "replace_existing": False,
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
    "combine_meshes": False,
    "convert_scene": True,
    "convert_scene_unit": True,
    "transform_vertex_to_absolute": False,
    "bake_pivot_in_vertex": False,
    "generate_lightmap_u_vs": True,
    "auto_generate_collision": False,
    "remove_degenerates": True,
})
task.set_editor_property("options", options)
asset_tools.import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

paths = sorted(str(value) for value in task.get_editor_property("imported_object_paths"))
assets = []
for path in paths:
    asset = library.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        continue
    bounds = asset.get_bounds()
    extent = bounds.box_extent
    slots = [
        str(row.get_editor_property("material_slot_name"))
        for row in asset.get_editor_property("static_materials")
    ]
    assets.append({
        "path": asset.get_path_name(),
        "name": asset.get_name(),
        "bounds_size_cm": [
            round(float(extent.x) * 2.0, 4),
            round(float(extent.y) * 2.0, 4),
            round(float(extent.z) * 2.0, 4),
        ],
        "material_slots": slots,
    })

expected_names = {str(row["name"]) for row in source_manifest["instances"]}
actual_names = {row["name"] for row in assets}
missing = sorted(expected_names - actual_names)
unexpected = sorted(actual_names - expected_names)
failures = []
if len(expected_names) != 336:
    failures.append(f"source manifest unique-name count is {len(expected_names)}, expected 336")
if len(assets) != 336:
    failures.append(f"imported static-mesh count is {len(assets)}, expected 336")
if missing:
    failures.append(f"missing source object assets: {missing[:12]}")
if unexpected:
    failures.append(f"unexpected imported assets: {unexpected[:12]}")

payload = {
    "$schema": "cairnwell/audit/press-train-a-fabrication-import-v030/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V013_336_OBJECT_IMPORT_CONTRACT__MAP_INTEGRATION_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__IMPORT_EVIDENCE_ONLY__NOT_A_PARENT",
    "source_fbx": str(FBX.relative_to(ROOT)).replace("\\", "/"),
    "source_fbx_sha256": sha256(FBX),
    "source_manifest_sha256": sha256(MANIFEST),
    "destination": DEST,
    "expected_object_count": 336,
    "imported_static_mesh_count": len(assets),
    "missing_names": missing,
    "unexpected_names": unexpected,
    "assets": assets,
    "map_created_or_modified": False,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({key: payload[key] for key in (
    "status", "destination", "imported_static_mesh_count", "missing_names", "unexpected_names", "failures"
)}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_PRESS_TRAIN_A_FABRICATION_IMPORT_V030_PASS")
unreal.SystemLibrary.quit_editor()
