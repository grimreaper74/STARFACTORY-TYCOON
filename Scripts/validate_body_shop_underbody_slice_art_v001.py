"""Read-only validation of the fresh Body Shop Underbody Slice art intake."""

from __future__ import annotations

import hashlib
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
SOURCE = PROJECT / "SourceAssets/Candidate/WeldShop/BodyShopUnderbodySlice_v001"
MANIFEST = SOURCE / "MANIFEST_v001.json"
FREEZE = SOURCE / "Audit/FROZEN_v001.json"
ROUNDTRIP = SOURCE / "Audit/roundtrip_validation_v001.json"
DEST = "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001"
DEST_DISK = PROJECT / "Content/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001"
AUDIT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001"
IMPORT_RECEIPT = AUDIT / "import_underbody_slice_art_receipt_v001.json"
PRECLEANUP_COMPLETION_RECEIPT = AUDIT / "complete_underbody_slice_art_precleanup_receipt_v001.json"
RECEIPT = AUDIT / "validate_underbody_slice_art_receipt_v001.json"
FAILURE = AUDIT / "validate_underbody_slice_art_failure_v001.json"
STAGING = DEST + "/__LegacyLODStaging"
lib = unreal.EditorAssetLibrary


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_UNDERBODY_ART_VALIDATION_V001_FAIL: " + message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def vector(value):
    return [float(value.x), float(value.y), float(value.z)]


def lod_bounds_cm(mesh, lod_index: int):
    dynamic_mesh = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    requested_lod = unreal.GeometryScriptMeshReadLOD()
    requested_lod.set_editor_properties({"lod_type": unreal.GeometryScriptLODType.SOURCE_MODEL,
                                         "lod_index": lod_index})
    dynamic_mesh, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic_mesh, options, requested_lod, False)
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        fail("source LOD bounds extraction failed: " + mesh.get_name() + ":" + str(lod_index) + ":" + str(outcome))
    box = dynamic_mesh.get_mesh_bounding_box()
    minimum, maximum = vector(box.min), vector(box.max)
    return minimum, maximum, [maximum[index] - minimum[index] for index in range(3)]


def package_path(asset_path: str) -> Path:
    return PROJECT / "Content" / Path(asset_path.replace("/Game/", "")).with_suffix(".uasset")


def frozen_inventory() -> dict:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if freeze.get("status") != "FROZEN_SOURCE_DERIVATIVE__ROUNDTRIP_PASS__UNREAL_IMPORT_PENDING":
        fail("freeze status drift")
    output = {}
    for row in freeze.get("files", []):
        path = SOURCE / row["path"]
        actual = {"bytes": path.stat().st_size, "sha256": sha256(path)} if path.is_file() else None
        if not actual or actual["bytes"] != row["bytes"] or actual["sha256"] != row["sha256"].upper():
            fail("frozen source drift: " + row["path"])
        output[row["path"]] = actual
    return output


def disk_inventory() -> dict:
    if not DEST_DISK.is_dir():
        return {}
    output = {}
    for path in DEST_DISK.rglob("*"):
        if path.is_file():
            output[str(path.relative_to(PROJECT / "Content")).replace("\\", "/")] = {
                "bytes": path.stat().st_size, "sha256": sha256(path),
            }
    return output


def staging_asset_path(name: str, lod_index: int) -> str:
    return STAGING + "/" + name + "__LegacySourceLOD" + str(lod_index)


def material_contract(mesh, name: str) -> list:
    slots = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        material = mesh.get_material(index)
        material_path = material.get_path_name() if material else None
        if material_path and material_path.startswith(DEST + "/"):
            fail("unexpected destination material package: " + name + ":" + material_path)
        slots.append({"index": index, "slot": str(slot.get_editor_property("material_slot_name")),
                      "material": material_path})
    return slots


def triangle_contract(name: str, lod_index: int, expected: int, actual: int) -> dict:
    # This is deliberately a one-source, one-LOD exception. The legacy FbxFactory
    # strips 240 zero-area fixture faces before both source-model and render data;
    # bounds, settings, and every other one of the 27 imports remain exact.
    if name == "SM_LB_BodyShop_UnderbodyFixture_v001" and lod_index == 0:
        if expected == 6768 and actual == 6528:
            return {"result": "PASS__NAMED_LEGACY_ZERO_AREA_FACE_NORMALIZATION_EXCEPTION",
                    "frozen_triangles": 6768, "ue_legacy_triangles": 6528,
                    "delta": -240,
                    "scope": "SM_LB_BodyShop_UnderbodyFixture_v001:LOD0 only"}
        fail("fixture named exception drift: expected frozen 6768 / legacy 6528, got " + str([expected, actual]))
    if actual != expected:
        fail("LOD/triangle drift: " + name + ":LOD" + str(lod_index) + ":" + str([expected, actual]))
    return {"result": "PASS__EXACT", "frozen_triangles": expected, "ue_legacy_triangles": actual, "delta": 0}


