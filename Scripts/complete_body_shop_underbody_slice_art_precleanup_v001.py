"""Complete the preserved isolated Body Shop art namespace without importing or deleting assets."""
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
STAGING = DEST + "/__LegacyLODStaging"
DEST_DISK = PROJECT / "Content/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001"
AUDIT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001"
RECEIPT = AUDIT / "complete_underbody_slice_art_precleanup_receipt_v001.json"
FAILURE = AUDIT / "complete_underbody_slice_art_precleanup_failure_v001.json"
VISION = "SM_LB_BodyShop_VisionGate_v001"
NAMES = {
    "SM_LB_BodyShopRobot_Base_v001", "SM_LB_BodyShopRobot_J1_v001",
    "SM_LB_BodyShopRobot_J2_v001", "SM_LB_BodyShopRobot_J3_v001",
    "SM_LB_BodyShopRobot_J4_v001", "SM_LB_BodyShopRobot_J5_v001",
    "SM_LB_BodyShopTool_PanelPick8Cup_v001", "SM_LB_BodyShop_UnderbodyFixture_v001", VISION,
}
lib = unreal.EditorAssetLibrary


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_UNDERBODY_ART_PRECLEANUP_COMPLETION_V001_FAIL: " + message)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def disk_asset(asset_path: str) -> Path:
    return PROJECT / "Content" / Path(asset_path.replace("/Game/", "")).with_suffix(".uasset")


def content_fingerprint() -> dict:
    root = PROJECT / "Content"
    output = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            path.resolve().relative_to(DEST_DISK.resolve())
            continue
        except ValueError:
            pass
        stat = path.stat()
        output[str(path.relative_to(root)).replace("\\", "/")] = [stat.st_size, stat.st_mtime_ns]
    return output


def namespace_inventory() -> dict:
    output = {}
    if not DEST_DISK.is_dir():
        return output
    for path in DEST_DISK.rglob("*"):
        if path.is_file():
            output[str(path.relative_to(PROJECT / "Content")).replace("\\", "/")] = {
                "bytes": path.stat().st_size, "sha256": digest(path)}
    return output


def source_contract():
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("project identity drift")
    if not all(path.is_file() for path in (MANIFEST, FREEZE, ROUNDTRIP)):
        fail("source evidence missing")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    roundtrip = json.loads(ROUNDTRIP.read_text(encoding="utf-8"))
    if manifest.get("asset_id") != "LB_BODYSHOP_UNDERBODY_SLICE_ART_V001" or manifest.get("unreal_content_intent") != DEST:
        fail("manifest identity drift")
    if roundtrip.get("status") != "PASS":
        fail("roundtrip evidence drift")
    if set(manifest.get("unreal_import_bindings", {})) != NAMES:
        fail("binding inventory drift")
    return manifest, roundtrip


def frozen_inventory() -> dict:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if freeze.get("status") != "FROZEN_SOURCE_DERIVATIVE__ROUNDTRIP_PASS__UNREAL_IMPORT_PENDING":
        fail("freeze status drift")
    output = {}
    for row in freeze.get("files", []):
        path = SOURCE / row["path"]
        actual = {"bytes": path.stat().st_size, "sha256": digest(path)} if path.is_file() else None
        if not actual or actual["bytes"] != row["bytes"] or actual["sha256"] != row["sha256"].upper():
            fail("frozen source drift: " + row["path"])
        output[row["path"]] = actual
    return output


def stage_asset(name: str, lod_index: int) -> str:
    return STAGING + "/" + name + "__LegacySourceLOD" + str(lod_index)


def expected_paths(manifest: dict):
    finals = {}
    staging = {}
    for name, binding in manifest["unreal_import_bindings"].items():
        final = binding["object_path"].rsplit(".", 1)[0]
        finals[name] = final
        for lod_index in (1, 2):
            staging[(name, lod_index)] = stage_asset(name, lod_index)
    return finals, staging


