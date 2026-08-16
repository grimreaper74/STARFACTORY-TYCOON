"""Build the static source-only UE import contract for VehicleWIPNativeKit_v001.

This is an offline standard-Python tool. It never launches/imports Unreal and it
does not snapshot Source, Content, Config, maps or saves. The later baseline
freezer owns that project-wide snapshot only after the shared Paint work settles.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
KIT = PROJECT / "SourceAssets/Candidate/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001"
OUTPUT = PROJECT / "Scripts/vehicle_wip_native_kit_unreal_import_contract_v001.json"
DEST = "/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001"
DEST_DISK = PROJECT / "Content/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001"


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT).as_posix()


def row(path: Path) -> dict:
    stat = path.stat()
    return {"path": relative(path), "sha256": sha256(path), "bytes": stat.st_size}


def cm(values) -> list[float]:
    return [round(float(value) * 100.0, 6) for value in values]


def main() -> None:
    manifest_path = KIT / "MANIFEST_v001.json"
    frozen_path = KIT / "Audit/FROZEN_v001.json"
    frozen_sha_path = KIT / "Audit/FROZEN_v001.sha256"
    build_path = KIT / "Audit/build_receipt_v001.json"
    geometry_path = KIT / "Audit/geometry_and_lod_gate_v001.json"
    roundtrip_path = KIT / "Audit/roundtrip_validation_v001.json"
    provenance_path = KIT / "Audit/provenance_and_asset_contract_v001.json"
    for path in (manifest_path, frozen_path, frozen_sha_path, build_path, geometry_path, roundtrip_path, provenance_path):
        if not path.is_file():
            raise RuntimeError("required frozen source evidence missing: " + str(path))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    build = json.loads(build_path.read_text(encoding="utf-8"))
    geometry = json.loads(geometry_path.read_text(encoding="utf-8"))
    roundtrip = json.loads(roundtrip_path.read_text(encoding="utf-8"))
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    frozen_line = frozen_sha_path.read_text(encoding="utf-8").strip().split()[0].upper()
    if (manifest.get("status") != "PASS__CLEAN_ROOM_PROCEDURAL__SOURCEASSETS_ONLY__FRESH_FBX_GLB_ROUNDTRIPS"
            or geometry.get("status") != "PASS" or roundtrip.get("status") != "PASS"
            or provenance.get("status") != "PASS__AFFIRMATIVE_ALLOWLIST__NO_ZERO_CALL_INFERENCE"
            or frozen.get("status") != "PASS__FROZEN_AFTER_BUILD_ROUNDTRIP_AND_VISUAL_INSPECTION"
            or frozen_line != sha256(frozen_path)):
        raise RuntimeError("frozen kit evidence status/hash drift")
    if DEST_DISK.exists():
        raise RuntimeError("fresh-only target already exists: " + str(DEST_DISK))

    assets = {}
    kinds = (("Layer", build["layers"], "Layers"), ("Panel", build["panels"], "Panels"))
    for kind, names, folder in kinds:
        for name in names:
            key = name
            asset_name = f"SM_LB_C2040_{name}"
            package_path = f"{DEST}/{folder}/{asset_name}"
            lods = []
            for lod in range(3):
                stats = geometry["asset_stats"][f"{kind}/{name}/LOD{lod}"]
                source = KIT / f"Exports/{folder}/LOD{lod}/SM_LB_C2040_{name}_LOD{lod}.fbx"
                source_record = build["exports"][f"{kind}/{name}/LOD{lod}"]["fbx"]
                if not source.is_file() or sha256(source) != source_record["sha256"]:
                    raise RuntimeError(f"source FBX drift: {kind}/{name}/LOD{lod}")
                lods.append({
                    "lod": lod,
                    "source": relative(source),
                    "source_sha256": sha256(source),
                    "source_bytes": source.stat().st_size,
                    "triangles": int(stats["triangles"]),
                    "vertices": int(stats["vertices"]),
                    "uv_layers": int(stats["uv_layers"]),
                    "degenerate_triangles": int(stats["degenerate_triangles"]),
                    "material_slots": list(stats["materials"]),
                    "expected_unreal_bounds": {
                        "minimum_cm": cm(stats["bounds_min_m"]),
                        "maximum_cm": cm(stats["bounds_max_m"]),
                        "dimensions_cm": cm(stats["dimensions_m"]),
                        "pivot_cm": [0.0, 0.0, 0.0],
                    },
                })
            chain = [entry["triangles"] for entry in lods]
            if not (chain[0] > chain[1] > chain[2] > 0):
                raise RuntimeError("non-monotonic source LOD chain: " + key)
            assets[key] = {
                "kind": kind,
                "role": name,
                "asset_name": asset_name,
                "package_path": package_path,
                "object_path": package_path + "." + asset_name,
                "disk_path": "Content/" + package_path.removeprefix("/Game/") + ".uasset",
                "triangle_chain": chain,
                "lods": lods,
                "collision": {"mode": "NONE_MOVING_WIP", "simple_count": 0, "convex_count": 0,
                              "trace_flag": "CTF_USE_DEFAULT", "navigation_component_policy": "CanEverAffectNavigation=false"},
                "mirror_recipe": build.get("mirror_recipes", {}).get(name),
            }

    lane_files = [
        "Scripts/vehicle_wip_native_kit_unreal_runtime_v001.py",
        "Scripts/import_vehicle_wip_native_kit_v001.py",
        "Scripts/validate_vehicle_wip_native_kit_v001.py",
        "Scripts/run_vehicle_wip_native_kit_unreal_import_lane_v001.ps1",
        "Scripts/prepare_vehicle_wip_native_kit_unreal_import_baseline_v001.py",
        "Scripts/vehicle_wip_native_kit_unreal_import_contract_v001.json",
    ]
    payload = {
        "$schema": "lineboss/vehicle-wip-native-kit-v001/unreal-static-import-contract/v1",
        "status": "READY__STATIC_SOURCE_CONTRACT_ONLY__WAITING_FOR_SHARED_PROJECT_BASELINE",
        "kit_id": "VehicleWIPNativeKit_v001",
        "model_id": "Cairnwell2040",
        "provenance_status": provenance["status"],
        "source": {
            "root": relative(KIT),
            "manifest": row(manifest_path),
            "frozen_receipt": row(frozen_path),
            "frozen_sidecar": row(frozen_sha_path),
            "frozen_tree_sha256": frozen["tree_sha256"],
            "build_receipt": row(build_path),
            "geometry_gate": row(geometry_path),
            "roundtrip_gate": row(roundtrip_path),
            "provenance_gate": row(provenance_path),
            "logical_asset_count": 16,
            "authored_lod_count": 48,
            "fbx_source_count": 48,
            "fresh_fbx_glb_roundtrip_count": 96,
        },
        "destination": {
            "namespace": DEST,
            "disk_root": relative(DEST_DISK),
            "expected_asset_count": 16,
            "expected_lod_count_per_asset": 3,
            "expected_source_fbx_count": 48,
            "expected_custom_lods_appended": 32,
            "must_be_absent_before_run": True,
            "forbidden_existing_or_meshy_namespaces": [
                "/Game/LineBoss/Candidates/Vehicles",
                "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Validation",
                "/Game/LineBoss/Candidates/WeldShop/PanelStillageRuntime_v001",
            ],
        },
        "import_contract": {
            "import_materials": False,
            "import_textures": False,
            "import_animations": False,
            "combine_meshes": True,
            "generate_lightmap_uvs": False,
            "auto_generate_collision": False,
            "remove_degenerates": False,
            "nanite_enabled": False,
            "auto_compute_lod_screen_size": False,
            "lod_screen_sizes": [1.0, 0.35, 0.12],
            "bounds_tolerance_cm": 0.25,
            "shared_pivot_cm": [0.0, 0.0, 0.0],
            "forward_axis": "+X",
            "up_axis": "+Z",
            "material_policy": "preserve exact semantic slot names; runtime native materials bind later; create no FBX materials/textures",
            "collision_policy": "zero simple/convex collision on every moving WIP mesh",
            "navigation_policy": "presentation components must set CanEverAffectNavigation=false",
        },
        "assets": assets,
        "lane_files_to_pin_when_baseline_is_cut": lane_files,
        "policy": {
            "fresh_only": True,
            "overwrite_reimport_delete_authorized": False,
            "map_load_save_authorized": False,
            "runtime_binding_or_promotion_authorized": False,
            "source_content_config_map_save_modification_outside_new_namespace_authorized": False,
            "automatic_partial_cleanup": False,
            "whole_project_baseline_must_be_cut_only_after_shared_paint_integration_settles": True,
        },
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if OUTPUT.exists():
        if OUTPUT.read_text(encoding="utf-8") != encoded:
            raise RuntimeError("refusing to overwrite changed static import contract")
    else:
        OUTPUT.write_text(encoded, encoding="utf-8")
    print("PASS__VEHICLE_WIP_NATIVE_STATIC_IMPORT_CONTRACT__NO_UE_NO_PROJECT_BASELINE")
    print(sha256(OUTPUT))


if __name__ == "__main__":
    main()
