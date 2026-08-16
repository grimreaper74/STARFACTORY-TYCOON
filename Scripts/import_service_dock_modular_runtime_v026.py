"""Import the verified v026 modular dock FBXs into a fresh Unreal asset path."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir())
DEST = "/Game/LineBoss/SupportRobots/ServiceDocks/Runtime_v026"
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/SupportRobots/service_dock_modular_runtime_import_v026.json"
SOURCES = {
    "mr01": PROJECT / "SourceAssets/SharedSystems/MaintenanceAMR/Dock_Candidate_v005/Unreal_ModularRuntime_v026",
    "cr01": PROJECT / "SourceAssets/SharedSystems/CleaningAMR/Dock_Candidate_v008/Unreal_ModularRuntime_v026",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def import_fbx(fbx: Path, destination: str, asset_name: str):
    asset_path = f"{destination}/{asset_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        raise RuntimeError(f"non-overwrite invariant failed; asset already exists: {asset_path}")
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(fbx), "destination_path": destination, "destination_name": asset_name,
        "automated": True, "replace_existing": False, "replace_existing_settings": False, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False, "import_materials": True,
        "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type": False,
    })
    options.static_mesh_import_data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "force_front_x_axis": False, "generate_lightmap_u_vs": True,
        "auto_generate_collision": True, "remove_degenerates": True,
    })
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
    if mesh is None:
        raise RuntimeError(f"import failed: {asset_path}; returned {task.imported_object_paths}")
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    return asset_path, mesh


def vec(value):
    return [round(value.x, 3), round(value.y, 3), round(value.z, 3)]


unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
records = []
for mode, folder in SOURCES.items():
    manifest_path = next(folder.glob("*_EXPORT_MANIFEST.json"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for key, component in manifest["components"].items():
        fbx = Path(component["fbx"])
        name = component["asset_name"]
        path, mesh = import_fbx(fbx, f"{DEST}/{mode.upper()}", name)
        size = mesh.get_bounds().box_extent * 2.0
        if min(size.x, size.y, size.z) <= 0.01:
            raise RuntimeError(f"degenerate imported bounds for {path}: {vec(size)}")
        uasset = PROJECT / "Content" / Path(path.removeprefix("/Game/") + ".uasset")
        if not uasset.is_file():
            raise RuntimeError(f"missing saved package: {uasset}")
        records.append({
            "mode": mode, "component": key, "asset_path": path,
            "bounds_cm": vec(size), "fbx_sha256": sha256(fbx),
            "uasset_sha256": sha256(uasset), "pivot_blender_mm": component["pivot_blender_mm"],
            "motion_authority": component.get("motion_authority"),
        })

mr_static = next(record for record in records if record["mode"] == "mr01" and record["component"] == "static")
cr_static = next(record for record in records if record["mode"] == "cr01" and record["component"] == "static")
failures = []
for label, record in (("MR01", mr_static), ("CR01", cr_static)):
    # Blender X width becomes Unreal X with the retained FBX convention.
    if not 259.0 <= record["bounds_cm"][0] <= 261.0:
        failures.append(f"{label} static width is not the authorised 260 cm: {record['bounds_cm']}")
if failures:
    raise RuntimeError("; ".join(failures))

payload = {
    "$schema": "cairnwell/audit/service-dock-modular-runtime-import-v026/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FRESH_NON_OVERWRITING_MODULAR_UNREAL_IMPORT__RUNTIME_AND_VISUAL_GATES_OPEN__NOT_PROMOTED",
    "destination": DEST,
    "assets": records,
    "policy": {
        "mr01_movers": "source-authorised pivots and ranges only",
        "cr01_movers": "static until pivots/travel are validated",
        "existing_intake_assets_overwritten": False,
        "press_shop_map_changed": False,
    },
    "failures": failures,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_SERVICE_DOCK_MODULAR_RUNTIME_IMPORT_V026_PASS")
unreal.log(json.dumps(payload, indent=2))
