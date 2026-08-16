"""Isolated UE 5.8 import and dimension audit for physical train signs v396."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_ROOT = ROOT / "SourceAssets/Candidate/PressShop/TrainIdentity/PhysicalSigns_v396"
MANIFEST_PATH = SOURCE_ROOT / "PHYSICAL_TRAIN_IDENTITY_MANIFEST_v396.json"
DEST = "/Game/LineBoss/Candidates/PressShop/TrainIdentity/PhysicalSigns_v397"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_physical_train_identity_unreal_intake_v397.json"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


lib = unreal.EditorAssetLibrary
if lib.does_directory_exist(DEST) or OUT.exists():
    raise RuntimeError("refusing to overwrite preserved v397 intake")
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")

tasks = []
for row in manifest["assets"]:
    source = SOURCE_ROOT / row["file"]
    if sha(source) != row["sha256"]:
        raise RuntimeError(f"source hash drift: {source.name}")
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source), "destination_path": DEST,
        "destination_name": row["asset"], "automated": True,
        "replace_existing": False, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False,
        "import_materials": True, "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "transform_vertex_to_absolute": False, "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": True, "auto_generate_collision": False,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    tasks.append(task)

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

records = []
failures = []
for source_row in manifest["assets"]:
    path = f"{DEST}/{source_row['asset']}"
    mesh = lib.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        failures.append(f"missing static mesh {path}")
        continue
    bounds = mesh.get_bounds()
    size = [bounds.box_extent.x * 2.0, bounds.box_extent.y * 2.0, bounds.box_extent.z * 2.0]
    slots = [str(slot.material_slot_name) for slot in mesh.get_editor_property("static_materials")]
    # UE legacy FBX commonly carries Blender metres as centimetres for this family.
    # Record the exact ratio; map placement must compensate only after this gate.
    expected_cm = [value / 10.0 for value in source_row["measured_dimensions_mm"]]
    sorted_ratio = sorted(size)[-1] / sorted(expected_cm)[-1] if max(expected_cm) else 0.0
    if not (0.009 <= sorted_ratio <= 1.01):
        failures.append(f"unexpected import scale {source_row['asset']}: size={size}, ratio={sorted_ratio}")
    if len(slots) != 4:
        failures.append(f"material slot count {source_row['asset']}: {len(slots)}")
    records.append({
        "asset": path, "source_sha256": source_row["sha256"],
        "imported_bounds_cm": size, "expected_visual_bounds_cm": expected_cm,
        "largest_axis_ratio_imported_to_expected": sorted_ratio,
        "material_slots": slots,
        "nanite_enabled": bool(mesh.get_editor_property("nanite_settings").enabled),
    })

payload = {
    "$schema": "cairnwell/audit/press-shop-physical-train-identity-unreal-intake-v397/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FOUR_PHYSICAL_IDENTITY_MESHES_IMPORTED__PLACEMENT_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V397_NOT_AUTHORIZED_FOR_PLACEMENT",
    "source_manifest": str(MANIFEST_PATH.relative_to(ROOT)).replace("\\", "/"),
    "destination": DEST, "assets": records,
    "runtime_naming_contract": {
        "allocator": "stable next-available train designation A..Z; never renumber surviving trains",
        "station_display_ids": "<train designation>-S01 through <train designation>-S07",
        "persistent_identity": "immutable save GUID separate from editable display name",
        "current_moorcross_instances": ["A", "B", "C", "D"],
        "implementation_status": "contract recorded; runtime allocator remains open",
    },
    "promotion_authorized": False, "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
