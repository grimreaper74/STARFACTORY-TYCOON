"""Re-audit PR-005 v003 dimensions/pivots with Blender-to-Unreal Y handedness."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Candidate/PressShop/PR005/UnrealDerived_v003"
MANIFEST = json.loads((SOURCE / "PR005_EXTERIOR_ENCLOSURE_UNREAL_DERIVED_MANIFEST_v003.json").read_text(encoding="utf-8"))
DEST = "/Game/LineBoss/Candidates/PressShop/PR005/ExteriorEnclosure_v003/Meshes"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr005_exterior_enclosure_unreal_handedness_reaudit_v003.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


results, failures = [], []
for row in MANIFEST["assets"]:
    source_path = SOURCE / row["fbx"]
    if sha256(source_path) != row["sha256"]:
        failures.append(f"derived hash mismatch {row['asset_name']}")
    mesh = unreal.EditorAssetLibrary.load_asset(f"{DEST}/{row['asset_name']}")
    if not isinstance(mesh, unreal.StaticMesh):
        failures.append(f"missing {row['asset_name']}")
        continue
    box = mesh.get_bounding_box()
    measured_min = [box.min.x, box.min.y, box.min.z]
    measured_max = [box.max.x, box.max.y, box.max.z]
    pivot_mm = [float(v) * 1000.0 for v in row["pivot_m"]]
    source_local_min = [(float(row["bounds_min_mm"][i]) - pivot_mm[i]) / 10.0 for i in range(3)]
    source_local_max = [(float(row["bounds_max_mm"][i]) - pivot_mm[i]) / 10.0 for i in range(3)]
    expected_min = [source_local_min[0], -source_local_max[1], source_local_min[2]]
    expected_max = [source_local_max[0], -source_local_min[1], source_local_max[2]]
    deltas_mm = [
        (measured_min[i] - expected_min[i]) * 10.0 for i in range(3)
    ] + [
        (measured_max[i] - expected_max[i]) * 10.0 for i in range(3)
    ]
    measured_dims = [(measured_max[i] - measured_min[i]) * 10.0 for i in range(3)]
    dim_deltas = [measured_dims[i] - float(row["expected_dimensions_mm"][i]) for i in range(3)]
    passed = max(abs(v) for v in deltas_mm + dim_deltas) <= 2.0
    if not passed:
        failures.append(f"handedness-aware drift {row['asset_name']}")
    results.append({
        "asset": f"{DEST}/{row['asset_name']}",
        "status": "PASS" if passed else "FAIL",
        "expected_dimensions_mm": row["expected_dimensions_mm"],
        "measured_dimensions_mm": [round(v, 3) for v in measured_dims],
        "expected_unreal_local_min_cm": [round(v, 4) for v in expected_min],
        "expected_unreal_local_max_cm": [round(v, 4) for v in expected_max],
        "measured_unreal_local_min_cm": [round(v, 4) for v in measured_min],
        "measured_unreal_local_max_cm": [round(v, 4) for v in measured_max],
        "max_abs_delta_mm": round(max(abs(v) for v in deltas_mm + dim_deltas), 4),
    })

report = {
    "$schema": "cairnwell/audit/press-shop-pr005-exterior-enclosure-unreal-handedness-reaudit-v003/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__NINE_EXACT_DIMENSION_AND_PIVOT_MESHES__BLENDER_PLUS_Y_TO_UNREAL_MINUS_Y_CONVERSION_PROVEN__PLACEMENT_AND_RUNTIME_HOLD" if not failures else "FAIL__V003_HANDEDNESS_REAUDIT__NOT_INTEGRATED_NOT_PROMOTED",
    "supersedes_interpretation_not_file": "press_shop_pr005_exterior_enclosure_unreal_intake_v003.json",
    "reason": "The initial v003 audit compared same-sign local Y bounds. Unreal FBX conversion correctly maps Blender +Y to Unreal -Y; this audit compares the converted bounds.",
    "assets": results,
    "world_placement": "TBC_NOT_INVENTED",
    "runtime_movers_replaced": False,
    "v053_or_production_maps_changed": False,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "assets": len(results), "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
