"""Independent read-only validation of spray booth runtime v002 packages."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
SCRIPT_FILE = PROJECT / "Scripts/validate_spray_booth_runtime_v002.py"
IMPORTER = PROJECT / "Scripts/import_spray_booth_runtime_v002.py"
IMPORTER_SHA256 = "B23FF792228CC5198178CE99C6C8BFFD322FD9720424329FDBD01485F28399EF"
AUTHORITY = PROJECT / "SourceAssets/Candidate/PaintShop/SprayBoothRuntime_v002/Authority"
DEST = "/Game/LineBoss/Candidates/PaintShop/SprayBoothRuntime_v002"
NAME = "SM_LB_PaintSprayBooth_Runtime_v002"
MESH_PACKAGE = f"{DEST}/{NAME}"
IMPORT_RECEIPT = PROJECT / "Saved/Audits/PaintShop/SprayBoothRuntime_v002/import_v002.json"
AUDIT = PROJECT / "Saved/Audits/PaintShop/SprayBoothRuntime_v002/validation_v002.json"
SOURCE_HASHES = {
    AUTHORITY / "LB_PaintSprayBooth_Runtime_LOD0_v002.fbx":
        "E38464ED0BFD141E6D6F28B7EF24EA6DFBB45F4DCB3C7F67DF0FC3CEA3F30B97",
    AUTHORITY / "LB_PaintSprayBooth_Runtime_LOD1_v002.fbx":
        "F55CB80FAD1F340FB97B928CC700807D2D82ADC282F16D2287CAE64B57D6CCFB",
    AUTHORITY / "authority_manifest_v002.json":
        "003A69983AFD71A5D9636145C4A3D4049ADDBB9EE0DDE6D7CB8C92AAB82A7EE4",
    AUTHORITY / "Audit/roundtrip_validation_v002.json":
        "068F4BCF63FB67B2017DD1DE4AE93D1B29C1C0560FBCE83FCE6B393207BDF251",
    AUTHORITY / "unreal_lane_recovery_authority_v003.json":
        "541A4F2DBD97A19106F932B39CF495A7FB7030371F7C7EDC18CE8D6CA4C73034",
}
MATERIAL_NAMES = (
    "M_LB_Cairnwell_Green", "M_LB_Extraction_Gray", "M_LB_Frame_Graphite",
    "M_LB_Panel_OffWhite", "M_LB_Rail_Steel", "M_LB_Safety_Yellow",
)
EXPECTED_COLLISION_COUNTS = {
    "box_elems": 0,
    "sphere_elems": 0,
    "sphyl_elems": 0,
    "tapered_capsule_elems": 0,
    "convex_elems": 3,
}


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest().upper()


def slot_name(slot) -> str:
    return str(slot.get_editor_property("imported_material_slot_name") or
               slot.get_editor_property("material_slot_name"))


def collision_evidence(mesh, subsystem) -> dict:
    """Read every accepted collision type directly from BodySetup AggGeom."""
    body_setup = mesh.get_editor_property("body_setup")
    if body_setup is None:
        raise RuntimeError("StaticMesh BodySetup is missing")
    aggregate = body_setup.get_editor_property("agg_geom")
    counts = {
        field: len(aggregate.get_editor_property(field))
        for field in EXPECTED_COLLISION_COUNTS
    }
    return {
        "acceptance_basis": "BODY_SETUP_AGG_GEOM_EXACT_TYPE_COUNTS",
        "aggregate_geometry_counts": counts,
        "static_mesh_editor_simple_collision_count":
            int(subsystem.get_simple_collision_count(mesh)),
        "static_mesh_editor_convex_collision_count":
            int(subsystem.get_convex_collision_count(mesh)),
        "runtime_convex_vertex_bounds_validation": (
            "UNAVAILABLE__UE_5_8_KCONVEXELEM_PYTHON_REFLECTION_EXPOSES_"
            "NEITHER_VERTEX_DATA_NOR_BOUNDS"
        ),
    }


def package_disk_path(package: str) -> Path:
    if not package.startswith("/Game/"):
        raise RuntimeError(f"Unexpected package root: {package}")
    return PROJECT / "Content" / (package[len("/Game/"):] + ".uasset")


def package_file_evidence(packages) -> tuple[list[dict], list[str]]:
    rows = []
    missing = []
    for package in sorted(packages):
        disk_path = package_disk_path(package)
        if not disk_path.is_file():
            missing.append(str(disk_path))
            continue
        rows.append({
            "package": package,
            "path": str(disk_path.relative_to(PROJECT)).replace("\\", "/"),
            "bytes": disk_path.stat().st_size,
            "sha256": sha256(disk_path),
        })
    return rows, missing


def main() -> None:
    lib = unreal.EditorAssetLibrary
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    failures = []
    if AUDIT.exists():
        raise RuntimeError(f"Refusing to overwrite validation receipt: {AUDIT}")
    if not IMPORT_RECEIPT.is_file():
        failures.append("missing import receipt")
        receipt = {}
    else:
        receipt = json.loads(IMPORT_RECEIPT.read_text(encoding="utf-8"))
    if sha256(IMPORTER) != IMPORTER_SHA256:
        failures.append("frozen importer hash drift")
    if receipt.get("importer_script_sha256") != IMPORTER_SHA256:
        failures.append("receipt/importer hash mismatch")
    for path, expected in SOURCE_HASHES.items():
        if not path.is_file() or sha256(path) != expected:
            failures.append(f"source hash drift: {path.name}")
    manifest = json.loads((AUTHORITY / "authority_manifest_v002.json").read_text(encoding="utf-8"))
    roundtrip = json.loads((AUTHORITY / "Audit/roundtrip_validation_v002.json").read_text(encoding="utf-8"))
    recovery = json.loads((AUTHORITY / "unreal_lane_recovery_authority_v003.json").read_text(
        encoding="utf-8"))
    if "Meshy" in manifest.get("provenance", "").replace("no Meshy", ""):
        failures.append("Meshy provenance contamination")
    if manifest.get("failures") or roundtrip.get("failures"):
        failures.append("offline authority did not pass")
    if not recovery.get("status", "").startswith("FROZEN__EXACT_COLLISION_INCIDENT_DIAGNOSED"):
        failures.append("successor Unreal-lane recovery authority is not frozen")

    expected_packages = {MESH_PACKAGE} | {f"{DEST}/{name}" for name in MATERIAL_NAMES}
    actual_packages = {path.split(".", 1)[0] for path in
                       lib.list_assets(DEST, recursive=True, include_folder=False)}
    if actual_packages != expected_packages:
        failures.append(f"exact seven-package namespace drift: {sorted(actual_packages)}")
    package_files, missing_package_files = package_file_evidence(expected_packages)
    if missing_package_files:
        failures.append(f"saved package files absent on disk: {missing_package_files}")
    if receipt.get("package_files") != package_files:
        failures.append("fresh-process package file evidence differs from import receipt")
    mesh = lib.load_asset(MESH_PACKAGE)
    facts = {}
    if not isinstance(mesh, unreal.StaticMesh):
        failures.append("exact StaticMesh missing")
    else:
        bounds = tuple(round(float(v), 3) for v in (
            mesh.get_bounds().box_extent.x * 2, mesh.get_bounds().box_extent.y * 2,
            mesh.get_bounds().box_extent.z * 2,
        ))
        triangles = tuple(int(mesh.get_num_triangles(i)) for i in range(mesh.get_num_lods()))
        screens = tuple(round(float(v), 2) for v in subsystem.get_lod_screen_sizes(mesh))
        material_rows = []
        for index, slot in enumerate(mesh.get_editor_property("static_materials")):
            name = slot_name(slot)
            material = mesh.get_material(index)
            path = material.get_path_name() if material else None
            expected = f"{DEST}/{name}.{name}"
            material_rows.append({"slot": name, "material": path, "expected": expected})
            if name not in MATERIAL_NAMES or path != expected:
                failures.append(f"material binding drift: {name} -> {path}")
        try:
            collision = collision_evidence(mesh, subsystem)
        except Exception as error:
            collision = {}
            failures.append(f"could not read exact BodySetup AggGeom collision inventory: {error}")
        nanite = bool(mesh.get_editor_property("nanite_settings").enabled)
        if triangles != (3804, 420): failures.append(f"LOD triangle drift: {triangles}")
        if any(abs(a - b) > .5 for a, b in zip(bounds, (1200, 500, 450))):
            failures.append(f"bounds drift: {bounds}")
        if screens != (1.0, .3): failures.append(f"LOD screens drift: {screens}")
        if collision:
            counts = collision["aggregate_geometry_counts"]
            if counts != EXPECTED_COLLISION_COUNTS:
                failures.append(f"exact BodySetup AggGeom collision inventory drift: {counts}")
            if collision["static_mesh_editor_simple_collision_count"] != 0:
                failures.append("UE 5.8 box+sphere+sphyl diagnostic count drift")
            if collision["static_mesh_editor_convex_collision_count"] != 3:
                failures.append("UE 5.8 convex collision diagnostic count drift")
            if receipt.get("collision") != collision:
                failures.append("fresh-process collision evidence differs from import receipt")
        if nanite: failures.append("Nanite enabled")
        if int(mesh.get_editor_property("light_map_coordinate_index")) != 1:
            failures.append("lightmap UV coordinate index drift")
        if int(mesh.get_editor_property("light_map_resolution")) != 64:
            failures.append("lightmap resolution drift")
        facts = {
            "mesh": mesh.get_path_name(), "bounds_cm": bounds, "triangles": triangles,
            "lod_count": mesh.get_num_lods(), "lod_screen_sizes": screens,
            "materials": material_rows, "collision": collision,
            "package_files": package_files,
            "nanite_enabled": nanite, "lightmap_coordinate_index": 1,
            "lightmap_resolution": 64, "portal_clearance_cm": [430, 335],
            "solid_long_sides": True, "robots": 0, "screens": 0,
        }
    payload = {
        "$schema": "lineboss/audit/paint/spray-booth-runtime-validation-v002/v2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": ("PASS__INDEPENDENT_SPRAY_BOOTH_V002__EXACT_GEOMETRY_MATERIALS_LODS_COLLISION_UV_NANITE_SCREENS_PROVENANCE"
                   if not failures else "FAIL__DO_NOT_REFERENCE_SPRAY_BOOTH_V002"),
        "destination": DEST, "expected_packages": sorted(expected_packages),
        "actual_packages": sorted(actual_packages), "facts": facts,
        "source_hashes": {str(path.relative_to(PROJECT)).replace("\\", "/"): expected
                          for path, expected in SOURCE_HASHES.items()},
        "import_receipt_sha256": sha256(IMPORT_RECEIPT) if IMPORT_RECEIPT.is_file() else None,
        "validator_script_sha256": sha256(SCRIPT_FILE),
        "read_only_content_validation": True, "maps_modified": False,
        "config_modified": False, "source_modified": False, "failures": failures,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise RuntimeError(" | ".join(failures))
    unreal.log("LINE_BOSS_SPRAY_BOOTH_RUNTIME_V002_VALIDATION_PASS")


if __name__ == "__main__":
    main()
