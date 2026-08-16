"""Import and exact-audit the PR005 service-logistics Unreal derivative."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Candidate/PressShop/PR005/ServiceLogistics_UnrealDerived_v007"
MANIFEST_PATH = SOURCE / "PR005_SERVICE_LOGISTICS_UNREAL_DERIVED_MANIFEST_v007.json"
DEST = "/Game/LineBoss/Candidates/PressShop/PR005/ServiceLogistics_v007/Meshes"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr005_service_logistics_unreal_intake_v007.json"
library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
fbx = SOURCE / manifest["fbx"]
asset_path = f"{DEST}/{manifest['asset_name']}"
failures = []
source_hash_before = sha256(fbx)
if source_hash_before != manifest["sha256"]:
    failures.append("derived source hash mismatch")
if library.does_asset_exist(asset_path):
    failures.append(f"refusing to overwrite existing asset {asset_path}")
if failures:
    raise RuntimeError("; ".join(failures))

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(fbx), "destination_path": DEST, "destination_name": manifest["asset_name"],
    "automated": True, "replace_existing": False, "replace_existing_settings": False, "save": True,
})
options = unreal.FbxImportUI()
options.set_editor_properties({
    "import_mesh": True, "import_as_skeletal": False, "import_materials": False,
    "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
})
data = options.get_editor_property("static_mesh_import_data")
data.set_editor_properties({
    "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
    "force_front_x_axis": False, "transform_vertex_to_absolute": False,
    "bake_pivot_in_vertex": False, "generate_lightmap_u_vs": True,
    "auto_generate_collision": False, "remove_degenerates": True, "import_uniform_scale": 1.0,
})
task.options = options
asset_tools.import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh = library.load_asset(asset_path)
measured = {}
if not isinstance(mesh, unreal.StaticMesh):
    failures.append("imported static mesh missing")
else:
    box = mesh.get_bounding_box()
    measured_min = [box.min.x, box.min.y, box.min.z]
    measured_max = [box.max.x, box.max.y, box.max.z]
    measured_dims_mm = [(measured_max[i] - measured_min[i]) * 10.0 for i in range(3)]
    source_min = [float(v) / 10.0 for v in manifest["expected_bounds_min_mm"]]
    source_max = [float(v) / 10.0 for v in manifest["expected_bounds_max_mm"]]
    expected_min = [source_min[0], -source_max[1], source_min[2]]
    expected_max = [source_max[0], -source_min[1], source_max[2]]
    deltas_mm = [(measured_min[i] - expected_min[i]) * 10.0 for i in range(3)] + [
        (measured_max[i] - expected_max[i]) * 10.0 for i in range(3)]
    if max(abs(value) for value in deltas_mm) > 2.0:
        failures.append(f"dimension/handedness drift mm={deltas_mm}")
    slots = [str(slot.material_slot_name) for slot in mesh.get_editor_property("static_materials")]
    missing = sorted(set(manifest["material_slots"]) - set(slots))
    if missing:
        failures.append(f"missing material slots {missing}")
    measured = {
        "local_min_cm": [round(v, 4) for v in measured_min],
        "local_max_cm": [round(v, 4) for v in measured_max],
        "dimensions_mm": [round(v, 3) for v in measured_dims_mm],
        "delta_mm": [round(v, 3) for v in deltas_mm],
        "material_slots": slots,
    }
    library.save_loaded_asset(mesh, only_if_is_dirty=False)

source_hash_after = sha256(fbx)
if source_hash_after != source_hash_before:
    failures.append("derived source changed during import")
report = {
    "$schema": "cairnwell/audit/press-shop-pr005-service-logistics-unreal-intake-v007/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__EXACT_DIMENSIONS_HANDEDNESS_PIVOT_AND_MATERIAL_SLOTS__INTEGRATION_HOLD_NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
    "source_sha256_before": source_hash_before, "source_sha256_after": source_hash_after,
    "asset": asset_path, "tolerance_mm": 2.0, "measured": measured,
    "replacement_scope": "SIX_V053_STATIC_LOGISTICS_BLOCKOUT_ACTORS_ONLY",
    "runtime_authority": "UNCHANGED_PR005_STATION_AND_MATERIAL_FLOW",
    "promotion_authorized": False, "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_PR005_SERVICE_LOGISTICS_V007_INTAKE_PASS")
unreal.SystemLibrary.quit_editor()
