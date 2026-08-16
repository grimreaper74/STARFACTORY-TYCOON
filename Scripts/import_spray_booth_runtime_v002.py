"""Fresh-only Unreal import of the original procedural spray booth v002."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
SCRIPT_FILE = PROJECT / "Scripts/import_spray_booth_runtime_v002.py"
AUTHORITY = PROJECT / "SourceAssets/Candidate/PaintShop/SprayBoothRuntime_v002/Authority"
LOD0 = AUTHORITY / "LB_PaintSprayBooth_Runtime_LOD0_v002.fbx"
LOD1 = AUTHORITY / "LB_PaintSprayBooth_Runtime_LOD1_v002.fbx"
MANIFEST = AUTHORITY / "authority_manifest_v002.json"
ROUNDTRIP = AUTHORITY / "Audit/roundtrip_validation_v002.json"
RECOVERY_AUTHORITY = AUTHORITY / "unreal_lane_recovery_authority_v003.json"
DEST = "/Game/LineBoss/Candidates/PaintShop/SprayBoothRuntime_v002"
ASSET_NAME = "SM_LB_PaintSprayBooth_Runtime_v002"
MESH_PACKAGE = f"{DEST}/{ASSET_NAME}"
AUDIT = PROJECT / "Saved/Audits/PaintShop/SprayBoothRuntime_v002/import_v002.json"
SOURCE_HASHES = {
    LOD0: "E38464ED0BFD141E6D6F28B7EF24EA6DFBB45F4DCB3C7F67DF0FC3CEA3F30B97",
    LOD1: "F55CB80FAD1F340FB97B928CC700807D2D82ADC282F16D2287CAE64B57D6CCFB",
    MANIFEST: "003A69983AFD71A5D9636145C4A3D4049ADDBB9EE0DDE6D7CB8C92AAB82A7EE4",
    ROUNDTRIP: "068F4BCF63FB67B2017DD1DE4AE93D1B29C1C0560FBCE83FCE6B393207BDF251",
    RECOVERY_AUTHORITY: "541A4F2DBD97A19106F932B39CF495A7FB7030371F7C7EDC18CE8D6CA4C73034",
}
MATERIAL_NAMES = (
    "M_LB_Cairnwell_Green", "M_LB_Extraction_Gray", "M_LB_Frame_Graphite",
    "M_LB_Panel_OffWhite", "M_LB_Rail_Steel", "M_LB_Safety_Yellow",
)
EXPECTED_TRIANGLES = (3804, 420)
EXPECTED_BOUNDS_CM = (1200.0, 500.0, 450.0)
LOD_SCREEN_SIZES = (1.0, 0.30)
EXPECTED_COLLISION_COUNTS = {
    "box_elems": 0,
    "sphere_elems": 0,
    "sphyl_elems": 0,
    "tapered_capsule_elems": 0,
    "convex_elems": 3,
}

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def slot_name(slot) -> str:
    return str(slot.get_editor_property("imported_material_slot_name") or
               slot.get_editor_property("material_slot_name"))


def collision_evidence(mesh) -> dict:
    """Read the exact reflected aggregate inventory; never infer UCX from simple count."""
    body_setup = mesh.get_editor_property("body_setup")
    require(body_setup is not None, "StaticMesh BodySetup is missing")
    aggregate = body_setup.get_editor_property("agg_geom")
    counts = {
        field: len(aggregate.get_editor_property(field))
        for field in EXPECTED_COLLISION_COUNTS
    }
    require(counts == EXPECTED_COLLISION_COUNTS,
            f"Exact BodySetup AggGeom collision inventory drift: {counts}")
    simple_api_count = int(subsystem.get_simple_collision_count(mesh))
    convex_api_count = int(subsystem.get_convex_collision_count(mesh))
    require(simple_api_count == 0,
            f"UE 5.8 box+sphere+sphyl diagnostic count drift: {simple_api_count}")
    require(convex_api_count == 3,
            f"UE 5.8 convex collision diagnostic count drift: {convex_api_count}")
    return {
        "acceptance_basis": "BODY_SETUP_AGG_GEOM_EXACT_TYPE_COUNTS",
        "aggregate_geometry_counts": counts,
        "static_mesh_editor_simple_collision_count": simple_api_count,
        "static_mesh_editor_convex_collision_count": convex_api_count,
        "runtime_convex_vertex_bounds_validation": (
            "UNAVAILABLE__UE_5_8_KCONVEXELEM_PYTHON_REFLECTION_EXPOSES_"
            "NEITHER_VERTEX_DATA_NOR_BOUNDS"
        ),
    }


def package_disk_path(package: str) -> Path:
    require(package.startswith("/Game/"), f"Unexpected package root: {package}")
    return PROJECT / "Content" / (package[len("/Game/"):] + ".uasset")


def package_file_evidence(packages) -> list[dict]:
    rows = []
    for package in sorted(packages):
        disk_path = package_disk_path(package)
        require(disk_path.is_file(), f"Saved package is absent on disk: {disk_path}")
        rows.append({
            "package": package,
            "path": str(disk_path.relative_to(PROJECT)).replace("\\", "/"),
            "bytes": disk_path.stat().st_size,
            "sha256": sha256(disk_path),
        })
    return rows


def main() -> None:
    require(not lib.does_directory_exist(DEST), f"Fresh namespace required: {DEST}")
    require(not AUDIT.exists(), f"Refusing to overwrite import receipt: {AUDIT}")
    require(subsystem is not None and hasattr(subsystem, "import_lod"),
            "StaticMeshEditorSubsystem.import_lod unavailable")
    for path, expected in SOURCE_HASHES.items():
        require(path.is_file() and sha256(path) == expected,
                f"Frozen original source drift: {path}")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    roundtrip = json.loads(ROUNDTRIP.read_text(encoding="utf-8"))
    recovery = json.loads(RECOVERY_AUTHORITY.read_text(encoding="utf-8"))
    require(manifest.get("status", "").startswith("PASS__TWO_ORIGINAL_PROCEDURAL"),
            "Authority manifest is not PASS")
    require(roundtrip.get("status", "").startswith("PASS__TWO_ORIGINAL_PROCEDURAL"),
            "Independent source round-trip is not PASS")
    require(recovery.get("status", "").startswith(
                "FROZEN__EXACT_COLLISION_INCIDENT_DIAGNOSED"),
            "Successor Unreal-lane recovery authority is not frozen")

    unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(LOD0), "destination_path": DEST,
        "destination_name": ASSET_NAME, "automated": True,
        "replace_existing": False, "replace_existing_settings": False, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False,
        "import_materials": True, "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type": False,
    })
    options.static_mesh_import_data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "force_front_x_axis": False, "import_uniform_scale": 1.0,
        "normal_import_method": unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS,
        "generate_lightmap_u_vs": True, "auto_generate_collision": False,
        "remove_degenerates": True, "one_convex_hull_per_ucx": True,
    })
    task.set_editor_property("options", options)
    tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    mesh = lib.load_asset(MESH_PACKAGE)
    require(isinstance(mesh, unreal.StaticMesh), "LOD0 import did not produce exact StaticMesh")
    require(subsystem.import_lod(mesh, 1, str(LOD1)) == 1, "Authored LOD1 import failed")
    nanite = mesh.get_editor_property("nanite_settings")
    nanite.enabled = False
    mesh.set_editor_property("nanite_settings", nanite)
    mesh.set_editor_property("light_map_coordinate_index", 1)
    mesh.set_editor_property("light_map_resolution", 64)
    require(subsystem.set_lod_screen_sizes(mesh, list(LOD_SCREEN_SIZES)),
            "Could not set exact authored LOD screen sizes")
    for material_name in MATERIAL_NAMES:
        material_path = f"{DEST}/{material_name}"
        material = lib.load_asset(material_path)
        require(material is not None, f"Imported material is missing: {material_path}")
        require(lib.save_loaded_asset(material, only_if_is_dirty=False),
                f"Material package save failed: {material_path}")
    require(lib.save_loaded_asset(mesh, only_if_is_dirty=False), "StaticMesh save failed")
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

    triangles = tuple(int(mesh.get_num_triangles(index)) for index in range(mesh.get_num_lods()))
    bounds = tuple(round(float(value), 3) for value in (
        mesh.get_bounds().box_extent.x * 2, mesh.get_bounds().box_extent.y * 2,
        mesh.get_bounds().box_extent.z * 2,
    ))
    materials = tuple(sorted(slot_name(slot) for slot in mesh.get_editor_property("static_materials")))
    packages = sorted(path.split(".", 1)[0] for path in
                      lib.list_assets(DEST, recursive=True, include_folder=False))
    expected_packages = {MESH_PACKAGE} | {f"{DEST}/{name}" for name in MATERIAL_NAMES}
    require(triangles == EXPECTED_TRIANGLES, f"Exact source LOD triangles drift: {triangles}")
    require(all(abs(a - b) <= .5 for a, b in zip(bounds, EXPECTED_BOUNDS_CM)),
            f"Bounds drift: {bounds}")
    require(materials == tuple(sorted(MATERIAL_NAMES)), f"Material slots drift: {materials}")
    collision = collision_evidence(mesh)
    require(not bool(mesh.get_editor_property("nanite_settings").enabled), "Nanite must be disabled")
    require([round(float(v), 2) for v in subsystem.get_lod_screen_sizes(mesh)] == [1.0, .3],
            "LOD screen sizes drifted")
    require(set(packages) == expected_packages,
            f"Controlled namespace exact package inventory drift: {packages}")
    package_files = package_file_evidence(expected_packages)

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "$schema": "lineboss/audit/paint/spray-booth-runtime-import-v002/v2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__FRESH_ORIGINAL_PROCEDURAL_SPRAY_BOOTH__TWO_SOURCE_LODS__PORTAL_SAFE_COLLISION",
        "destination": DEST, "mesh": mesh.get_path_name(), "packages": packages,
        "importer_script_sha256": sha256(SCRIPT_FILE),
        "source_hashes": {str(path.relative_to(PROJECT)).replace("\\", "/"): digest
                          for path, digest in SOURCE_HASHES.items()},
        "bounds_cm": bounds, "triangles": triangles, "materials": materials,
        "collision": collision, "package_files": package_files,
        "nanite_enabled": False,
        "lightmap_coordinate_index": 1, "lightmap_resolution": 64,
        "lod_screen_sizes": [1.0, .3], "portal_clearance_cm": [430.0, 335.0],
        "solid_long_sides": True, "robots": 0, "screens": 0,
        "maps_modified": False, "config_modified": False, "source_modified": False,
    }
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_SPRAY_BOOTH_RUNTIME_V002_IMPORT_PASS")


if __name__ == "__main__":
    main()
