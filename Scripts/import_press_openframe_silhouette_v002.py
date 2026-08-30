"""Versioned Unreal intake for the OpenFrame S03--S06 source handoff.

v001 stopped at the first native triangle-count mismatch.  This is a
measurement-led supersede: Blender proves that each source FBX contains 16
zero-area triangles, while UE removes those faces during mesh build even when
the legacy importer reports ``remove_degenerates=False``.  v002 preserves the
immutable source count and separately asserts the expected UE payload count.

It never mutates v001, any map, the source package, or the runtime binding.
"""

from __future__ import annotations

import importlib.util
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
SCRIPTS = PROJECT / "Scripts"
BASE_SCRIPT = SCRIPTS / "import_press_openframe_silhouette_v001.py"
TRIANGLE_ACCOUNTING = (PROJECT / "Saved/Audits/OneFactory/Press/"
                       "OpenFrameSilhouetteNative_v001/"
                       "openframe_triangle_accounting_v001.json")
DEST = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/OpenFrameSilhouette_v002"
MESH_DEST = DEST + "/Meshes"
SCRATCH_DEST = DEST + "/_ImportScratch"
AUDIT_DIR = PROJECT / "Saved/Audits/OneFactory/Press/OpenFrameSilhouetteNative_v002"
RECEIPT = AUDIT_DIR / "native_import_receipt_v002.json"
FAILURE = AUDIT_DIR / "native_import_failure_v002.json"


