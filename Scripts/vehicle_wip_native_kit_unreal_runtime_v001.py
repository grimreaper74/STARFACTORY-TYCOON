"""Shared UE 5.8 helpers for the guarded clean-room vehicle-WIP intake lane."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
CONTRACT = PROJECT / "Scripts/vehicle_wip_native_kit_unreal_import_contract_v001.json"
EXPECTED_CONTRACT_SHA256 = "87D9FD32964CC0AD0F4AA52CC6F27A0E23BFDA23A18B2F714E6E2807CCA9684D"
BASELINE = PROJECT / "Scripts/vehicle_wip_native_kit_unreal_import_baseline_v001.json"
BASELINE_SHA = PROJECT / "Scripts/vehicle_wip_native_kit_unreal_import_baseline_v001.sha256"
DEST = "/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001"
DEST_DISK = PROJECT / "Content/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001"
AUDIT_ROOT = PROJECT / "Saved/Audits/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/UnrealImportLane_v001"
RUN_ROOT_ENV = "LINEBOSS_VEHICLE_WIP_NATIVE_V001_RUN_ROOT"
ACK_ENV = "LINEBOSS_VEHICLE_WIP_NATIVE_V001_ACK"
ACK_TOKEN = "IMPORT_FROZEN_VEHICLE_WIP_NATIVE_KIT_V001_BASELINE_V001_ONCE"
INTERCHANGE_FBX_CVAR = "Interchange.FeatureFlags.Import.FBX"
IMPORT_RECEIPT = "import_receipt_v001.json"
IMPORT_FAILURE = "import_failure_v001.json"
VALIDATION_RECEIPT = "fresh_load_validation_receipt_v001.json"
VALIDATION_FAILURE = "fresh_load_validation_failure_v001.json"
SUMMARY = "lane_summary_v001.json"
RESULT_NAMES = {IMPORT_RECEIPT, IMPORT_FAILURE, VALIDATION_RECEIPT, VALIDATION_FAILURE, SUMMARY}
EXPECTED_BASELINE_STATUS = "FROZEN__VEHICLE_WIP_NATIVE_KIT_V001_UNREAL_IMPORT_BASELINE_V001"
library = unreal.EditorAssetLibrary


def fail(message: str) -> None:
    raise RuntimeError("VEHICLE_WIP_NATIVE_KIT_V001_UNREAL_LANE_FAIL: " + message)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT).as_posix()


def file_row(path: Path) -> dict:
    if not path.is_file():
        fail("required file missing: " + str(path))
    stat = path.stat()
    return {"path": relative(path), "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)}


def canonical_hash(rows: list[dict]) -> str:
    compact = [{key: row[key] for key in ("path", "bytes", "mtime_ns", "sha256")}
               for row in sorted(rows, key=lambda item: item["path"].casefold())]
    return hashlib.sha256(json.dumps(compact, sort_keys=True, separators=(",", ":")).encode()).hexdigest().upper()


def run_root() -> Path:
    raw = os.environ.get(RUN_ROOT_ENV, "").strip()
    if not raw or os.environ.get(ACK_ENV, "").strip() != ACK_TOKEN:
        fail("guarded runner environment/acknowledgement absent")
    path = Path(raw).resolve()
    if path == AUDIT_ROOT.resolve() or not inside(path, AUDIT_ROOT) or not path.is_dir():
        fail("run root escapes or is absent: " + str(path))
    return path


def load_contract() -> dict:
    if not CONTRACT.is_file() or sha256(CONTRACT) != EXPECTED_CONTRACT_SHA256:
        fail("exact static clean-room source contract absent or changed")
    payload = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    if (payload.get("$schema") != "lineboss/vehicle-wip-native-kit-v001/unreal-static-import-contract/v1"
            or payload.get("destination", {}).get("namespace") != DEST
            or payload.get("destination", {}).get("expected_asset_count") != 16
            or payload.get("destination", {}).get("expected_lod_count_per_asset") != 3):
        fail("static contract identity/destination drift")
    forbidden = payload["destination"]["forbidden_existing_or_meshy_namespaces"]
    if not DEST.startswith("/Game/LineBoss/Native/Vehicles/") or any(DEST.startswith(item) for item in forbidden):
        fail("destination is not the isolated native namespace")
    return payload


def load_baseline() -> dict:
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("running project identity drift")
    contract = load_contract()
    if not BASELINE.is_file() or not BASELINE_SHA.is_file():
        fail("post-Paint whole-project baseline has not been cut")
    if BASELINE_SHA.read_text(encoding="utf-8-sig").strip().split()[0].upper() != sha256(BASELINE):
        fail("baseline sidecar mismatch")
    payload = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
    if (payload.get("$schema") != "lineboss/vehicle-wip-native-kit-v001/unreal-import-baseline/v1"
            or payload.get("status") != EXPECTED_BASELINE_STATUS
            or payload.get("contract", {}).get("sha256") != EXPECTED_CONTRACT_SHA256
            or payload.get("destination", {}).get("namespace") != DEST
            or payload.get("destination", {}).get("expected_asset_count") != 16
            or payload.get("policy", {}).get("overwrite_reimport_delete_authorized") is not False):
        fail("frozen baseline identity/safety drift")
    if set(payload["assets"]) != set(contract["assets"]):
        fail("baseline/static-contract asset role drift")
    return payload


def verify_inventory(snapshot: dict, label: str) -> dict:
    rows = []
    for expected in snapshot["all_files"] if "all_files" in snapshot else snapshot["files"]:
        actual = file_row(PROJECT / expected["path"])
        if any(actual[key] != expected[key] for key in ("bytes", "mtime_ns", "sha256")):
            fail(f"{label} file drift: {expected['path']}")
        rows.append(actual)
    digest = canonical_hash(rows)
    if len(rows) != int(snapshot["file_count"]) or digest != snapshot["inventory_sha256"]:
        fail(label + " inventory drift")
    return {"file_count": len(rows), "inventory_sha256": digest}


def verify_source(baseline: dict) -> dict:
    root = PROJECT / baseline["source"]["root"]
    actual_paths = {relative(path) for path in root.rglob("*") if path.is_file()}
    wanted_paths = {row["path"] for row in baseline["source"]["all_files"]}
    if actual_paths != wanted_paths:
        fail("frozen source path inventory drift")
    return verify_inventory(baseline["source"], "frozen source")


def verify_protected(baseline: dict) -> dict:
    protected = baseline["protected"]
    actual_union = set()
    for group in protected["groups"]:
        selected = {PROJECT / rel for rel in group.get("files", [])}
        for rel in group.get("roots", []):
            root = PROJECT / rel
            if not root.is_dir():
                if group.get("allow_empty"):
                    continue
                fail("protected root missing: " + rel)
            selected.update(path for path in root.rglob("*") if path.is_file())
        exclusions = [PROJECT / rel for rel in group.get("excludes", [])]
        selected = {path for path in selected
                    if not any(path.resolve() == ex.resolve() or inside(path, ex) for ex in exclusions)}
        paths = {relative(path) for path in selected}
        if paths != set(group["paths"]):
            fail("protected group path inventory drift: " + group["name"])
        actual_union.update(paths)
    if actual_union != {row["path"] for row in protected["files"]}:
        fail("protected group union drift")
    return verify_inventory(protected, "protected project")


def verify_lane(baseline: dict) -> dict:
    return verify_inventory(baseline["lane"], "prepared lane")


def namespace_inventory() -> dict:
    if not DEST_DISK.is_dir():
        return {}
    return {row["path"]: {"bytes": row["bytes"], "mtime_ns": row["mtime_ns"], "sha256": row["sha256"]}
            for row in (file_row(path) for path in sorted(DEST_DISK.rglob("*"), key=lambda p: str(p).casefold()) if path.is_file())}


def prior_results() -> list[str]:
    if not AUDIT_ROOT.is_dir():
        return []
    return sorted(relative(path) for path in AUDIT_ROOT.rglob("*") if path.is_file() and path.name in RESULT_NAMES)


def vector(value) -> list[float]:
    return [float(value.x), float(value.y), float(value.z)]


def lod_bounds(mesh, lod_index: int) -> dict:
    dynamic = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    request = unreal.GeometryScriptMeshReadLOD()
    request.set_editor_properties({"lod_type": unreal.GeometryScriptLODType.SOURCE_MODEL, "lod_index": lod_index})
    dynamic, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(mesh, dynamic, options, request, False)
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        fail(f"source LOD bounds extraction failed: {mesh.get_name()}:LOD{lod_index}")
    box = dynamic.get_mesh_bounding_box()
    minimum, maximum = vector(box.min), vector(box.max)
    return {"minimum_cm": minimum, "maximum_cm": maximum,
            "dimensions_cm": [maximum[i] - minimum[i] for i in range(3)], "pivot_cm": [0.0, 0.0, 0.0]}


def assert_bounds(actual: dict, expected: dict, tolerance: float, label: str) -> None:
    for field in ("minimum_cm", "maximum_cm", "dimensions_cm"):
        if max(abs(float(actual[field][i]) - float(expected[field][i])) for i in range(3)) > tolerance:
            fail(label + " bounds/pivot drift: " + field)


def slot_names(mesh) -> list[str]:
    return [str(row.get_editor_property("material_slot_name")) for row in mesh.get_editor_property("static_materials")]


def section_slots(mesh, subsystem, lod_index: int, slots: list[str]) -> list[str]:
    output = []
    for section in range(int(mesh.get_num_sections(lod_index))):
        index = int(subsystem.get_lod_material_slot(mesh, lod_index, section))
        if index < 0 or index >= len(slots):
            fail(f"section/material index invalid: {mesh.get_name()}:LOD{lod_index}")
        output.append(slots[index])
    return output


def import_data(mesh) -> dict:
    data = mesh.get_editor_property("asset_import_data")
    output = {"import_uniform_scale": float(data.get_editor_property("import_uniform_scale")),
              "convert_scene": bool(data.get_editor_property("convert_scene")),
              "convert_scene_unit": bool(data.get_editor_property("convert_scene_unit")),
              "force_front_x_axis": bool(data.get_editor_property("force_front_x_axis")),
              "transform_vertex_to_absolute": bool(data.get_editor_property("transform_vertex_to_absolute")),
              "bake_pivot_in_vertex": bool(data.get_editor_property("bake_pivot_in_vertex")),
              "generate_lightmap_u_vs": bool(data.get_editor_property("generate_lightmap_u_vs")),
              "auto_generate_collision": bool(data.get_editor_property("auto_generate_collision")),
              "remove_degenerates": bool(data.get_editor_property("remove_degenerates"))}
    expected = {"import_uniform_scale": 1.0, "convert_scene": True, "convert_scene_unit": True,
                "force_front_x_axis": False, "transform_vertex_to_absolute": True,
                "bake_pivot_in_vertex": False, "generate_lightmap_u_vs": False,
                "auto_generate_collision": False, "remove_degenerates": False}
    if output != expected:
        fail("legacy FBX import setting drift: " + mesh.get_name() + repr(output))
    return output


def validate_mesh(key: str, spec: dict, baseline: dict, subsystem) -> dict:
    mesh = library.load_asset(spec["package_path"])
    if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name() != spec["object_path"] or int(mesh.get_num_lods()) != 3:
        fail("StaticMesh/object/LOD count drift: " + key)
    screens = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
    if screens != baseline["import_contract"]["lod_screen_sizes"] or mesh.is_lod_screen_size_auto_computed():
        fail("manual LOD screen-size drift: " + key)
    slots = slot_names(mesh)
    expected_global = spec["lods"][0]["material_slots"]
    if slots != expected_global:
        fail("global semantic material slot drift: " + key + repr(slots))
    lods = []
    for index, expected in enumerate(spec["lods"]):
        triangles = int(mesh.get_num_triangles(index))
        uv = int(mesh.get_num_tex_coords(index))
        bounds = lod_bounds(mesh, index)
        if triangles != int(expected["triangles"]) or uv != 1:
            fail(f"triangle/UV drift: {key}:LOD{index}")
        assert_bounds(bounds, expected["expected_unreal_bounds"], baseline["import_contract"]["bounds_tolerance_cm"], f"{key}:LOD{index}")
        sections = section_slots(mesh, subsystem, index, slots)
        if sections != expected["material_slots"]:
            fail(f"section/material semantic drift: {key}:LOD{index}:{sections}")
        lods.append({"lod": index, "triangles": triangles, "vertices": int(mesh.get_num_vertices(index)),
                     "uv_channels": uv, "bounds": bounds, "section_material_slots": sections})
    chain = [entry["triangles"] for entry in lods]
    if chain != spec["triangle_chain"] or not (chain[0] > chain[1] > chain[2] > 0):
        fail("strict LOD triangle chain drift: " + key)
    simple = int(unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh))
    convex = int(unreal.EditorStaticMeshLibrary.get_convex_collision_count(mesh))
    body = mesh.get_editor_property("body_setup")
    trace = str(body.get_editor_property("collision_trace_flag")) if body else "NONE"
    nanite = bool(subsystem.get_nanite_settings(mesh).get_editor_property("enabled"))
    if simple != 0 or convex != 0 or "DEFAULT" not in trace.upper() or nanite:
        fail(f"moving-WIP collision/Nanite drift: {key}:{simple}:{convex}:{trace}:{nanite}")
    bound = [mesh.get_material(i).get_path_name() if mesh.get_material(i) else None for i in range(len(slots))]
    if any(path and path.startswith("/Game/LineBoss/Candidates/Vehicles/") for path in bound):
        fail("Meshy-era vehicle material binding entered native namespace: " + key)
    return {"asset_key": key, "object_path": mesh.get_path_name(), "lod_count": 3,
            "lod_screen_sizes": screens, "lod_screen_size_auto_computed": False,
            "lods": lods, "triangle_chain": chain, "strict_monotonic_triangles": True,
            "global_material_slots": slots, "bound_materials": bound,
            "simple_collision_count": simple, "convex_collision_count": convex,
            "collision_trace_flag": trace, "nanite_enabled": nanite, "legacy_import_data": import_data(mesh)}