def assert_precise_preserved_namespace(finals: dict, staging: dict) -> None:
    expected = set(finals.values()) | set(staging.values())
    # AssetRegistry returns object paths ("/Game/Foo/SM_Name.SM_Name") while
    # the frozen manifest deliberately records package paths ("/Game/Foo/SM_Name").
    registry = {str(path).rsplit(".", 1)[0]
                for path in lib.list_assets(DEST, recursive=True, include_folder=False)}
    if registry != expected:
        fail("preserved registry inventory drift: " + str(sorted(registry)))
    expected_disk = {str(disk_asset(asset).relative_to(PROJECT / "Content")).replace("\\", "/") for asset in expected}
    actual_disk = set(namespace_inventory())
    if actual_disk != expected_disk:
        fail("preserved disk inventory drift: " + str(sorted(actual_disk)))


def exact_import_data(mesh, name: str) -> dict:
    data = mesh.get_editor_property("asset_import_data")
    try:
        value = {"import_uniform_scale": float(data.get_editor_property("import_uniform_scale")),
                 "transform_vertex_to_absolute": bool(data.get_editor_property("transform_vertex_to_absolute")),
                 "remove_degenerates": bool(data.get_editor_property("remove_degenerates"))}
    except Exception as error:
        fail("legacy import-data unavailable: " + name + ":" + str(error))
    if value != {"import_uniform_scale": 1.0, "transform_vertex_to_absolute": True, "remove_degenerates": False}:
        fail("legacy import-data policy drift: " + name + ":" + str(value))
    return value


def material_slots(mesh, name: str) -> list:
    output = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        material = mesh.get_material(index)
        path = material.get_path_name() if material else None
        if path and path.startswith(DEST + "/"):
            fail("unexpected material package created: " + name + ":" + path)
        output.append({"index": index, "slot": str(slot.get_editor_property("material_slot_name")), "material": path})
    return output


def configure_final(mesh, name: str, subsystem) -> dict:
    if not isinstance(mesh, unreal.StaticMesh):
        fail("final is not a static mesh: " + name)
    if int(mesh.get_num_lods()) != 3:
        fail("final LOD count before policy configuration is not 3: " + name)
    if not subsystem.set_lod_screen_sizes(mesh, [1.0, 0.55, 0.25]):
        fail("unable to set LOD screens: " + name)
    nanite = subsystem.get_nanite_settings(mesh)
    nanite.set_editor_property("enabled", False)
    subsystem.set_nanite_settings(mesh, nanite, True)
    body = mesh.get_editor_property("body_setup")
    if not body:
        fail("body setup missing: " + name)
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
    if not lib.save_loaded_asset(mesh, only_if_is_dirty=False):
        fail("final mesh save failed: " + name)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    simple = int(subsystem.get_simple_collision_count(mesh))
    convex = int(subsystem.get_convex_collision_count(mesh))
    enabled = bool(subsystem.get_nanite_settings(mesh).get_editor_property("enabled"))
    trace = str(body.get_editor_property("collision_trace_flag"))
    if simple or convex or enabled or "SIMPLE_AS_COMPLEX" not in trace.upper():
        fail("collision/Nanite policy drift after configuration: " + name)
    return {"lod_count": int(mesh.get_num_lods()),
            "render_triangles": [int(mesh.get_num_triangles(index)) for index in range(3)],
            "simple_collision_count": simple, "convex_collision_count": convex,
            "collision_trace_flag": trace, "nanite_enabled": enabled,
            "legacy_import_data": exact_import_data(mesh, name), "material_slots": material_slots(mesh, name)}


