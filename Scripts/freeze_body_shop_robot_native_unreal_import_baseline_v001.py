"""Freeze the offline authority and protected-file baseline for the v001 robot intake.

This script is deliberately pure CPython: it does not import or launch Unreal.  It
may only write the JSON baseline under Scripts.  The import and validation lanes
pin the resulting JSON by SHA-256 and refuse to run against a regenerated file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUTPUT = PROJECT / "Scripts/body_shop_robot_native_unreal_import_baseline_v001.json"
SOURCE_ROOT = PROJECT / "SourceAssets/Candidate/WeldShop/BodyShopRobotNative_v001"
FREEZE = SOURCE_ROOT / "Audit/FROZEN_v001.json"
MANIFEST = SOURCE_ROOT / "MANIFEST_v001.json"
GEOMETRY = SOURCE_ROOT / "Audit/geometry_inventory_v001.json"
ROUNDTRIP = SOURCE_ROOT / "Audit/roundtrip_validation_v001.json"
CONTACT = SOURCE_ROOT / "Audit/contact_fk_validation_v001.json"

DEST_NAMESPACE = "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001"
DEST_RELATIVE = "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001"

EXPECTED_FINAL_SOURCE_HASHES = {
    "Audit/FROZEN_v001.json": "C11F95D4EC8B57C2D2D89AD63D44589C8A46FF0A6169DD37E733A25C0AA7C3CB",
    "MANIFEST_v001.json": "2797633628F0D295850A62319BB4D3E84ABA87BEB3C2B303C26FE7E17DBF1D4E",
    "Authority/LB_BodyShopRobotNative_v001.blend": "91DC4262FEA06C63B49A2E457ACB30F2E70576CEC92B2EA4D6FF2FC7F7C55E3B",
    "Audit/contact_fk_validation_v001.json": "29A0DCB9EF64191E7558B9E79562540CF1DFC98F1BC7D95CDAC25D3B4F6FA963",
    "Audit/geometry_inventory_v001.json": "8B334351E194F61033F269FBFB2BF45686AD4A3AC28C58536A04E2E3A1B61E82",
    "Audit/roundtrip_validation_v001.json": "FA784FB2D05781CDD5DA54D5E168225CB0D000A48E6F5CCCECB3A6E1F84CE9DB",
}
EXPECTED_FREEZE_STATUS = (
    "FROZEN__HIGH_ELBOW__STRICT_MONOTONIC_LODS__ONE_UV_LAYER__SOURCEASSETS_ONLY__"
    "50_EXPORT_ROUNDTRIPS_PASS__UNREAL_IMPORT_PENDING"
)
EXPECTED_MANIFEST_STATUS = (
    "SOURCE_BUILD_PASS__HIGH_ELBOW__STRICT_MONOTONIC_LODS__ONE_UV_LAYER__"
    "FK_CONTACT_CLEARANCE_PASS__READY_FOR_ISOLATED_UNREAL_IMPORT__NOT_PROMOTED"
)
EXPECTED_CONTACT_STATUS = "PASS__NATIVE_SIX_AXIS_HIGH_ELBOW_MIRRORED_CONTACT_AND_CLEARANCE"
EXPECTED_ROUNDTRIP_STATUS = "PASS__ALL_50_FBX_GLB_EXPORTS_ROUNDTRIP__STRICT_MONOTONIC_LODS__ONE_UV_LAYER"
EXPECTED_GEOMETRY_STATUS = (
    "PASS__ORIGINAL_PROCEDURAL_LOW_POLY__STRICT_PER_ASSET_MONOTONIC_LODS__"
    "ONE_UV_LAYER__SEMANTIC_MATERIALS"
)
EXPECTED_BODY_MAP_SHA256 = "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F"
EXPECTED_PRESS_V913_SHA256 = "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6"

BODY_MAP = "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
PRESS_V913 = "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap"

MATERIAL_BINDINGS = {
    "M_LB_BS_BlackMotor": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_BlackMotor_v002",
    "M_LB_BS_BrushedSteel": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_BrushedSteel_v002",
    "M_LB_BS_CreamPaint": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_CreamPaint_v002",
    "M_LB_BS_EmeraldPanel": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_EmeraldPanel_v002",
    "M_LB_BS_GraphiteTooling": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_GraphiteTooling_v002",
    "M_LB_BS_SafetyYellow": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_SafetyYellow_v002",
    "M_LB_BS_StructuralLightGrey": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_StructuralLightGrey_v002",
}

PROTECTED_GROUPS = (
    {"name": "project_descriptor", "files": ("LineBossCarFactory.uproject",)},
    {"name": "press_v913_map", "files": (PRESS_V913,)},
    {"name": "body_shop_map", "files": (BODY_MAP,)},
    {"name": "config_tree", "roots": ("Config",)},
    {"name": "body_shop_existing_content", "roots": ("Content/LineBoss/BodyShop",)},
    {
        "name": "weld_shop_existing_promoted_and_meshed_content",
        "roots": ("Content/LineBoss/Candidates/WeldShop",),
        "excludes": (DEST_RELATIVE,),
    },
    {"name": "complete_source_tree", "roots": ("Source",)},
    {"name": "save_games", "globs": ("Saved/SaveGames/*.sav",), "allow_empty": True},
)


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_ROBOT_NATIVE_BASELINE_V001_FAIL: " + message)


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT.resolve()).as_posix()


def file_row(path: Path) -> dict:
    if not path.is_file():
        fail("required file is missing: " + str(path))
    stat = path.stat()
    return {"path": relative(path), "bytes": stat.st_size, "sha256": sha256(path)}


def canonical_inventory_hash(rows: Iterable[dict]) -> str:
    canonical = [
        {"path": row["path"], "bytes": int(row["bytes"]), "sha256": row["sha256"]}
        for row in sorted(rows, key=lambda item: item["path"].casefold())
    ]
    data = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest().upper()


def is_inside(path: Path, candidate_parent: Path) -> bool:
    try:
        path.resolve().relative_to(candidate_parent.resolve())
        return True
    except ValueError:
        return False


def protected_inventory() -> tuple[list[dict], list[dict]]:
    membership: dict[str, set[str]] = defaultdict(set)
    paths: dict[str, Path] = {}
    group_rows = []
    for spec in PROTECTED_GROUPS:
        name = spec["name"]
        selected: set[Path] = set()
        for item in spec.get("files", ()):
            selected.add(PROJECT / item)
        for root_name in spec.get("roots", ()):
            root = PROJECT / root_name
            if not root.is_dir():
                fail(f"protected root is missing for {name}: {root}")
            selected.update(path for path in root.rglob("*") if path.is_file())
        for pattern in spec.get("globs", ()):
            selected.update(path for path in PROJECT.glob(pattern) if path.is_file())
        excludes = [PROJECT / item for item in spec.get("excludes", ())]
        selected = {path for path in selected if not any(is_inside(path, excluded) for excluded in excludes)}
        if not selected and not spec.get("allow_empty", False):
            fail("protected group is unexpectedly empty: " + name)
        group_paths = []
        for path in sorted(selected, key=lambda item: str(item).casefold()):
            row_path = relative(path)
            paths[row_path] = path
            membership[row_path].add(name)
            group_paths.append(row_path)
        group_rows.append({
            "name": name,
            "file_count": len(group_paths),
            "paths": group_paths,
            "files": list(spec.get("files", ())),
            "roots": list(spec.get("roots", ())),
            "globs": list(spec.get("globs", ())),
            "excludes": list(spec.get("excludes", ())),
            "allow_empty": bool(spec.get("allow_empty", False)),
        })
    rows = []
    for row_path in sorted(paths, key=str.casefold):
        row = file_row(paths[row_path])
        row["groups"] = sorted(membership[row_path])
        rows.append(row)
    return group_rows, rows


def expected_unreal_bounds(source_bounds: dict) -> dict:
    minimum = [float(value) for value in source_bounds["minimum_m"]]
    maximum = [float(value) for value in source_bounds["maximum_m"]]
    # Blender/FBX is right-handed; UE's FBX scene conversion reflects local Y.
    ue_min = [minimum[0] * 100.0, -maximum[1] * 100.0, minimum[2] * 100.0]
    ue_max = [maximum[0] * 100.0, -minimum[1] * 100.0, maximum[2] * 100.0]
    return {
        "minimum_cm": [round(value, 6) for value in ue_min],
        "maximum_cm": [round(value, 6) for value in ue_max],
        "dimensions_cm": [round(ue_max[index] - ue_min[index], 6) for index in range(3)],
        "pivot_cm": [0.0, 0.0, 0.0],
    }


def asset_contract(geometry: dict, freeze_by_source_relative: dict) -> dict:
    expected_keys = {"Base", "CGun", "J1", "J2", "J3", "J4", "J5", "J6"}
    if set(geometry.get("assets", {})) != expected_keys:
        fail("geometry asset inventory is not the exact Base/J1-J6/CGun set")
    output = {}
    for key in sorted(expected_keys):
        source_lods = geometry["assets"][key]
        if list(source_lods) != ["LOD0", "LOD1", "LOD2"]:
            fail("geometry LOD inventory/order drift: " + key)
        final_name = source_lods["LOD0"]["object"]
        folder = "Tools" if key == "CGun" else "Robot"
        package_path = f"{DEST_NAMESPACE}/{folder}/{final_name}"
        lod_rows = []
        for lod_index, lod_key in enumerate(("LOD0", "LOD1", "LOD2")):
            source = source_lods[lod_key]
            source_relative = "Exports/" + source["object"] + ".fbx"
            source_project_relative = "SourceAssets/Candidate/WeldShop/BodyShopRobotNative_v001/" + source_relative
            frozen = freeze_by_source_relative.get(source_relative)
            if frozen is None:
                fail("FBX is absent from the source freeze: " + source_relative)
            lod_rows.append({
                "lod": lod_index,
                "source": source_project_relative,
                "source_bytes": int(frozen["bytes"]),
                "source_sha256": str(frozen["sha256"]).upper(),
                "object_name": source["object"],
                "triangles": int(source["triangles"]),
                "source_vertices": int(source["vertices"]),
                "source_uv_layers": int(source["uv_layers"]),
                "source_uv_layer_names": list(source["uv_layer_names"]),
                "material_slots": list(source["materials"]),
                "source_bounds_m": source["bounds_local"],
                "expected_unreal_bounds": expected_unreal_bounds(source["bounds_local"]),
                "source_scale": [float(value) for value in source["scale"]],
                "source_rotation_euler_degrees": [float(value) for value in source["rotation_euler_degrees"]],
            })
        output[key] = {
            "asset_name": final_name,
            "package_path": package_path,
            "object_path": package_path + "." + final_name,
            "disk_path": DEST_RELATIVE + f"/{folder}/{final_name}.uasset",
            "lods": lod_rows,
        }
    return output


def active_body_shop_binding_contract(assets: dict) -> dict:
    source_root = PROJECT / "Source/LineBossCarFactory"
    active_files = sorted(
        {
            *source_root.glob("LBBodyShop*.h"),
            *source_root.glob("LBBodyShop*.cpp"),
        },
        key=lambda item: str(item).casefold(),
    )
    if not active_files:
        fail("active Body Shop source binding inventory is empty")
    forbidden = "WeldRobotRuntime_v001"
    forbidden_matches = []
    for path in active_files:
        for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
            if forbidden in line:
                forbidden_matches.append({"path": relative(path), "line": line_number})
    if forbidden_matches:
        fail("old WeldRobotRuntime_v001 path remains in active Body Shop binding: " + repr(forbidden_matches))

    actor_path = source_root / "LBBodyShopRobotActor.cpp"
    if not actor_path.is_file():
        fail("active LBBodyShopRobotActor.cpp binding authority is missing")
    actor_text = actor_path.read_text(encoding="utf-8-sig")
    required_objects = [assets[key]["object_path"] for key in ("Base", "J1", "J2", "J3", "J4", "J5", "J6", "CGun")]
    missing = [path for path in required_objects if path not in actor_text]
    if missing:
        fail("LBBodyShopRobotActor.cpp is missing native v001 object paths: " + repr(missing))
    return {
        "status": "PASS__ACTIVE_BODYSHOP_BINDINGS_USE_ONLY_NATIVE_V001_ROBOT_AND_OPEN_CGUN",
        "scanned_files": [relative(path) for path in active_files],
        "forbidden_old_runtime_token": forbidden,
        "forbidden_matches": [],
        "binding_authority": relative(actor_path),
        "required_object_paths": required_objects,
        "missing_required_object_paths": [],
        "archived_legacy_scope_not_semantically_rejected": [
            "Source/LineBossCarFactory/LBBodyWeldLineActor.cpp",
            "Source/LineBossCarFactory/LBBodyWeldLineActor.h",
            "Source/LineBossCarFactory/LBBodyWeldLineActorTests.cpp",
        ],
        "archived_weld_robot_packages_preserved_by_protected_hashes": True,
    }


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as error:
        fail(f"could not parse {path}: {error}")


def build_payload() -> dict:
    if PROJECT.resolve() != Path.cwd().resolve():
        fail(f"run from the exact project root: {PROJECT}")
    for source_relative, expected_hash in EXPECTED_FINAL_SOURCE_HASHES.items():
        actual = sha256(SOURCE_ROOT / source_relative)
        if actual != expected_hash:
            fail(f"final high-elbow authority hash drift: {source_relative}: {actual}")

    freeze = load_json(FREEZE)
    manifest = load_json(MANIFEST)
    geometry = load_json(GEOMETRY)
    roundtrip = load_json(ROUNDTRIP)
    contact = load_json(CONTACT)
    if freeze.get("status") != EXPECTED_FREEZE_STATUS or len(freeze.get("files", [])) != 63:
        fail("exact revised 63-file freeze/status gate is not present")
    if manifest.get("status") != EXPECTED_MANIFEST_STATUS:
        fail("exact revised high-elbow source manifest gate is not present")
    if geometry.get("status") != EXPECTED_GEOMETRY_STATUS:
        fail("geometry gate is not PASS")
    monotonic = geometry.get("strict_per_asset_lod_monotonicity", {})
    uv_contract = geometry.get("uv_contract", {})
    transform_gate = geometry.get("transform_gate", {})
    expected_assets = {"Base", "CGun", "J1", "J2", "J3", "J4", "J5", "J6"}
    if (monotonic.get("contract") != "LOD0_TRIANGLES_GT_LOD1_TRIANGLES_GT_LOD2_TRIANGLES"
            or monotonic.get("all_pass") is not True
            or set(monotonic.get("assets", {})) != expected_assets
            or not all(value is True for value in monotonic.get("assets", {}).values())):
        fail("strict per-asset LOD monotonicity gate is not PASS")
    if (uv_contract.get("expected_layers_per_asset_lod") != 1
            or uv_contract.get("all_pass") is not True):
        fail("exact one-UV-layer geometry gate is not PASS")
    if (transform_gate.get("all_scales_one") is not True
            or transform_gate.get("standalone_origins_clean") is not True):
        fail("source transform/pivot gate is not PASS")
    manifest_lod = manifest.get("lod_contract", {})
    if (manifest_lod.get("per_asset_triangle_order") != "LOD0_GT_LOD1_GT_LOD2"
            or manifest_lod.get("all_assets_pass") is not True
            or manifest_lod.get("uv_layers_per_asset_lod") != 1):
        fail("manifest strict LOD/UV contract is not PASS")
    if (roundtrip.get("status") != EXPECTED_ROUNDTRIP_STATUS
            or int(roundtrip.get("exports_tested", -1)) != 50
            or int(roundtrip.get("passed", -1)) != 50
            or int(roundtrip.get("failed", -1)) != 0):
        fail("50/50 FBX+GLB roundtrip gate is not PASS")
    summary = contact.get("contact_summary", {})
    elbow = contact.get("high_elbow_visual_gate", {})
    clearance = contact.get("clearance_proxy", {})
    if (contact.get("status") != EXPECTED_CONTACT_STATUS
            or summary.get("samples") != 18 or summary.get("passed") != 18
            or float(summary.get("maximum_distance_cm", 1e9)) > 10.0001
            or float(summary.get("minimum_direction_dot", -1.0)) < 0.9999999
            or elbow.get("gate") != "PASS"
            or float(elbow.get("minimum_elbow_rise_above_shoulder_cm", -1.0)) < 45.0
            or float(elbow.get("minimum_centre_process_elbow_height_above_wrist_cm", -1.0)) < 20.0
            or clearance.get("gate") != "PASS"
            or float(clearance.get("minimum_floor_clearance_cm", -1.0)) < 64.0):
        fail("revised 18/18 high-elbow contact/clearance gate is not PASS")

    frozen_rows = {}
    for row in freeze["files"]:
        source_relative = str(row["path"]).replace("\\", "/")
        if source_relative in frozen_rows:
            fail("duplicate path in FROZEN_v001: " + source_relative)
        path = SOURCE_ROOT / source_relative
        actual = file_row(path)
        if actual["bytes"] != int(row["bytes"]) or actual["sha256"] != str(row["sha256"]).upper():
            fail("frozen source row drift: " + source_relative)
        frozen_rows[source_relative] = row

    source_files = [file_row(path) for path in sorted(SOURCE_ROOT.rglob("*"), key=lambda item: str(item).casefold()) if path.is_file()]
    if len(source_files) != 66:
        fail(f"exact revised source directory inventory drift: expected 66 files, found {len(source_files)}")
    source_relatives = {
        Path(row["path"]).relative_to(Path("SourceAssets/Candidate/WeldShop/BodyShopRobotNative_v001")).as_posix()
        for row in source_files
    }
    freeze_excluded = sorted(source_relatives - set(frozen_rows) - {"Audit/FROZEN_v001.json"})
    if freeze_excluded != [
            "Audit/SupersededEvidence/pre_monotonic_blender_generation_stdout.log",
            "Audit/blender_generation_stderr.log",
    ]:
        fail("unexpected files outside the 63-row freeze: " + repr(freeze_excluded))

    assets = asset_contract(geometry, frozen_rows)
    active_binding = active_body_shop_binding_contract(assets)
    if sum(len(row["lods"]) for row in assets.values()) != 24:
        fail("expected exactly 24 runtime FBX LOD bindings")
    if geometry.get("lod_triangle_totals") != {"LOD0": 2628, "LOD1": 1964, "LOD2": 1356}:
        fail("frozen aggregate triangle contract drift")
    for key, asset in assets.items():
        triangles = [row["triangles"] for row in asset["lods"]]
        if not triangles[0] > triangles[1] > triangles[2]:
            fail(f"strict triangle monotonicity drift in asset contract: {key}: {triangles}")
        if any(row["source_uv_layers"] != 1 or row["source_uv_layer_names"] != ["UVMap"]
               for row in asset["lods"]):
            fail("source UV contract drift in asset: " + key)
    used_materials = set(geometry.get("semantic_materials_used", []))
    if not used_materials or not used_materials.issubset(MATERIAL_BINDINGS):
        fail("semantic material binding coverage drift")

    group_rows, protected_rows = protected_inventory()
    protected_by_path = {row["path"]: row for row in protected_rows}
    if protected_by_path[BODY_MAP]["sha256"] != EXPECTED_BODY_MAP_SHA256:
        fail("protected Body Shop map hash drift")
    if protected_by_path[PRESS_V913]["sha256"] != EXPECTED_PRESS_V913_SHA256:
        fail("protected Press v913 map hash drift")
    for package in MATERIAL_BINDINGS.values():
        disk = "Content/" + package.removeprefix("/Game/") + ".uasset"
        if disk not in protected_by_path:
            fail("bound presentation material is absent from protected inventory: " + disk)

    return {
        "$schema": "lineboss/bodyshop-robot-native-v001-unreal-import-baseline/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FROZEN__HIGH_ELBOW_STRICT_MONOTONIC_BODYSHOP_ROBOT_NATIVE_V001_CLEAN_UNREAL_IMPORT_BASELINE",
        "project": {
            "root": str(PROJECT),
            "uproject": "LineBossCarFactory.uproject",
            "game_name": "LineBossCarFactory",
        },
        "source": {
            "root": "SourceAssets/Candidate/WeldShop/BodyShopRobotNative_v001",
            "freeze_status": freeze["status"],
            "manifest_status": manifest["status"],
            "contact_status": contact["status"],
            "roundtrip_status": roundtrip["status"],
            "authority_hashes": EXPECTED_FINAL_SOURCE_HASHES,
            "frozen_row_count": len(frozen_rows),
            "all_source_file_count": len(source_files),
            "freeze_excluded_but_baseline_pinned": freeze_excluded,
            "all_files": source_files,
            "inventory_sha256": canonical_inventory_hash(source_files),
            "high_elbow_gate": elbow,
            "contact_summary": summary,
            "clearance_proxy": clearance,
        },
        "destination": {
            "namespace": DEST_NAMESPACE,
            "disk_path": DEST_RELATIVE,
            "expected_asset_count": 8,
            "expected_lod_count_per_asset": 3,
            "expected_package_extension": ".uasset",
        },
        "import_contract": {
            "legacy_fbx_factory": True,
            "fresh_destination_only": True,
            "custom_lod_route": "LEGACY_FBX_WITH_INTERCHANGE_FEATURE_FLAG_TEMPORARILY_DISABLED",
            "interchange_fbx_cvar": "Interchange.FeatureFlags.Import.FBX",
            "interchange_previous_value_captured_and_restored_in_finally": True,
            "source_units": "metres",
            "unreal_units": "centimetres",
            "import_uniform_scale": 1.0,
            "convert_scene": True,
            "convert_scene_unit": True,
            "force_front_x_axis": False,
            "transform_vertex_to_absolute": True,
            "bake_pivot_in_vertex": False,
            "remove_degenerates": False,
            "generate_lightmap_uvs": False,
            "expected_uv_channels_per_lod": 1,
            "strict_per_asset_triangle_order": "LOD0_GT_LOD1_GT_LOD2",
            "import_materials": False,
            "import_textures": False,
            "nanite_enabled": False,
            "lod_screen_sizes": [1.0, 0.55, 0.25],
            "auto_compute_lod_screen_size": False,
            "screen_size_write_order": "AFTER_ALL_LOD_IMPORT_NANITE_COLLISION_MATERIAL_SAVE_AND_COMPILATION",
            "screen_size_persistence_passes": 2,
            "bounds_tolerance_cm": 0.5,
            "collision": "ZERO_SIMPLE_OR_CONVEX_PRIMITIVES__SIMPLE_AS_COMPLEX__PRESENTATION_ONLY",
            "material_bindings": MATERIAL_BINDINGS,
        },
        "assets": assets,
        "active_body_shop_binding": active_binding,
        "protected": {
            "body_shop_map_sha256": EXPECTED_BODY_MAP_SHA256,
            "press_v913_map_sha256": EXPECTED_PRESS_V913_SHA256,
            "groups": group_rows,
            "file_count": len(protected_rows),
            "files": protected_rows,
            "inventory_sha256": canonical_inventory_hash(protected_rows),
            "destination_excluded_from_weld_shop_snapshot": DEST_RELATIVE,
        },
        "policy": {
            "one_shot": True,
            "replace_existing": False,
            "fresh_import_after_hash_guarded_archive_and_atomic_recoverable_namespace_move": True,
            "failed_runs_required_for_archive": 2,
            "invalid_packages_required_for_copy_and_move": 8,
            "destination_must_be_absent_before_unreal_launch": True,
            "automatic_failure_cleanup": False,
            "partial_assets_preserved_in_saved_audits_recovery_archive": True,
            "content_packages_deleted": False,
            "maps_source_config_and_existing_content_writable": False,
            "runtime_binding_or_promotion_authorized": False,
            "unreal_or_ubt_run_by_baseline_freezer": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write the pinned baseline JSON under Scripts")
    parser.add_argument(
        "--verify-existing", action="store_true",
        help="read-only comparison of current source/protected files to the existing baseline",
    )
    args = parser.parse_args()
    payload = build_payload()
    rendered = json.dumps(payload, indent=2) + "\n"
    if args.write and args.verify_existing:
        fail("--write and --verify-existing are mutually exclusive")
    if args.verify_existing:
        if not OUTPUT.is_file():
            fail("existing baseline is missing: " + str(OUTPUT))
        existing = load_json(OUTPUT)
        for key in ("$schema", "status", "project", "source", "destination", "import_contract", "assets", "active_body_shop_binding", "protected", "policy"):
            if existing.get(key) != payload.get(key):
                fail("existing baseline differs from current read-only snapshot at key: " + key)
        print("PASS__BODYSHOP_ROBOT_NATIVE_V001_EXISTING_BASELINE_MATCHES_SOURCE_AND_PROTECTED_FILES")
        print("BASELINE_SHA256 " + sha256(OUTPUT))
    elif args.write:
        OUTPUT.write_text(rendered, encoding="utf-8")
        print(f"WROTE {OUTPUT}")
        print(f"SHA256 {sha256(OUTPUT)}")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