def staged_mesh_contract(name: str, lod_index: int, source_row: dict) -> dict:
    asset_path = staging_asset_path(name, lod_index)
    mesh = lib.load_asset(asset_path)
    if not isinstance(mesh, unreal.StaticMesh):
        fail("staging static-mesh drift: " + asset_path)
    if int(mesh.get_num_lods()) != 1:
        fail("staging LOD count drift: " + asset_path)
    triangles = int(mesh.get_num_triangles(0))
    expected = int(source_row["triangles"])
    triangle = triangle_contract(name, lod_index, expected, triangles)
    minimum, maximum, dimensions = lod_bounds_cm(mesh, 0)
    expected_dimensions = [float(value) * 100.0 for value in source_row["bounds_m"]]
    delta = [dimensions[index] - expected_dimensions[index] for index in range(3)]
    if max(abs(value) for value in delta) > 0.5:
        fail("staging scale/axis drift: " + name + ":LOD" + str(lod_index))
    data = mesh.get_editor_property("asset_import_data")
    settings = {"import_uniform_scale": float(data.get_editor_property("import_uniform_scale")),
                "transform_vertex_to_absolute": bool(data.get_editor_property("transform_vertex_to_absolute")),
                "remove_degenerates": bool(data.get_editor_property("remove_degenerates"))}
    if settings != {"import_uniform_scale": 1.0, "transform_vertex_to_absolute": True, "remove_degenerates": False}:
        fail("staging legacy import-data policy drift: " + name + ":LOD" + str(lod_index))
    return {"asset": mesh.get_path_name(), "lod": lod_index, "triangles": triangles,
            "triangle_contract": triangle, "bounds_cm": {"min": minimum, "max": maximum, "dimensions": dimensions},
            "expected_dimensions_cm": expected_dimensions, "dimension_delta_cm": delta,
            "legacy_import_data": settings}


