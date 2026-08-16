"""Import and dimension-audit retained PR-005 source Candidate_v002 in isolation.

This creates content assets only under a new candidate folder. It does not
place them in v053, replace runtime movers, or claim world placement.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Candidate/PressShop/PR005/Candidate_v002"
MANIFEST_PATH = SOURCE / "PR005_EXTERIOR_ENCLOSURE_MANIFEST_v002.json"
DEST = "/Game/LineBoss/Candidates/PressShop/PR005/ExteriorEnclosure_v002/Meshes"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr005_exterior_enclosure_unreal_intake_v002.json"
library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
source_hashes_before = {row["fbx"]: sha256(SOURCE / row["fbx"]) for row in manifest["assets"]}
failures = []
for row in manifest["assets"]:
    if source_hashes_before[row["fbx"]] != row["sha256"]:
        failures.append(f"source hash mismatch {row['asset_name']}")
    asset_path = f"{DEST}/{row['asset_name']}"
    if library.does_asset_exist(asset_path):
        failures.append(f"refusing to overwrite existing asset {asset_path}")
if failures:
    raise RuntimeError("; ".join(failures))

tasks = []
for row in manifest["assets"]:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE / row["fbx"]),
        "destination_path": DEST,
        "destination_name": row["asset_name"],
        "automated": True,
        "replace_existing": False,
        "replace_existing_settings": False,
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
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": False,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": False,
        "remove_degenerates": True,
        "import_uniform_scale": 1.0,
    })
    task.options = options
    tasks.append(task)

asset_tools.import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

results = []
for row in manifest["assets"]:
    asset_path = f"{DEST}/{row['asset_name']}"
    mesh = library.load_asset(asset_path)
    if not isinstance(mesh, unreal.StaticMesh):
        failures.append(f"missing imported static mesh {row['asset_name']}")
        continue
    box = mesh.get_bounding_box()
    measured_min_cm = [box.min.x, box.min.y, box.min.z]
    measured_max_cm = [box.max.x, box.max.y, box.max.z]
    measured_dims_mm = [
        (box.max.x - box.min.x) * 10.0,
        (box.max.y - box.min.y) * 10.0,
        (box.max.z - box.min.z) * 10.0,
    ]
    expected_dims_mm = [float(v) for v in row["dimensions_mm"]]
    dim_delta_mm = [measured_dims_mm[i] - expected_dims_mm[i] for i in range(3)]
    pivot_mm = [float(v) * 1000.0 for v in row["pivot_m"]]
    expected_local_min_cm = [(float(row["bounds_min_mm"][i]) - pivot_mm[i]) / 10.0 for i in range(3)]
    expected_local_max_cm = [(float(row["bounds_max_mm"][i]) - pivot_mm[i]) / 10.0 for i in range(3)]
    local_bound_delta_mm = [
        (measured_min_cm[i] - expected_local_min_cm[i]) * 10.0 for i in range(3)
    ] + [
        (measured_max_cm[i] - expected_local_max_cm[i]) * 10.0 for i in range(3)
    ]
    material_slots = [str(slot.material_slot_name) for slot in mesh.get_editor_property("static_materials")]
    passed = max(abs(v) for v in dim_delta_mm + local_bound_delta_mm) <= 2.0
    if not passed:
        failures.append(f"bounds/pivot drift {row['asset_name']}")
    results.append({
        "asset": asset_path,
        "source_fbx": row["fbx"],
        "source_sha256": row["sha256"],
        "expected_dimensions_mm": expected_dims_mm,
        "measured_dimensions_mm": [round(v, 3) for v in measured_dims_mm],
        "dimension_delta_mm": [round(v, 3) for v in dim_delta_mm],
        "expected_local_min_cm": [round(v, 4) for v in expected_local_min_cm],
        "expected_local_max_cm": [round(v, 4) for v in expected_local_max_cm],
        "measured_local_min_cm": [round(v, 4) for v in measured_min_cm],
        "measured_local_max_cm": [round(v, 4) for v in measured_max_cm],
        "local_bound_delta_mm": [round(v, 3) for v in local_bound_delta_mm],
        "material_slots": material_slots,
        "status": "PASS" if passed else "FAIL",
    })
    library.save_loaded_asset(mesh, only_if_is_dirty=False)

source_hashes_after = {row["fbx"]: sha256(SOURCE / row["fbx"]) for row in manifest["assets"]}
if source_hashes_after != source_hashes_before:
    failures.append("protected source Candidate_v002 changed")

report = {
    "$schema": "cairnwell/audit/press-shop-pr005-exterior-enclosure-unreal-intake-v002/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__NINE_MODULAR_MESHES_IMPORTED_WITH_DIMENSIONS_AND_LOCAL_PIVOTS_PRESERVED__PLACEMENT_RUNTIME_AND_PROMOTION_HOLD" if not failures else "FAIL__PR005_V002_UNREAL_INTAKE__NOT_INTEGRATED_NOT_PROMOTED",
    "source_candidate": "SourceAssets/Candidate/PressShop/PR005/Candidate_v002",
    "destination": DEST,
    "asset_count": len(results),
    "tolerance_mm": 2.0,
    "world_placement": "TBC_NOT_INVENTED",
    "gameplay_footprint_extent_y_mm": 10400,
    "planning_line_notation_mm": 11500,
    "relationship": "TBC_NOT_INVENTED",
    "runtime_movers_replaced": False,
    "v053_or_production_maps_changed": False,
    "source_hashes_before": source_hashes_before,
    "source_hashes_after": source_hashes_after,
    "results": results,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "assets": len(results), "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
