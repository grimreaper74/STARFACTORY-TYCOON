"""Create the v088 validation contract from v087 plus the derived portal build."""

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V087 = ROOT / "Saved/Audits/PR009_InMap_v087/release_collision_build.json"
PORTAL = ROOT / "Saved/Audits/PR009_InMap_v088/trace_portal_clearance_build.json"
OUT = ROOT / "Saved/Audits/PR009_InMap_v088/release_collision_build.json"


def relabel(value):
    return value.replace("V087", "V088").replace("v087", "v088") if isinstance(value, str) else value


def main():
    baseline = json.loads(V087.read_text(encoding="utf-8"))
    portal = json.loads(PORTAL.read_text(encoding="utf-8"))
    baseline["$schema"] = "cairnwell/audit/pr009-release-collision-build-v088/v1"
    baseline["generated_utc"] = datetime.now(timezone.utc).isoformat()
    baseline["status"] = "V088_SIMPLE_COLLISION_WITH_DIMENSIONED_TRACE_PORTAL__FULL_RUNTIME_AND_SWEEP_GATES_REQUIRED__NOT_PROMOTED"
    baseline["parent_map"] = portal["parent_map"]
    baseline["target_map"] = portal["target_map"]
    baseline["portal_clearance_source_manifest"] = portal["source_manifest"]
    baseline["visual_mesh_geometry_changed"] = True
    baseline["visual_geometry_change_scope"] = "Trace portal only: 2800 mm opening and source-Y centre 3150 mm"
    baseline["source_v002_modified"] = False
    baseline["parent_v087_modified"] = False
    baseline["pr010_started"] = False
    baseline["promotion_authorized"] = False

    for row in baseline["static_groups"]:
        row["actor"] = relabel(row["actor"])
        if row["group"] == "SM_CA_MW_PR009_TracePortal_01":
            row["actor"] = portal["portal_actor"]
            row["release_asset"] = portal["imported_asset"]
            row["simple_collision"] = portal["collision"]["counts"]
            row["primitives"] = portal["collision"]["primitives"]
            row["derived_clear_opening_mm"] = portal["clear_opening_mm"]
            row["derived_source_y_envelope_m"] = portal["source_y_envelope_m"]
            row["geometry_identity_expected"] = False
            row["geometry_change_approved_for_validation"] = True
        else:
            row["geometry_identity_expected"] = True
    for key in ("moving_collision_actors", "fixed_chassis_collision_actors"):
        for row in baseline[key]:
            row["actor"] = relabel(row["actor"])
    baseline["static_simple_primitive_total"] = sum(row["simple_collision"]["total"] for row in baseline["static_groups"])
    baseline["trace_portal_clearance_build"] = str(PORTAL.relative_to(ROOT)).replace("\\", "/")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": baseline["status"],
        "output": str(OUT),
        "static_simple_primitive_total": baseline["static_simple_primitive_total"],
        "portal_asset": portal["imported_asset"],
    }, indent=2))


if __name__ == "__main__":
    main()