def fail(message: str) -> None:
    raise RuntimeError("OPENFRAME_SILHOUETTE_NATIVE_IMPORT_V002_FAIL: " + message)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_v001_module():
    if not BASE_SCRIPT.is_file():
        fail("v001 intake script is absent")
    spec = importlib.util.spec_from_file_location("openframe_native_import_v001", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        fail("could not load v001 intake script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reconcile_triangle_contract(v001, specs):
    if not TRIANGLE_ACCOUNTING.is_file():
        fail("Blender triangle-accounting evidence is absent")
    accounting = json.loads(TRIANGLE_ACCOUNTING.read_text(encoding="utf-8"))
    if accounting.get("source_blend_modified") or accounting.get("unreal_assets_modified"):
        fail("triangle-accounting evidence is not read-only")
    source_rows = accounting.get("source", {})
    fbx_rows = accounting.get("fbx_reimport", {})
    if set(source_rows) != set(specs) or set(fbx_rows) != set(specs):
        fail("triangle-accounting station inventory drift")
    reconciled = {}
    for station, spec in sorted(specs.items()):
        source = source_rows[station]
        fbx = fbx_rows[station]
        manifest_triangles = int(spec["triangles"])
        source_triangles = int(source["evaluated_blend"]["triangles"])
        fbx_triangles = int(fbx["triangles"])
        source_degenerates = int(source["evaluated_blend"]["degenerate_area_le_1e-12"])
        fbx_degenerates = int(fbx["degenerate_area_le_1e-12"])
        if (int(source["manifest_evaluated_export_triangles"]) != manifest_triangles
                or source_triangles != manifest_triangles
                or fbx_triangles != manifest_triangles):
            fail("source/FBX triangle evidence drift: " + station)
        if source_degenerates <= 0 or fbx_degenerates != source_degenerates:
            fail("degenerate-face evidence drift: " + station)
        expected_native = fbx_triangles - fbx_degenerates
        if expected_native <= 0:
            fail("non-positive expected native payload: " + station)
        spec["source_evaluated_export_triangles"] = manifest_triangles
        spec["source_zero_area_triangles"] = fbx_degenerates
        spec["expected_native_payload_triangles"] = expected_native
        # v001's verifier consumes spec['triangles']; in v002 it deliberately
        # means the UE-built payload rather than the Blender export payload.
        spec["triangles"] = expected_native
        reconciled[station] = {
            "source_evaluated_export_triangles": manifest_triangles,
            "source_zero_area_triangles": fbx_degenerates,
            "expected_native_payload_triangles": expected_native,
        }
    return reconciled


def main():
    v001 = load_v001_module()
    # Reuse the tested import and verification functions, but never write into
    # v001's partial evidence namespace or its receipts.
    v001.DEST = DEST
    v001.MESH_DEST = MESH_DEST
    v001.SCRATCH_DEST = SCRATCH_DEST
    v001.AUDIT_DIR = AUDIT_DIR
    v001.RECEIPT = RECEIPT
    v001.FAILURE = FAILURE
    evidence = {
        "$schema": "lineboss/onefactory/press/openframe-silhouette-v002/native-import/v1",
        "generated_utc": utc_now(),
        "supersedes": "OpenFrameSilhouetteNative_v001 import accounting only",
        "destination": DEST,
        "triangle_accounting_evidence": str(TRIANGLE_ACCOUNTING),
        "map_opened_by_script": False,
        "map_saved_by_script": False,
        "source_assets_mutated": False,
        "v001_native_namespace_mutated": False,
        "content_writes": [DEST],
        "integration_authorized": False,
    }
    try:
        manifest, specs = v001.source_contract()
        triangle_accounting = reconcile_triangle_contract(v001, specs)
        evidence.update({
            "source_manifest_sha256": v001.sha256(v001.MANIFEST),
            "source_fbx": {
                station: {"path": str(spec["source"]), "sha256": spec["sha256"]}
                for station, spec in specs.items()
            },
            "triangle_accounting": triangle_accounting,
        })
        if RECEIPT.exists():
            fail("prior successful v002 receipt exists; refusing overwrite")
        if v001.LIBRARY.does_directory_exist(DEST):
            fail("fresh v002 destination namespace already exists")
        meshes = v001.import_meshes(specs)
        rows = v001.configure_and_verify(meshes, specs)
        registry = set(str(item) for item in v001.LIBRARY.list_assets(
            DEST, recursive=True, include_folder=False))
        expected_registry = {
            v001.object_path(MESH_DEST, spec["name"]) for spec in specs.values()
        }
        if registry != expected_registry:
            fail("native v002 package closure drift: {} vs {}".format(registry, expected_registry))
        for station, row in rows.items():
            expected = triangle_accounting[station]["expected_native_payload_triangles"]
            if row["triangles"] != expected:
                fail("native payload did not match reconciled evidence: " + station)
        evidence.update({
            "status": "PASS__OPENFRAME_SILHOUETTE_V002_NATIVE_IMPORT_RECONCILED",
            "native_mesh_count": len(rows),
            "native_payload_triangles": sum(row["triangles"] for row in rows.values()),
            "source_evaluated_export_triangles": sum(
                row["source_evaluated_export_triangles"] for row in triangle_accounting.values()),
            "native_assets": sorted(registry),
            "native_recipe": {
                "importer": "Unreal 5.8 legacy FbxFactory",
                "combine_meshes": False,
                "convert_scene": True,
                "convert_scene_unit": True,
                "transform_vertex_to_absolute": False,
                "bake_pivot_in_vertex": False,
                "remove_degenerates_requested": False,
                "observed_mesh_build": "UE strips the 16 source zero-area triangles per FBX",
                "collision": "none authored/imported",
                "nanite": False,
            },
            "meshes": rows,
        })
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        unreal.log("OPENFRAME_SILHOUETTE_NATIVE_IMPORT_V002_PASS=" + str(RECEIPT))
    except Exception as error:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        failure = {
            **evidence,
            "status": "FAIL_CLOSED__OPENFRAME_SILHOUETTE_V002_NATIVE_IMPORT",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "partial_native_assets_preserved": list(v001.LIBRARY.list_assets(
                DEST, recursive=True, include_folder=False))
            if v001.LIBRARY.does_directory_exist(DEST) else [],
        }
        FAILURE.write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        unreal.log_error("OPENFRAME_SILHOUETTE_NATIVE_IMPORT_V002_FAIL=" + str(error))
        raise
    finally:
        unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