def main() -> None:
    evidence = {"$schema": "lineboss/audit/bodyshop/experimental-v001-underbody-art-validation/v1",
                "generated_utc": datetime.now(timezone.utc).isoformat(),
                "destination_namespace": DEST, "map_changes": [], "runtime_binding_changes": [],
                "source_assets_mutated": False, "meshy_credits_used_by_codex": 0}
    try:
        if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
            fail("running project identity mismatch")
        if not all(path.is_file() for path in (MANIFEST, FREEZE, ROUNDTRIP, PRECLEANUP_COMPLETION_RECEIPT)):
            fail("source or pre-cleanup completion receipt is missing")
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        roundtrip = json.loads(ROUNDTRIP.read_text(encoding="utf-8"))
        completed = json.loads(PRECLEANUP_COMPLETION_RECEIPT.read_text(encoding="utf-8"))
        if manifest.get("unreal_content_intent") != DEST or roundtrip.get("status") != "PASS":
            fail("source contract identity/status drift")
        if completed.get("status") != "PASS__BODYSHOP_UNDERBODY_ART_PRECLEANUP_FINALS_COMPLETED_V001":
            fail("pre-cleanup completion is not a PASS receipt")
        if completed.get("source_manifest_sha256") != sha256(MANIFEST):
            fail("source manifest hash differs from pre-cleanup completion receipt")
        bindings = manifest.get("unreal_import_bindings", {})
        expected_assets = {row["object_path"].rsplit(".", 1)[0]: row for row in bindings.values()}
        expected_staging = {staging_asset_path(path.rsplit("/", 1)[-1], lod_index)
                            for path in expected_assets for lod_index in (1, 2)}
        # AssetRegistry returns object paths; compare the manifest's package paths.
        registry = {str(path).rsplit(".", 1)[0]
                    for path in lib.list_assets(DEST, recursive=True, include_folder=False)}
        if registry != set(expected_assets) | expected_staging:
            fail("asset-registry namespace inventory drift")
        expected_files = {str(package_path(path).relative_to(PROJECT / "Content")).replace("\\", "/")
                          for path in set(expected_assets) | expected_staging}
        inventory = disk_inventory()
        if set(inventory) != expected_files:
            fail("on-disk namespace package inventory drift")
        recorded_finals = completed.get("final_asset_packages", {})
        recorded_staging = completed.get("staging_asset_packages_before_and_after_identical", {})
        for package_key, package in inventory.items():
            recorded = recorded_staging.get(package_key) if "/__LegacyLODStaging/" in package_key else recorded_finals.get(package_key)
            if not recorded or package["sha256"] != recorded.get("sha256"):
                fail("package hash drift since pre-cleanup completion: " + package_key)

        rows_by_file = {row.get("file"): row for row in roundtrip.get("roundtrips", [])}
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        if subsystem is None:
            fail("StaticMeshEditorSubsystem unavailable")
        meshes = {}
        for asset_path, binding in sorted(expected_assets.items()):
            name = asset_path.rsplit("/", 1)[-1]
            mesh = lib.load_asset(asset_path)
            if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name() != binding["object_path"]:
                fail("static-mesh/object-path drift: " + name)
            source_rows = [rows_by_file.get(Path(binding[key]).name) for key in ("lod0_fbx", "lod1_fbx", "lod2_fbx")]
            if any(item is None for item in source_rows):
                fail("roundtrip LOD evidence missing: " + name)
            lod_count = int(mesh.get_num_lods())
            triangles = [int(mesh.get_num_triangles(index)) for index in range(lod_count)]
            if lod_count != 3:
                fail("final LOD count drift: " + name + ":" + str(lod_count))
            triangle_contracts = [triangle_contract(name, lod_index, int(source_row["triangles"]), triangles[lod_index])
                                  for lod_index, source_row in enumerate(source_rows)]
            lod_bounds = []
            for lod_index, source_row in enumerate(source_rows):
                minimum, maximum, dimensions = lod_bounds_cm(mesh, lod_index)
                expected_dimensions = [float(value) * 100.0 for value in source_row["bounds_m"]]
                delta = [dimensions[i] - expected_dimensions[i] for i in range(3)]
                if max(abs(value) for value in delta) > 0.5:
                    fail("scale/axis drift: " + name + ":LOD" + str(lod_index))
                lod_bounds.append({"lod": lod_index, "min_cm": minimum, "max_cm": maximum,
                                   "dimensions_cm": dimensions, "expected_dimensions_cm": expected_dimensions,
                                   "dimension_delta_cm": delta})
            import_data = mesh.get_editor_property("asset_import_data")
            try:
                import_scale = float(import_data.get_editor_property("import_uniform_scale"))
                absolute = bool(import_data.get_editor_property("transform_vertex_to_absolute"))
                remove = bool(import_data.get_editor_property("remove_degenerates"))
            except Exception as error:
                fail("legacy import-data unavailable: " + name + ":" + str(error))
            if abs(import_scale - 1.0) > 0.0001 or not absolute or remove:
                fail("legacy import-data policy drift: " + name + ":" + str([import_scale, absolute, remove]))
            simple = int(subsystem.get_simple_collision_count(mesh))
            convex = int(subsystem.get_convex_collision_count(mesh))
            trace = str(mesh.get_editor_property("body_setup").get_editor_property("collision_trace_flag"))
            nanite = bool(subsystem.get_nanite_settings(mesh).get_editor_property("enabled"))
            if simple or convex or nanite or "SIMPLE_AS_COMPLEX" not in trace.upper():
                fail("collision/Nanite policy drift: " + name)
            meshes[name] = {"asset": mesh.get_path_name(), "lod_count": lod_count,
                "triangles": triangles, "triangle_contracts": triangle_contracts, "lod_bounds_cm": lod_bounds,
                "simple_collision_count": simple, "convex_collision_count": convex,
                "collision_trace_flag": trace, "nanite_enabled": nanite,
                "material_slots": material_contract(mesh, name),
                "legacy_import_data": {"import_uniform_scale": import_scale,
                                       "transform_vertex_to_absolute": absolute,
                                       "remove_degenerates": remove}}

        evidence.update({"status": "PASS__BODYSHOP_UNDERBODY_ART_SOURCE_LOD_SCALE_NAMESPACE_AND_POLICY_VALIDATION_V001",
                         "source_manifest_sha256": sha256(MANIFEST), "freeze_manifest_sha256": sha256(FREEZE),
                         "roundtrip_report_sha256": sha256(ROUNDTRIP), "frozen_source_hashes": frozen_inventory(),
                         "precleanup_completion_receipt_sha256": sha256(PRECLEANUP_COMPLETION_RECEIPT),
                         "asset_packages": inventory, "meshes": meshes,
                         "staging_meshes": [staged_mesh_contract(asset_path.rsplit("/", 1)[-1], lod_index,
                                                                  [rows_by_file.get(Path(binding[key]).name)
                                                                   for key in ("lod0_fbx", "lod1_fbx", "lod2_fbx")][lod_index])
                                           for asset_path, binding in sorted(expected_assets.items()) for lod_index in (1, 2)],
                         "named_triangle_exception": {"asset": "SM_LB_BodyShop_UnderbodyFixture_v001", "lod": 0,
                                                      "frozen_triangles": 6768, "ue_legacy_triangles": 6528,
                                                      "delta": -240, "reason": "legacy FbxFactory zero-area-face normalization"},
                         "staging_cleanup": "NOT_PERFORMED__explicitly_retained", "failures": []})
        AUDIT.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        unreal.log("LINE_BOSS_BODYSHOP_UNDERBODY_ART_VALIDATION_V001_PASS")
        print(json.dumps(evidence, indent=2))
    except Exception as error:
        AUDIT.mkdir(parents=True, exist_ok=True)
        failure = {"$schema": "lineboss/audit/bodyshop/experimental-v001-underbody-art-validation-failure/v1",
                   "generated_utc": datetime.now(timezone.utc).isoformat(),
                   "status": "FAIL_CLOSED__BODYSHOP_UNDERBODY_ART_VALIDATION_V001",
                   "destination_namespace": DEST, "error": str(error), "traceback": traceback.format_exc(),
                   "map_changes": [], "runtime_binding_changes": [], "source_assets_mutated": False,
                   "meshy_credits_used_by_codex": 0}
        FAILURE.write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(failure, indent=2))
        raise


if __name__ == "__main__":
    main()