def main() -> None:
    before_content = content_fingerprint()
    evidence = {"$schema": "lineboss/audit/bodyshop/experimental-v001-underbody-art-precleanup-completion/v1",
                "generated_utc": now(), "destination_namespace": DEST, "map_changes": [],
                "runtime_binding_changes": [], "source_assets_mutated": False,
                "meshy_credits_used_by_codex": 0, "new_fbx_imports": 0,
                "staging_cleanup": "NOT_PERFORMED__explicitly_retained_for_precleanup_validation"}
    try:
        manifest, roundtrip = source_contract()
        frozen_before = frozen_inventory()
        finals, staging = expected_paths(manifest)
        assert_precise_preserved_namespace(finals, staging)
        staging_before = {key: value for key, value in namespace_inventory().items()
                          if "/__LegacyLODStaging/" in key}
        vision = lib.load_asset(finals[VISION])
        if not isinstance(vision, unreal.StaticMesh) or int(vision.get_num_lods()) != 1:
            fail("Vision final is not the expected uncompleted LOD0-only mesh")
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        if subsystem is None:
            fail("StaticMeshEditorSubsystem unavailable")
        for lod_index in (1, 2):
            source = lib.load_asset(staging[(VISION, lod_index)])
            expected_object = staging[(VISION, lod_index)] + "." + staging[(VISION, lod_index)].rsplit("/", 1)[-1]
            if not isinstance(source, unreal.StaticMesh) or source.get_path_name() != expected_object:
                fail("Vision legacy staging source drift: LOD" + str(lod_index))
            if int(source.get_num_lods()) != 1:
                fail("Vision legacy staging LOD count drift: LOD" + str(lod_index))
            if subsystem.set_lod_from_static_mesh(vision, lod_index, source, 0, True) != lod_index:
                fail("Vision legacy LOD transfer failed: LOD" + str(lod_index))
            unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        if int(vision.get_num_lods()) != 3:
            fail("Vision did not receive exactly 3 LODs")
        finals_after = {}
        for name in sorted(finals):
            mesh = lib.load_asset(finals[name])
            finals_after[name] = configure_final(mesh, name, subsystem)
        staging_after = {key: value for key, value in namespace_inventory().items()
                         if "/__LegacyLODStaging/" in key}
        if staging_after != staging_before:
            fail("staging package hash drift during final completion")
        assert_precise_preserved_namespace(finals, staging)
        if content_fingerprint() != before_content:
            fail("Content outside isolated destination changed")
        frozen_after = frozen_inventory()
        if frozen_after != frozen_before:
            fail("frozen source changed during completion")
        namespace_after = namespace_inventory()
        final_packages = {key: value for key, value in namespace_after.items() if "/__LegacyLODStaging/" not in key}
        evidence.update({"status": "PASS__BODYSHOP_UNDERBODY_ART_PRECLEANUP_FINALS_COMPLETED_V001",
                         "source_manifest_sha256": digest(MANIFEST), "freeze_manifest_sha256": digest(FREEZE),
                         "roundtrip_report_sha256": digest(ROUNDTRIP), "frozen_source_hashes_before": frozen_before,
                         "frozen_source_hashes_after": frozen_after, "vision_lods_attached_from_existing_legacy_staging": [1, 2],
                         "final_meshes": finals_after, "final_asset_packages": final_packages,
                         "staging_asset_packages_before_and_after_identical": staging_after,
                         "final_asset_count": len(final_packages), "staging_asset_count": len(staging_after),
                         "unintended_content_mutations": [], "failures": []})
        AUDIT.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        unreal.log("LINE_BOSS_BODYSHOP_UNDERBODY_ART_PRECLEANUP_COMPLETION_V001_PASS")
        print(json.dumps(evidence, indent=2))
    except Exception as error:
        AUDIT.mkdir(parents=True, exist_ok=True)
        failure = {"$schema": "lineboss/audit/bodyshop/experimental-v001-underbody-art-precleanup-completion-failure/v1",
                   "generated_utc": now(), "status": "FAIL_CLOSED__BODYSHOP_UNDERBODY_ART_PRECLEANUP_COMPLETION_V001",
                   "destination_namespace": DEST, "error": str(error), "traceback": traceback.format_exc(),
                   "namespace_files_preserved_for_inspection": namespace_inventory(),
                   "outside_content_changed": content_fingerprint() != before_content,
                   "automatic_cleanup": "NOT_PERFORMED__staging explicitly retained", "map_changes": [],
                   "runtime_binding_changes": [], "source_assets_mutated": False, "meshy_credits_used_by_codex": 0,
                   "new_fbx_imports": 0}
        FAILURE.write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(failure, indent=2))
        raise


if __name__ == "__main__":
    main()
