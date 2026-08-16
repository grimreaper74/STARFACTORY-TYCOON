"""Independent clean-scene round-trip validator for the CR01 reduction study."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUTPUT = PROJECT / "Saved/Experiments/SupportRobots/CR01_TriangleReduction_v001"
MANIFEST = OUTPUT / "experiment_manifest_v001.json"
RECEIPT = OUTPUT / "roundtrip_validation_v001.json"


def fail(message: str) -> None:
    raise RuntimeError("CR01_TRIANGLE_REDUCTION_VALIDATION_V001_FAIL: " + message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def triangle_count(obj: bpy.types.Object) -> int:
    return sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons)


def dimensions_cm(obj: bpy.types.Object) -> list[float]:
    return [round(float(value) * 100.0, 5) for value in obj.dimensions]


def main() -> None:
    if not MANIFEST.is_file() or RECEIPT.exists():
        fail("manifest missing or validation receipt already exists")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("status") != "PASS__ISOLATED_CR01_AUTOMATIC_REDUCTION_AND_ADDON_EXPORT_EXPERIMENT_V001":
        fail("experiment manifest status drift")
    if sha256(Path(manifest["source"]["path"])) != manifest["source"]["sha256"]:
        fail("source hash drift")

    rows = []
    for expected in manifest["results"]:
        fbx = OUTPUT / expected["fbx"]
        if not fbx.is_file() or sha256(fbx) != expected["fbx_sha256"]:
            fail("FBX missing/hash drift: " + str(fbx))
        # Clear only scene objects. Loading factory settings here fires unrelated
        # extension handlers and is not required for an independent FBX round-trip.
        for existing in list(bpy.data.objects):
            bpy.data.objects.remove(existing, do_unlink=True)
        result = bpy.ops.import_scene.fbx(filepath=str(fbx), use_anim=False)
        if "FINISHED" not in result:
            fail("FBX import failed: " + str(fbx))
        meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
        if len(meshes) != 1:
            fail(f"expected one round-trip mesh for {fbx.name}, found {len(meshes)}")
        obj = meshes[0]
        actual_triangles = triangle_count(obj)
        triangle_delta = actual_triangles - expected["actual_triangles"]
        # FBX may discard a handful of zero-area faces. Permit only a tiny,
        # reduction-only normalization; any growth or material loss still fails.
        if triangle_delta > 0 or triangle_delta < -8:
            fail(
                f"triangle normalization outside 0..-8 for {fbx.name}: "
                f"{actual_triangles} vs {expected['actual_triangles']}"
            )
        dims = dimensions_cm(obj)
        delta = [abs(a - b) for a, b in zip(dims, expected["dimensions_cm"])]
        if max(delta) > 0.02:
            fail(f"round-trip bounds drift for {fbx.name}: {delta}")
        uv_layers = [layer.name for layer in obj.data.uv_layers]
        if not uv_layers:
            fail("round-trip UV missing: " + fbx.name)
        if len(obj.material_slots) != 1:
            fail("round-trip material-slot count drift: " + fbx.name)
        rows.append({
            "fbx": expected["fbx"],
            "fbx_sha256": expected["fbx_sha256"],
            "triangles": actual_triangles,
            "triangle_delta_from_blend": triangle_delta,
            "fbx_zero_area_normalization_accepted": triangle_delta != 0,
            "dimensions_cm": dims,
            "max_dimension_delta_cm": round(max(delta), 6),
            "uv_layers": uv_layers,
            "material_slot_count": len(obj.material_slots),
        })

    study = OUTPUT / manifest["study_blend"]["path"]
    render = OUTPUT / manifest["comparison_render"]["path"]
    if sha256(study) != manifest["study_blend"]["sha256"]:
        fail("study blend hash drift")
    if sha256(render) != manifest["comparison_render"]["sha256"]:
        fail("comparison render hash drift")

    receipt = {
        "schema": "lineboss/validation/support-robots/cr01-triangle-reduction-roundtrip-v001/v1",
        "status": "PASS__CR01_REDUCED_FBX_CLEAN_SCENE_ROUNDTRIP_V001",
        "experiment_manifest_sha256": sha256(MANIFEST),
        "validated_exports": rows,
        "source_modified": False,
        "unreal_content_modified": False,
        "promotion_authorized": False,
        "failures": [],
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("CR01_TRIANGLE_REDUCTION_VALIDATION_V001_PASS=" + str(RECEIPT))


if __name__ == "__main__":
    main()
