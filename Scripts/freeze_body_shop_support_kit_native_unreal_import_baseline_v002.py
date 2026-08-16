"""Freeze the offline authority and protected-project baseline for support-kit intake.

Pure CPython only: this script never imports, starts, or controls Unreal.  It may
write only the named JSON baseline under ``Scripts`` when ``--write`` is used.
The one-shot lane runs ``--verify-existing`` immediately before Unreal starts.
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
OUTPUT = PROJECT / "Scripts/body_shop_support_kit_native_unreal_import_baseline_v002.json"
SOURCE_ROOT = PROJECT / "SourceAssets/Candidate/WeldShop/BodyShopSupportKitNative_v001"
FREEZE = SOURCE_ROOT / "Audit/FROZEN_v001.json"
MANIFEST = SOURCE_ROOT / "MANIFEST_v001.json"
GEOMETRY = SOURCE_ROOT / "Audit/geometry_inventory_v001.json"
ROUNDTRIP = SOURCE_ROOT / "Audit/roundtrip_validation_v001.json"
PROVENANCE = SOURCE_ROOT / "Audit/provenance_and_datum_contract_v001.json"

DEST_NAMESPACE = "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v001"
DEST_RELATIVE = "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v001"

EXPECTED_FINAL_SOURCE_HASHES = {
    "Audit/FROZEN_v001.json": "A4E4BF52C46F93EF5A084A708D94A7B2B920ABDC702CF655B5A8569920A9AD6F",
    "MANIFEST_v001.json": "F0EFB621EC94C0D5E4806487576E1C6AE13EE8158A68A8D445052D6F33C700EC",
    "Authority/LB_BodyShopSupportKitNative_v001.blend": "5D69E9F6D4770475BC91AD1EAC61F528EEA3F7D8C4A3979BFF6F92B5ACC60F18",
    "Audit/geometry_inventory_v001.json": "1DC636BD128CC5CA37161638F92E63DA566BE7F14A293833280643F9A4441A67",
    "Audit/roundtrip_validation_v001.json": "8933C5A746070FEB6B628786E7BD52543D96D8162CCC3B27D2BF37618D098A4A",
    "Audit/SHA256SUMS_v001.txt": "FD78070F1E68950241035ED8B4AFDA79BD94E10F43759EBCB712AA674CB3A627",
}
EXPECTED_FREEZE_STATUS = (
    "FROZEN__SOURCEASSETS_ONLY__12_NATIVE_ASSETS__36_LODS__72_EXPORT_ROUNDTRIPS_PASS__"
    "VISUAL_INSPECTION_PASS__UNREAL_IMPORT_PENDING"
)
EXPECTED_MANIFEST_STATUS = (
    "SOURCE_BUILD_PASS__12_NATIVE_ASSETS__36_LOD_MESHES__READY_FOR_ROUNDTRIP_VALIDATION__"
    "UNREAL_IMPORT_PENDING"
)
EXPECTED_GEOMETRY_STATUS = (
    "PASS__ORIGINAL_PROCEDURAL_GEOMETRY__IDENTITY_TRANSFORMS__FLOOR_PIVOTS__THREE_LODS"
)
EXPECTED_ROUNDTRIP_STATUS = (
    "PASS__AUTHORITY_AND_ALL_72_FBX_GLB_EXPORTS_ROUNDTRIP__12_ASSETS__36_LODS__CLEAN_ROOM"
)
EXPECTED_PROVENANCE_STATUS = (
    "PASS__CLEAN_ROOM_PROCEDURAL__NO_EXTERNAL_MESH_TEXTURE_IMAGE_RIG_OR_ANIMATION__SOURCEASSETS_ONLY"
)
EXPECTED_BODY_MAP_SHA256 = "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F"
EXPECTED_PRESS_V913_SHA256 = "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6"
EXPECTED_RESTORED_PRESS_MAP_SHA256 = "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5"

BODY_MAP = "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
PRESS_V913 = "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap"
RESTORED_PRESS_MAP = "Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap"
NATIVE_ROBOT_ROOT = "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001"
EXPECTED_NATIVE_ROBOT_PACKAGES = {
    NATIVE_ROBOT_ROOT + "/Robot/SM_LB_BodyShopRobotNative_Base_v001.uasset": {
        "bytes": 54559,
        "sha256": "EB7975C71866AD9531FE8EBA93CAA14EDE06CC4333CCFBF88F965DF5E52E7000",
    },
    NATIVE_ROBOT_ROOT + "/Robot/SM_LB_BodyShopRobotNative_J1_v001.uasset": {
        "bytes": 53723,
        "sha256": "50C2A7065808D59C6666D52CC44F4BDB045E0B929350D9F821E5DEF027AE54C7",
    },
    NATIVE_ROBOT_ROOT + "/Robot/SM_LB_BodyShopRobotNative_J2_v001.uasset": {
        "bytes": 43220,
        "sha256": "E6D5FA37E12B14279FE23042C940B3EF2FB33F3D6EE9D7E0D659526F5A471230",
    },
    NATIVE_ROBOT_ROOT + "/Robot/SM_LB_BodyShopRobotNative_J3_v001.uasset": {
        "bytes": 44543,
        "sha256": "02D873DD7E6688AC60DD2E4D367A78742D6524CEDF80CABA876E20FD5B2D44C5",
    },
    NATIVE_ROBOT_ROOT + "/Robot/SM_LB_BodyShopRobotNative_J4_v001.uasset": {
        "bytes": 36851,
        "sha256": "A9F887F6B8FF3955CD48FA3BF132F6F24A00DAED1765194442AD7999048E997C",
    },
    NATIVE_ROBOT_ROOT + "/Robot/SM_LB_BodyShopRobotNative_J5_v001.uasset": {
        "bytes": 36164,
        "sha256": "EE26BCDD02B6F43132B5C2CCDB8F216B01CEDFA163748E8AC05A0CF5397D116F",
    },
    NATIVE_ROBOT_ROOT + "/Robot/SM_LB_BodyShopRobotNative_J6_v001.uasset": {
        "bytes": 36605,
        "sha256": "832AC4BAD232E5BDBC1675A1E46B64BDFA4A833C5CAF1B4478A8E9492BBA0D10",
    },
    NATIVE_ROBOT_ROOT + "/Tools/SM_LB_BodyShopToolNative_OpenCGun_v001.uasset": {
        "bytes": 55603,
        "sha256": "7473FA6260B17333ABC5D2833736A657D093458CFA004DD862876096F407EFE1",
    },
}

ASSET_KEYS = (
    "PanelStillageEmpty",
    "PanelStillageFull",
    "EmptyReturnCart",
    "ComponentServicePallet",
    "SmallPartsCrate",
    "SmallPartsBin",
    "ElectricalCabinet",
    "HMIPedestal",
    "GuardPanel2m",
    "GuardGate2m",
    "UtilityPedestal",
    "ExtractionPedestal",
)

# Native source slot -> already-promoted, hash-protected Body Shop presentation material.
MATERIAL_BINDINGS = {
    "M_LB_Support_CairnwellGreen": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_EmeraldPanel_v002",
    "M_LB_Support_FoundryCharcoal": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_GraphiteTooling_v002",
    "M_LB_Support_SteelGrey": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_StructuralLightGrey_v002",
    "M_LB_Support_WarmWhite": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_CreamPaint_v002",
    "M_LB_Support_SafetyYellow": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_SafetyYellow_v002",
    "M_LB_Support_SignalRed": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_StatusRed_v002",
    "M_LB_Support_BrushedSteel": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_BrushedSteel_v002",
    "M_LB_Support_RubberBlack": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_VacuumRubber_v002",
    "M_LB_Support_ReadyAqua": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_ScannerLens_v002",
}

PROTECTED_GROUPS = (
    {"name": "project_descriptor", "files": ("LineBossCarFactory.uproject",)},
    {"name": "complete_source_tree", "roots": ("Source",)},
    {"name": "complete_config_tree", "roots": ("Config",)},
    {"name": "body_shop_map", "files": (BODY_MAP,)},
    {"name": "press_v913_map", "files": (PRESS_V913,)},
    {"name": "restored_press_map", "files": (RESTORED_PRESS_MAP,)},
    {"name": "current_native_robot_packages", "roots": (NATIVE_ROBOT_ROOT,)},
    {
        "name": "all_existing_content_outside_new_support_namespace",
        "roots": ("Content",),
        "excludes": (DEST_RELATIVE,),
    },
    {"name": "campaign_save_games", "roots": ("Saved/SaveGames",), "allow_empty": True},
)


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_SUPPORT_KIT_NATIVE_BASELINE_V002_FAIL: " + message)


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
    return {
        "path": relative(path),
        "bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256(path),
    }


def canonical_inventory_hash(rows: Iterable[dict]) -> str:
    canonical = [
        {
            "path": row["path"],
            "bytes": int(row["bytes"]),
            "mtime_ns": int(row["mtime_ns"]),
            "sha256": row["sha256"],
        }
        for row in sorted(rows, key=lambda item: item["path"].casefold())
    ]
    data = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest().upper()


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def protected_inventory() -> tuple[list[dict], list[dict]]:
    paths: dict[str, Path] = {}
    membership: dict[str, set[str]] = defaultdict(set)
    group_rows = []
    for spec in PROTECTED_GROUPS:
        selected: set[Path] = set()
        for item in spec.get("files", ()):
            selected.add(PROJECT / item)
        for item in spec.get("roots", ()):
            root = PROJECT / item
            if not root.is_dir():
                if spec.get("allow_empty"):
                    continue
                fail("protected root is missing: " + str(root))
            selected.update(path for path in root.rglob("*") if path.is_file())
        excludes = [PROJECT / item for item in spec.get("excludes", ())]
        selected = {
            path for path in selected
            if not any(path.resolve() == excluded.resolve() or is_inside(path, excluded) for excluded in excludes)
        }
        if not selected and not spec.get("allow_empty"):
            fail("protected group is empty: " + spec["name"])
        group_paths = []
        for path in sorted(selected, key=lambda item: str(item).casefold()):
            row_path = relative(path)
            paths[row_path] = path
            membership[row_path].add(spec["name"])
            group_paths.append(row_path)
        group_rows.append({
            "name": spec["name"],
            "file_count": len(group_paths),
            "paths": group_paths,
            "files": list(spec.get("files", ())),
            "roots": list(spec.get("roots", ())),
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


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as error:
        fail(f"could not parse {path}: {error}")


def asset_contract(manifest: dict, geometry: dict, frozen: dict[str, dict]) -> dict:
    if tuple(manifest.get("assets", {}).keys()) != ASSET_KEYS:
        fail("manifest asset order/inventory is not the exact frozen 12-asset set")
    if tuple(geometry.get("assets", {}).keys()) != ASSET_KEYS:
        fail("geometry asset order/inventory is not the exact frozen 12-asset set")
    output = {}
    used_materials: set[str] = set()
    for key in ASSET_KEYS:
        spec = manifest["assets"][key]
        source_lods = geometry["assets"][key]
        if list(source_lods) != ["LOD0", "LOD1", "LOD2"]:
            fail("geometry LOD inventory/order drift: " + key)
        final_name = source_lods["LOD0"]["object"]
        category = str(spec["category"])
        package_path = f"{DEST_NAMESPACE}/{category}/{final_name}"
        lod_rows = []
        lod0_slots = list(source_lods["LOD0"]["material_slots"])
        if not lod0_slots or len(lod0_slots) != len(set(lod0_slots)):
            fail("LOD0 material slots must be non-empty and unique: " + key)
        target_dimensions = [float(value) for value in spec["dimensions_m"]]
        for lod_index, lod_key in enumerate(("LOD0", "LOD1", "LOD2")):
            source = source_lods[lod_key]
            source_relative = f"Exports/{category}/{lod_key}/{source['object']}.fbx"
            source_project_relative = (
                "SourceAssets/Candidate/WeldShop/BodyShopSupportKitNative_v001/" + source_relative
            )
            frozen_row = frozen.get(source_relative)
            if frozen_row is None:
                fail("FBX is absent from source freeze: " + source_relative)
            slots = list(source["material_slots"])
            if not slots or len(slots) != len(set(slots)):
                fail("LOD material slots must be non-empty and unique: " + key + ":" + lod_key)
            if not set(slots).issubset(set(lod0_slots)):
                fail("LOD material slot is absent from LOD0 global slots: " + key + ":" + lod_key)
            used_materials.update(slots)
            transform = source["transform"]
            if transform != {
                "location": [0.0, 0.0, 0.0],
                "rotation_euler": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
            }:
                fail("source transform contract drift: " + key + ":" + lod_key)
            bounds = source["bounds"]
            minimum = [float(value) for value in bounds["minimum_m"]]
            maximum = [float(value) for value in bounds["maximum_m"]]
            dimensions = [maximum[index] - minimum[index] for index in range(3)]
            if abs(minimum[2]) > 0.00001:
                fail("source floor-pivot Z=0 contract drift: " + key + ":" + lod_key)
            if abs(minimum[0] + maximum[0]) > 0.00001 or abs(minimum[1] + maximum[1]) > 0.00001:
                fail("source XY-centred pivot contract drift: " + key + ":" + lod_key)
            if any(abs(dimensions[index] - target_dimensions[index]) > 0.00001 for index in range(3)):
                fail("source dimensions/manifest contract drift: " + key + ":" + lod_key)
            uv_layers = list(source["uv_layers"])
            if uv_layers != ["UVMap"]:
                fail("source exact one-UV-layer contract drift: " + key + ":" + lod_key)
            lod_rows.append({
                "lod": lod_index,
                "source": source_project_relative,
                "source_bytes": int(frozen_row["bytes"]),
                "source_sha256": str(frozen_row["sha256"]).upper(),
                "object_name": source["object"],
                "triangles": int(source["triangles"]),
                "source_vertices": int(source["vertices"]),
                "material_slots": slots,
                "source_bounds_m": bounds,
                "expected_unreal_bounds": expected_unreal_bounds(bounds),
                "uv_layers": uv_layers,
                "transform": transform,
            })
        triangle_chain = [row["triangles"] for row in lod_rows]
        if not (triangle_chain[0] > triangle_chain[1] > triangle_chain[2] > 0):
            fail("strict per-asset monotonic triangle contract drift: " + key + ":" + repr(triangle_chain))
        output[key] = {
            "asset_name": final_name,
            "category": category,
            "semantic_role": spec["role"],
            "wip_contract": spec["wip_contract"],
            "target_dimensions_m": target_dimensions,
            "strict_monotonic_triangles": True,
            "triangle_chain": triangle_chain,
            "package_path": package_path,
            "object_path": package_path + "." + final_name,
            "disk_path": DEST_RELATIVE + f"/{category}/{final_name}.uasset",
            "collision": {
                "shape": "AABB_BOX",
                "simple_count": 1,
                "convex_count": 0,
                "trace_flag": "CTF_USE_DEFAULT",
                "reason": (
                    "Deterministic placement/blocking hull; support props are non-enterable, and gate state "
                    "must toggle or move component collision at runtime."
                ),
            },
            "lods": lod_rows,
        }
    if used_materials != set(MATERIAL_BINDINGS):
        fail("semantic material coverage drift: " + repr(sorted(used_materials)))
    return output


def build_payload() -> dict:
    if PROJECT.resolve() != Path.cwd().resolve():
        fail("run from the exact project root: " + str(PROJECT))
    for source_relative, expected_hash in EXPECTED_FINAL_SOURCE_HASHES.items():
        actual = sha256(SOURCE_ROOT / source_relative)
        if actual != expected_hash:
            fail(f"frozen source authority hash drift: {source_relative}: {actual}")

    freeze = load_json(FREEZE)
    manifest = load_json(MANIFEST)
    geometry = load_json(GEOMETRY)
    roundtrip = load_json(ROUNDTRIP)
    provenance = load_json(PROVENANCE)
    if freeze.get("status") != EXPECTED_FREEZE_STATUS or freeze.get("counts") != {
        "assets": 12,
        "lod_meshes": 36,
        "exports": 72,
        "renders": 6,
        "frozen_files_excluding_self": 89,
    }:
        fail("exact 89-row source freeze/count gate is not present")
    if manifest.get("status") != EXPECTED_MANIFEST_STATUS:
        fail("exact source manifest gate is not present")
    if geometry.get("status") != EXPECTED_GEOMETRY_STATUS or geometry.get("gates", {}).get("status") != "PASS":
        fail("geometry gate is not PASS")
    if (roundtrip.get("status") != EXPECTED_ROUNDTRIP_STATUS
            or int(roundtrip.get("exports_tested", -1)) != 72
            or int(roundtrip.get("exports_passed", -1)) != 72
            or int(roundtrip.get("exports_failed", -1)) != 0
            or roundtrip.get("failures") != []):
        fail("72/72 FBX+GLB roundtrip gate is not PASS")
    if provenance.get("status") != EXPECTED_PROVENANCE_STATUS:
        fail("clean-room provenance gate is not PASS")

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
    if len(frozen_rows) != 89:
        fail("exact frozen-row count drift")

    source_files = [
        file_row(path)
        for path in sorted(SOURCE_ROOT.rglob("*"), key=lambda item: str(item).casefold())
        if path.is_file()
    ]
    if len(source_files) != 90:
        fail(f"exact source directory inventory drift: expected 90 files, found {len(source_files)}")
    source_relatives = {
        Path(row["path"]).relative_to(
            Path("SourceAssets/Candidate/WeldShop/BodyShopSupportKitNative_v001")
        ).as_posix()
        for row in source_files
    }
    if source_relatives - set(frozen_rows) != {"Audit/FROZEN_v001.json"}:
        fail("unexpected files outside the 89-row freeze")

    assets = asset_contract(manifest, geometry, frozen_rows)
    if sum(len(row["lods"]) for row in assets.values()) != 36:
        fail("expected exactly 36 runtime FBX LOD bindings")
    totals = {
        f"LOD{lod}": sum(asset["lods"][lod]["triangles"] for asset in assets.values())
        for lod in range(3)
    }
    if totals != {"LOD0": 20408, "LOD1": 7580, "LOD2": 1780}:
        fail("frozen aggregate triangle contract drift: " + repr(totals))

    group_rows, protected_rows = protected_inventory()
    protected_by_path = {row["path"]: row for row in protected_rows}
    if protected_by_path[BODY_MAP]["sha256"] != EXPECTED_BODY_MAP_SHA256:
        fail("protected Body Shop map hash drift")
    if protected_by_path[PRESS_V913]["sha256"] != EXPECTED_PRESS_V913_SHA256:
        fail("protected Press v913 map hash drift")
    if protected_by_path[RESTORED_PRESS_MAP]["sha256"] != EXPECTED_RESTORED_PRESS_MAP_SHA256:
        fail("protected restored full Press map hash drift")
    actual_robot_paths = {
        path for path in protected_by_path
        if path.startswith(NATIVE_ROBOT_ROOT + "/")
    }
    if actual_robot_paths != set(EXPECTED_NATIVE_ROBOT_PACKAGES):
        fail("current native robot package inventory drift: " + repr(sorted(actual_robot_paths)))
    for path, expected in EXPECTED_NATIVE_ROBOT_PACKAGES.items():
        actual = protected_by_path[path]
        if (actual["bytes"] != int(expected["bytes"])
                or actual["sha256"] != str(expected["sha256"]).upper()):
            fail("current native robot package hash/size drift: " + path)
    for package in MATERIAL_BINDINGS.values():
        disk = "Content/" + package.removeprefix("/Game/") + ".uasset"
        if disk not in protected_by_path:
            fail("bound presentation material is absent from protected inventory: " + disk)

    return {
        "$schema": "lineboss/bodyshop-support-kit-native-v001-unreal-import-baseline/v2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FROZEN__BODYSHOP_SUPPORT_KIT_NATIVE_V001_UNREAL_IMPORT_BASELINE_V002",
        "project": {
            "root": str(PROJECT),
            "uproject": "LineBossCarFactory.uproject",
            "game_name": "LineBossCarFactory",
        },
        "source": {
            "root": "SourceAssets/Candidate/WeldShop/BodyShopSupportKitNative_v001",
            "freeze_status": freeze["status"],
            "manifest_status": manifest["status"],
            "geometry_status": geometry["status"],
            "roundtrip_status": roundtrip["status"],
            "provenance_status": provenance["status"],
            "authority_hashes": EXPECTED_FINAL_SOURCE_HASHES,
            "frozen_row_count": len(frozen_rows),
            "all_source_file_count": len(source_files),
            "all_files": source_files,
            "inventory_sha256": canonical_inventory_hash(source_files),
            "triangle_totals": totals,
            "strict_per_asset_monotonic_triangles": True,
            "exact_uv_layers_per_lod": ["UVMap"],
        },
        "destination": {
            "namespace": DEST_NAMESPACE,
            "disk_path": DEST_RELATIVE,
            "expected_asset_count": 12,
            "expected_lod_count_per_asset": 3,
            "expected_package_extension": ".uasset",
            "expected_categories": ["Logistics", "Controls", "Safety", "Services"],
        },
        "import_contract": {
            "legacy_fbx_factory": True,
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
            "auto_generate_collision": False,
            "expected_uv_channels_per_lod": 1,
            "import_materials": False,
            "import_textures": False,
            "nanite_enabled": False,
            "lod_screen_sizes": [1.0, 0.45, 0.18],
            "auto_compute_lod_screen_size": False,
            "screen_size_write_order": (
                "AFTER_ALL_LOD_IMPORT_NANITE_COLLISION_MATERIAL_SAVE_AND_COMPILATION"
            ),
            "screen_size_persistence_passes": 2,
            "bounds_tolerance_cm": 0.5,
            "pivot_tolerance_cm": 0.1,
            "collision": "ONE_DETERMINISTIC_AABB_BOX_PER_ASSET__USE_DEFAULT",
            "material_policy": "IMPORT_NONE__BIND_HASH_PROTECTED_BODYSHOP_PRESENTATION_MATERIALS_V002",
            "material_bindings": MATERIAL_BINDINGS,
        },
        "assets": assets,
        "protected": {
            "body_shop_map_sha256": EXPECTED_BODY_MAP_SHA256,
            "press_v913_map_sha256": EXPECTED_PRESS_V913_SHA256,
            "restored_press_map_sha256": EXPECTED_RESTORED_PRESS_MAP_SHA256,
            "current_native_robot_packages": {
                path: protected_by_path[path]
                for path in sorted(EXPECTED_NATIVE_ROBOT_PACKAGES, key=str.casefold)
            },
            "groups": group_rows,
            "file_count": len(protected_rows),
            "files": protected_rows,
            "inventory_sha256": canonical_inventory_hash(protected_rows),
            "destination_excluded_from_existing_content_snapshot": DEST_RELATIVE,
        },
        "policy": {
            "one_shot": True,
            "replace_existing": False,
            "refuse_any_preexisting_lane_result": True,
            "automatic_failure_cleanup": False,
            "partial_assets_preserved_for_explicit_recovery": True,
            "maps_source_config_saves_and_existing_content_writable": False,
            "runtime_binding_placement_or_promotion_authorized": False,
            "unreal_or_ubt_run_by_baseline_freezer": False,
            "supersedes_disabled_provisional_lane": (
                "Scripts/run_body_shop_support_kit_native_unreal_import_lane_v001.ps1"
            ),
            "provisional_lane_files_modified": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write the pinned baseline under Scripts")
    parser.add_argument(
        "--verify-existing",
        action="store_true",
        help="read-only comparison of current source/protected files to the existing baseline",
    )
    args = parser.parse_args()
    if args.write and args.verify_existing:
        fail("--write and --verify-existing are mutually exclusive")
    destination = PROJECT / DEST_RELATIVE
    if destination.exists():
        fail("isolated destination already exists; v001 cannot be frozen or run: " + str(destination))
    payload = build_payload()
    rendered = json.dumps(payload, indent=2) + "\n"
    if args.verify_existing:
        if not OUTPUT.is_file():
            fail("existing baseline is missing: " + str(OUTPUT))
        existing = load_json(OUTPUT)
        for key in (
            "$schema", "status", "project", "source", "destination", "import_contract",
            "assets", "protected", "policy",
        ):
            if existing.get(key) != payload.get(key):
                fail("existing baseline differs from current read-only snapshot at key: " + key)
        print("PASS__BODYSHOP_SUPPORT_KIT_NATIVE_V001_BASELINE_V002_MATCHES_SOURCE_AND_PROTECTED_FILES")
        print("BASELINE_SHA256 " + sha256(OUTPUT))
    elif args.write:
        if OUTPUT.exists():
            fail("refusing to overwrite existing baseline: " + str(OUTPUT))
        OUTPUT.write_text(rendered, encoding="utf-8")
        print("WROTE " + str(OUTPUT))
        print("SHA256 " + sha256(OUTPUT))
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
