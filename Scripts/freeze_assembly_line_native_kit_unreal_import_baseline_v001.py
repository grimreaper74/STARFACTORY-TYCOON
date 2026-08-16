"""Freeze the one-shot Unreal intake baseline for the native Assembly kit.

Offline only.  The sole authorized write is a previously absent baseline JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUTPUT = PROJECT / "Scripts/assembly_line_native_kit_unreal_import_baseline_v001.json"
SOURCE_ROOT = PROJECT / "SourceAssets/Candidate/AssemblyShop/AssemblyLineNativeKit_v001"
DEST_NAMESPACE = "/Game/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001"
DEST_RELATIVE = "Content/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001"
AUDIT_RELATIVE = "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/UnrealImportLane_v001"

AUTHORITIES = {
    "MANIFEST_v001.json": "CB3653EDAFCBA00D6E20F6D1053A884911B428616BB2554C722C36DA968A35AB",
    "Audit/FROZEN_v001.json": "EC2DF8EDF41492D9D1B956322DF65D30C9CFA7FFBAC3C8CBAFCAFE468E8D3363",
    "Audit/geometry_inventory_v001.json": "A6D67F7697C931028E7E43A8589DC62E4DA559E538BDD101B1D953F2005F08C0",
    "Audit/roundtrip_validation_v001.json": "A5E23D80410F67B4D0E31E6137D2887BC42E50F479E6F945468FD720CFFD1D07",
    "Audit/SHA256SUMS_v001.txt": "D83617E184551393411E6A737211E16C3223ABCC5B6E6F859A1251E316AF3D5F",
    "Authority/LB_AssemblyLineNativeKit_v001.blend": "9F1F8C9B568064A5783FC78F54A7AFB67985E17A20533C7F68900CD9EC6BA3CA",
}
ASSET_KEYS = (
    "SkilletCarrier", "SequencedPartsCart", "WheelTireRack", "CockpitInstallAssist",
    "HeavyMarriageGantry", "ErgonomicLiftPlatform", "WheelAlignmentBed", "EOLInspectionArch",
)
COMPLEX_COLLISION = {"CockpitInstallAssist", "HeavyMarriageGantry", "EOLInspectionArch"}
MATERIAL_BINDINGS = {
    "M_LB_Assembly_CairnwellGreen": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_EmeraldPanel_v002",
    "M_LB_Assembly_FoundryCharcoal": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_GraphiteTooling_v002",
    "M_LB_Assembly_SteelGrey": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_StructuralLightGrey_v002",
    "M_LB_Assembly_WarmWhite": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_CreamPaint_v002",
    "M_LB_Assembly_SafetyYellow": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_SafetyYellow_v002",
    "M_LB_Assembly_BrushedSteel": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_BrushedSteel_v002",
    "M_LB_Assembly_RubberBlack": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_VacuumRubber_v002",
    "M_LB_Assembly_ReadyAqua": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_ScannerLens_v002",
}
MAPS = {
    "press_v913": "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap",
    "restored_press": "Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap",
    "body": "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap",
    "paint": "Content/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001.umap",
    "one_factory": "Content/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001.umap",
}
EXPECTED_MAP_HASHES = {
    "press_v913": "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6",
    "restored_press": "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5",
    "body": "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F",
    "paint": "2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069",
    "one_factory": "750FB6C93BBE8220467F5BF9656C4017F0D9E2706B35C413460AF20CEB9EB682",
}
PROTECTED_GROUPS = (
    {"name": "project_descriptor", "files": ("LineBossCarFactory.uproject",)},
    {"name": "complete_source_tree", "roots": ("Source",)},
    {"name": "complete_config_tree", "roots": ("Config",)},
    {"name": "campaign_save_games", "roots": ("Saved/SaveGames",), "allow_empty": True},
    {"name": "all_existing_content_outside_target_namespace", "roots": ("Content",), "excludes": (DEST_RELATIVE,)},
    *({"name": f"exact_{name}_map", "files": (path,)} for name, path in MAPS.items()),
)


def fail(message: str) -> None:
    raise RuntimeError("ASSEMBLY_NATIVE_KIT_UNREAL_BASELINE_V001_FAIL: " + message)


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
        fail("required file missing: " + str(path))
    stat = path.stat()
    return {"path": relative(path), "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)}


def canonical_hash(rows: list[dict]) -> str:
    compact = [{key: row[key] for key in ("path", "bytes", "mtime_ns", "sha256")}
               for row in sorted(rows, key=lambda item: item["path"].casefold())]
    return hashlib.sha256(json.dumps(compact, sort_keys=True, separators=(",", ":")).encode()).hexdigest().upper()


def inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def protected_inventory() -> tuple[list[dict], list[dict]]:
    paths: dict[str, Path] = {}
    memberships: dict[str, set[str]] = defaultdict(set)
    groups = []
    for spec in PROTECTED_GROUPS:
        selected = {PROJECT / item for item in spec.get("files", ())}
        for item in spec.get("roots", ()):
            root = PROJECT / item
            if not root.is_dir():
                if spec.get("allow_empty"):
                    continue
                fail("protected root missing: " + str(root))
            selected.update(path for path in root.rglob("*") if path.is_file())
        exclusions = [PROJECT / item for item in spec.get("excludes", ())]
        selected = {path for path in selected if not any(path.resolve() == ex.resolve() or inside(path, ex) for ex in exclusions)}
        if not selected and not spec.get("allow_empty"):
            fail("protected group empty: " + spec["name"])
        group_paths = []
        for path in sorted(selected, key=lambda item: str(item).casefold()):
            rel = relative(path)
            paths[rel] = path
            memberships[rel].add(spec["name"])
            group_paths.append(rel)
        groups.append({"name": spec["name"], "files": list(spec.get("files", ())),
                       "roots": list(spec.get("roots", ())), "excludes": list(spec.get("excludes", ())),
                       "allow_empty": bool(spec.get("allow_empty", False)), "paths": group_paths,
                       "file_count": len(group_paths)})
    rows = []
    for rel in sorted(paths, key=str.casefold):
        row = file_row(paths[rel])
        row["groups"] = sorted(memberships[rel])
        rows.append(row)
    return groups, rows


def ue_bounds(record: dict) -> dict:
    minimum = [float(value) for value in record["bounds_min_m"]]
    maximum = [float(value) for value in record["bounds_max_m"]]
    ue_min = [minimum[0] * 100.0, -maximum[1] * 100.0, minimum[2] * 100.0]
    ue_max = [maximum[0] * 100.0, -minimum[1] * 100.0, maximum[2] * 100.0]
    return {"minimum_cm": [round(value, 6) for value in ue_min],
            "maximum_cm": [round(value, 6) for value in ue_max],
            "dimensions_cm": [round(ue_max[i] - ue_min[i], 6) for i in range(3)],
            "pivot_cm": [0.0, 0.0, 0.0]}


def build_payload() -> dict:
    if Path.cwd().resolve() != PROJECT.resolve():
        fail("run from exact project root")
    if OUTPUT.exists():
        fail("refusing to overwrite existing baseline")
    if (PROJECT / DEST_RELATIVE).exists():
        fail("isolated destination already exists")
    if (PROJECT / AUDIT_RELATIVE).exists():
        fail("dedicated lane audit/results root already exists")
    for rel, expected in AUTHORITIES.items():
        actual = sha256(SOURCE_ROOT / rel)
        if actual != expected:
            fail(f"frozen authority hash drift: {rel}:{actual}")
    manifest = json.loads((SOURCE_ROOT / "MANIFEST_v001.json").read_text(encoding="utf-8-sig"))
    freeze = json.loads((SOURCE_ROOT / "Audit/FROZEN_v001.json").read_text(encoding="utf-8-sig"))
    geometry = json.loads((SOURCE_ROOT / "Audit/geometry_inventory_v001.json").read_text(encoding="utf-8-sig"))
    roundtrip = json.loads((SOURCE_ROOT / "Audit/roundtrip_validation_v001.json").read_text(encoding="utf-8-sig"))
    if manifest.get("asset_count") != 8 or manifest.get("lod_count_per_asset") != 3:
        fail("manifest 8 x 3 identity drift")
    if freeze.get("asset_count") != 8 or freeze.get("lod_record_count") != 24 or freeze.get("roundtrip_record_count") != 48:
        fail("source freeze count drift")
    if geometry.get("status") != "PASS__8_NATIVE_ASSETS_24_STRICT_LODS_ZERO_DEGENERATES" or len(geometry.get("inventory", [])) != 24:
        fail("geometry authority drift")
    if (roundtrip.get("status") != "PASS__48_OF_48_FBX_GLB_ROUNDTRIPS_EXACT" or
            roundtrip.get("validated_count") != 48 or roundtrip.get("failures") != []):
        fail("roundtrip authority drift")
    manifest_assets = {row["id"]: row for row in manifest["assets"]}
    if tuple(manifest_assets) != ASSET_KEYS:
        fail("manifest asset order drift")
    geometry_rows = {(row["asset"], int(row["lod"])): row for row in geometry["inventory"]}
    fbx_rows = {(row["asset"], int(row["lod"])): row for row in roundtrip["records"] if row["kind"] == "fbx"}
    if len(geometry_rows) != 24 or len(fbx_rows) != 24:
        fail("exact 24 geometry/FBX record gate drift")
    assets = {}
    used_slots = set()
    totals = [0, 0, 0]
    for key in ASSET_KEYS:
        identity = manifest_assets[key]
        category = identity["category"]
        asset_name = identity["base_name"] + "_v001"
        lods = []
        for lod_index in range(3):
            geo = geometry_rows[(key, lod_index)]
            fbx = fbx_rows[(key, lod_index)]
            source_rel = fbx["path"]
            source = SOURCE_ROOT / source_rel
            if sha256(source) != fbx["sha256"] or source.stat().st_size != int(fbx["bytes"]):
                fail(f"FBX byte authority drift: {key}:LOD{lod_index}")
            if int(geo["triangles"]) != int(fbx["triangles"]) or int(geo["uv_layers"]) != 1 or int(fbx["uv_layers"]) != 1:
                fail(f"geometry/roundtrip triangle or UV drift: {key}:LOD{lod_index}")
            slots = list(fbx["materials"])
            if not slots or len(slots) != len(set(slots)):
                fail(f"material slot order invalid: {key}:LOD{lod_index}")
            used_slots.update(slots)
            totals[lod_index] += int(geo["triangles"])
            lods.append({"lod": lod_index, "source": relative(source), "source_sha256": fbx["sha256"],
                         "source_bytes": int(fbx["bytes"]), "triangles": int(geo["triangles"]),
                         "source_vertices": int(geo["vertices"]), "uv_layers": 1,
                         "material_slots": slots, "expected_unreal_bounds": ue_bounds(fbx)})
        chain = [row["triangles"] for row in lods]
        if not (chain[0] > chain[1] > chain[2] > 0):
            fail("strict monotonic triangles drift: " + key)
        if any(not set(row["material_slots"]).issubset(set(lods[0]["material_slots"])) for row in lods):
            fail("LOD semantic material not present in LOD0: " + key)
        collision = ({"mode": "COMPLEX_AS_SIMPLE", "simple_count": 0, "convex_count": 0,
                      "trace_flag": "CTF_USE_COMPLEX_AS_SIMPLE", "reason": "Open installed portal/gantry geometry must remain traversable."}
                     if key in COMPLEX_COLLISION else
                     {"mode": "AABB_BOX", "simple_count": 1, "convex_count": 0,
                      "trace_flag": "CTF_USE_DEFAULT", "reason": "Compact non-enterable handling/station prop uses deterministic placement hull."})
        package = f"{DEST_NAMESPACE}/{category}/{asset_name}"
        assets[key] = {"asset_name": asset_name, "category": category, "semantic_role": identity["role"],
                       "package_path": package, "object_path": package + "." + asset_name,
                       "disk_path": DEST_RELATIVE + f"/{category}/{asset_name}.uasset",
                       "triangle_chain": chain, "strict_monotonic_triangles": True,
                       "collision": collision, "lods": lods}
    if used_slots != set(MATERIAL_BINDINGS):
        fail("material semantic coverage drift: " + repr(sorted(used_slots)))
    source_rows = [file_row(path) for path in SOURCE_ROOT.rglob("*") if path.is_file()]
    if len(source_rows) != 62:
        fail(f"exact frozen source inventory drift: expected 62 files, found {len(source_rows)}")
    groups, protected_rows = protected_inventory()
    protected = {row["path"]: row for row in protected_rows}
    for name, path in MAPS.items():
        if protected[path]["sha256"] != EXPECTED_MAP_HASHES[name]:
            fail("protected map hash drift: " + name)
    for package in MATERIAL_BINDINGS.values():
        disk = "Content/" + package.removeprefix("/Game/") + ".uasset"
        if disk not in protected:
            fail("bound material absent from protected inventory: " + disk)
    return {
        "$schema": "lineboss/assembly-line-native-kit-v001/unreal-import-baseline/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FROZEN__ASSEMBLY_LINE_NATIVE_KIT_V001_UNREAL_IMPORT_BASELINE_V001",
        "project": {"root": str(PROJECT), "uproject": "LineBossCarFactory.uproject", "game_name": "LineBossCarFactory"},
        "source": {"root": relative(SOURCE_ROOT), "authorities": AUTHORITIES, "all_files": sorted(source_rows, key=lambda row: row["path"].casefold()),
                   "file_count": len(source_rows), "inventory_sha256": canonical_hash(source_rows),
                   "manifest_status": manifest["status"], "freeze_status": freeze["status"],
                   "geometry_status": geometry["status"], "roundtrip_status": roundtrip["status"],
                   "triangle_totals": {f"LOD{i}": totals[i] for i in range(3)}, "asset_count": 8,
                   "lod_record_count": 24, "roundtrip_record_count": 48},
        "destination": {"namespace": DEST_NAMESPACE, "disk_root": DEST_RELATIVE, "expected_asset_count": 8,
                        "expected_lod_count_per_asset": 3, "expected_source_fbx_count": 24},
        "assets": assets,
        "import_contract": {"fresh_only": True, "replace_existing": False, "import_materials": False,
                            "import_textures": False, "auto_generate_collision": False, "nanite_enabled": False,
                            "lod_screen_sizes": [1.0, 0.45, 0.18], "screen_size_persistence_passes": 2,
                            "auto_compute_lod_screen_size": False, "expected_uv_channels_per_lod": 1,
                            "bounds_tolerance_cm": 0.2, "material_bindings": MATERIAL_BINDINGS,
                            "collision_policy": "PER_ASSET__AABB_COMPACT_PROPS__COMPLEX_AS_SIMPLE_OPEN_INSTALLATIONS",
                            "custom_lod_cvar": "Interchange.FeatureFlags.Import.FBX", "custom_lods_requested": 16,
                            "legacy_cvar_restore_required_in_finally": True},
        "protected": {"groups": groups, "files": protected_rows, "file_count": len(protected_rows),
                      "inventory_sha256": canonical_hash(protected_rows), "maps": {name: protected[path] for name, path in MAPS.items()}},
        "policy": {"require_target_namespace_absent": True, "require_lane_receipts_absent": True,
                   "overwrite_reimport_delete_authorized": False, "maps_load_or_save_authorized": False,
                   "runtime_binding_or_promotion_authorized": False,
                   "partial_failure_artifacts_preserved_for_explicit_recovery": True},
    }


def verify_existing() -> dict:
    if not OUTPUT.is_file():
        fail("verify-only requires existing baseline")
    payload = json.loads(OUTPUT.read_text(encoding="utf-8-sig"))
    if (payload.get("$schema") != "lineboss/assembly-line-native-kit-v001/unreal-import-baseline/v1" or
            payload.get("status") != "FROZEN__ASSEMBLY_LINE_NATIVE_KIT_V001_UNREAL_IMPORT_BASELINE_V001"):
        fail("existing baseline identity/status drift")
    if (PROJECT / DEST_RELATIVE).exists() or (PROJECT / AUDIT_RELATIVE).exists():
        fail("verify-only requires pristine target namespace and absent lane receipts")
    source_expected = {row["path"]: row for row in payload["source"]["all_files"]}
    source_paths = {relative(path) for path in SOURCE_ROOT.rglob("*") if path.is_file()}
    if source_paths != set(source_expected):
        fail("verify-only source path inventory drift")
    source_rows = []
    for rel in sorted(source_expected, key=str.casefold):
        actual, wanted = file_row(PROJECT / rel), source_expected[rel]
        if any(actual[key] != wanted[key] for key in ("bytes", "mtime_ns", "sha256")):
            fail("verify-only source file drift: " + rel)
        source_rows.append(actual)
    if canonical_hash(source_rows) != payload["source"]["inventory_sha256"]:
        fail("verify-only source canonical inventory drift")
    groups, protected_rows = protected_inventory()
    expected_groups = {row["name"]: row for row in payload["protected"]["groups"]}
    for group in groups:
        if group["name"] not in expected_groups or group["paths"] != expected_groups[group["name"]]["paths"]:
            fail("verify-only protected group drift: " + group["name"])
    protected_expected = {row["path"]: row for row in payload["protected"]["files"]}
    if {row["path"] for row in protected_rows} != set(protected_expected):
        fail("verify-only protected union path drift")
    for actual in protected_rows:
        wanted = protected_expected[actual["path"]]
        if any(actual[key] != wanted[key] for key in ("bytes", "mtime_ns", "sha256")):
            fail("verify-only protected file drift: " + actual["path"])
    digest = canonical_hash(protected_rows)
    if digest != payload["protected"]["inventory_sha256"]:
        fail("verify-only protected canonical inventory drift")
    return {"status": "PASS__FULL_SOURCE_AND_PROTECTED_BASELINE_REVERIFY",
            "baseline_sha256": sha256(OUTPUT), "source_files": len(source_rows),
            "protected_files": len(protected_rows), "protected_inventory_sha256": digest}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify_existing(), indent=2))
        return
    payload = build_payload()
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "path": str(OUTPUT), "sha256": sha256(OUTPUT),
                      "assets": 8, "lods": 24, "protected_files": payload["protected"]["file_count"]}, indent=2))


if __name__ == "__main__":
    main()
