"""Shared UE 5.8 runtime helpers for the guarded Assembly native-kit lane."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
BASELINE = PROJECT / "Scripts/assembly_line_native_kit_unreal_import_baseline_v001.json"
DEST = "/Game/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001"
DEST_DISK = PROJECT / "Content/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001"
AUDIT_ROOT = PROJECT / "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/UnrealImportLane_v001"
RUN_ROOT_ENV = "LINEBOSS_ASSEMBLY_NATIVE_KIT_V001_RUN_ROOT"
ACK_ENV = "LINEBOSS_ASSEMBLY_NATIVE_KIT_V001_ACK"
ACK_TOKEN = "IMPORT_FROZEN_ASSEMBLY_LINE_NATIVE_KIT_V001_BASELINE_V001_ONCE"
INTERCHANGE_FBX_CVAR = "Interchange.FeatureFlags.Import.FBX"
IMPORT_RECEIPT = "import_receipt_v001.json"
IMPORT_FAILURE = "import_failure_v001.json"
VALIDATION_RECEIPT = "fresh_load_validation_receipt_v001.json"
VALIDATION_FAILURE = "fresh_load_validation_failure_v001.json"
SUMMARY = "lane_summary_v001.json"
RESULT_NAMES = {IMPORT_RECEIPT, IMPORT_FAILURE, VALIDATION_RECEIPT, VALIDATION_FAILURE, SUMMARY}
EXPECTED_BASELINE_SHA256 = "041C802023D14ADE7EC418EF7488679D7F4A03550471AE38E2DC80B310E731BA"
EXPECTED_BASELINE_STATUS = "FROZEN__ASSEMBLY_LINE_NATIVE_KIT_V001_UNREAL_IMPORT_BASELINE_V001"
library = unreal.EditorAssetLibrary


def fail(message: str) -> None:
    raise RuntimeError("ASSEMBLY_NATIVE_KIT_UNREAL_LANE_V001_FAIL: " + message)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
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


def load_baseline() -> dict:
    if PROJECT != EXPECTED_PROJECT:
        fail("project identity drift")
    if str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("game identity drift")
    if not BASELINE.is_file() or sha256(BASELINE) != EXPECTED_BASELINE_SHA256:
        fail("frozen baseline absent or changed")
    payload = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
    if (payload.get("$schema") != "lineboss/assembly-line-native-kit-v001/unreal-import-baseline/v1" or
            payload.get("status") != EXPECTED_BASELINE_STATUS or
            payload.get("destination", {}).get("namespace") != DEST or
            payload.get("destination", {}).get("expected_asset_count") != 8 or
            payload.get("destination", {}).get("expected_lod_count_per_asset") != 3):
        fail("baseline identity/destination drift")
    policy = payload.get("policy", {})
    if (policy.get("overwrite_reimport_delete_authorized") is not False or
            policy.get("require_target_namespace_absent") is not True or
            policy.get("require_lane_receipts_absent") is not True):
        fail("baseline safety policy drift")
    return payload


def verify_source(baseline: dict) -> dict:
    wanted = {row["path"]: row for row in baseline["source"]["all_files"]}
    root = PROJECT / baseline["source"]["root"]
    actual_paths = {relative(path) for path in root.rglob("*") if path.is_file()}
    if actual_paths != set(wanted):
        fail("frozen source path inventory drift")
    rows = []
    for rel in sorted(wanted, key=str.casefold):
        actual = file_row(PROJECT / rel)
        expected = wanted[rel]
        if any(actual[key] != expected[key] for key in ("bytes", "mtime_ns", "sha256")):
            fail("frozen source file drift: " + rel)
        rows.append(actual)
    digest = canonical_hash(rows)
    if digest != baseline["source"]["inventory_sha256"]:
        fail("frozen source inventory hash drift")
    return {"file_count": len(rows), "inventory_sha256": digest}


def scan_group(group: dict) -> set[str]:
    selected = {PROJECT / item for item in group.get("files", [])}
    for item in group.get("roots", []):
        root = PROJECT / item
        if not root.is_dir():
            if group.get("allow_empty"):
                continue
            fail("protected root missing: " + str(root))
        selected.update(path for path in root.rglob("*") if path.is_file())
    exclusions = [PROJECT / item for item in group.get("excludes", [])]
    selected = {path for path in selected if not any(path.resolve() == ex.resolve() or inside(path, ex) for ex in exclusions)}
    return {relative(path) for path in selected}


def verify_protected(baseline: dict, full_hash: bool) -> dict:
    protected = baseline["protected"]
    wanted = {row["path"]: row for row in protected["files"]}
    union = set()
    groups = []
    for group in protected["groups"]:
        actual = scan_group(group)
        if actual != set(group["paths"]):
            fail("protected group inventory drift: " + group["name"])
        union.update(actual)
        groups.append({"name": group["name"], "file_count": len(actual)})
    if union != set(wanted):
        fail("protected union inventory drift")
    rows = []
    critical = set(row["path"] for row in protected["maps"].values())
    critical.update("Content/" + package.removeprefix("/Game/") + ".uasset"
                    for package in baseline["import_contract"]["material_bindings"].values())
    for rel in sorted(union, key=str.casefold):
        path = PROJECT / rel
        stat = path.stat()
        expected = wanted[rel]
        if stat.st_size != int(expected["bytes"]) or stat.st_mtime_ns != int(expected["mtime_ns"]):
            fail("protected metadata drift: " + rel)
        if full_hash or rel in critical:
            actual = file_row(path)
            if actual["sha256"] != expected["sha256"]:
                fail("protected hash drift: " + rel)
            rows.append(actual)
    return {"file_count": len(union), "hashed_file_count": len(rows),
            "hashed_inventory_sha256": canonical_hash(rows), "groups": groups, "full_hash": full_hash}


def namespace_inventory() -> dict:
    if not DEST_DISK.is_dir():
        return {}
    return {row["path"]: {"bytes": row["bytes"], "mtime_ns": row["mtime_ns"], "sha256": row["sha256"]}
            for row in (file_row(path) for path in sorted(DEST_DISK.rglob("*"), key=lambda item: str(item).casefold()) if path.is_file())}


def package_file(package_path: str) -> Path:
    return PROJECT / "Content" / Path(package_path.removeprefix("/Game/")).with_suffix(".uasset")


def object_path(package_path: str) -> str:
    return package_path + "." + package_path.rsplit("/", 1)[-1]


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
    if slots != spec["lods"][0]["material_slots"]:
        fail("global material semantic drift: " + key)
    lods = []
    for index, expected in enumerate(spec["lods"]):
        triangles = int(mesh.get_num_triangles(index))
        uv = int(mesh.get_num_tex_coords(index))
        bounds = lod_bounds(mesh, index)
        if triangles != expected["triangles"] or uv != 1:
            fail(f"triangle/UV channel drift: {key}:LOD{index}")
        assert_bounds(bounds, expected["expected_unreal_bounds"], baseline["import_contract"]["bounds_tolerance_cm"], f"{key}:LOD{index}")
        sections = section_slots(mesh, subsystem, index, slots)
        if sections != expected["material_slots"]:
            fail(f"section/material drift: {key}:LOD{index}")
        lods.append({"lod": index, "triangles": triangles, "vertices": int(mesh.get_num_vertices(index)),
                     "uv_channels": uv, "bounds": bounds, "section_material_slots": sections})
    chain = [row["triangles"] for row in lods]
    if chain != spec["triangle_chain"] or not (chain[0] > chain[1] > chain[2] > 0):
        fail("strict monotonic triangle drift: " + key)
    expected_materials = [object_path(baseline["import_contract"]["material_bindings"][slot]) for slot in slots]
    bound = [mesh.get_material(i).get_path_name() if mesh.get_material(i) else None for i in range(len(slots))]
    if bound != expected_materials:
        fail("bound material semantics drift: " + key)
    body = mesh.get_editor_property("body_setup")
    simple = int(unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh))
    convex = int(unreal.EditorStaticMeshLibrary.get_convex_collision_count(mesh))
    trace = str(body.get_editor_property("collision_trace_flag")) if body else "NONE"
    collision = spec["collision"]
    nanite = bool(subsystem.get_nanite_settings(mesh).get_editor_property("enabled"))
    if (simple != collision["simple_count"] or convex != collision["convex_count"] or
            collision["trace_flag"].removeprefix("CTF_") not in trace.upper() or nanite):
        fail("collision/Nanite drift: " + key + f":{simple}:{convex}:{trace}:{nanite}")
    return {"asset_key": key, "object_path": mesh.get_path_name(), "lod_count": 3,
            "lod_screen_sizes": screens, "lod_screen_size_auto_computed": False,
            "lods": lods, "triangle_chain": chain, "strict_monotonic_triangles": True,
            "global_material_slots": slots, "bound_materials": bound,
            "simple_collision_count": simple, "convex_collision_count": convex,
            "collision_trace_flag": trace, "collision_mode": collision["mode"],
            "nanite_enabled": nanite, "legacy_import_data": import_data(mesh)}
