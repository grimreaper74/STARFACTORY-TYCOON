"""Validate RP01 core v003 and the MR01 v004 / CR01 v007 successors."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def world_mm(obj):
    return [round(v * 1000.0, 3) for v in obj.matrix_world.translation]


def bounds_mm(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [round(min(p[i] for p in points) * 1000.0, 3) for i in range(3)],
        "max": [round(max(p[i] for p in points) * 1000.0, 3) for i in range(3)],
    }


def size_mm(obj):
    bounds = bounds_mm(obj)
    return [round(bounds["max"][i] - bounds["min"][i], 3) for i in range(3)]


def close(actual, expected, tolerance=1.0):
    return all(abs(actual[i] - expected[i]) <= tolerance for i in range(3))


def intersects(a, b):
    return all(a["min"][i] < b["max"][i] and a["max"][i] > b["min"][i] for i in range(3))


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2 or args[0].lower() not in {"core", "mr01", "cr01"}:
        raise SystemExit("Usage: -- core|mr01|cr01 output.json [v003|v004]")
    mode, output = args[0].lower(), Path(args[1]).resolve()
    family = args[2].lower() if len(args) >= 3 else "v003"
    if family not in {"v003", "v004"}:
        raise SystemExit(f"Unsupported family {family}")
    blend = Path(bpy.data.filepath).resolve()
    objects = bpy.data.objects
    failures = []

    roots = {
        "v003": {"core": "ROOT_LB_RP01_DOCK_CORE_V003", "mr01": "ROOT_LB_MR01_SERVICE_DOCK_V004", "cr01": "ROOT_LB_CR01_SERVICE_DOCK_V007"},
        "v004": {"core": "ROOT_LB_RP01_DOCK_CORE_V004", "mr01": "ROOT_LB_MR01_SERVICE_DOCK_V005", "cr01": "ROOT_LB_CR01_SERVICE_DOCK_V008"},
    }
    required_root = roots[family][mode]
    if required_root not in objects:
        failures.append(f"missing root {required_root}")
    core_root = roots[family]["core"]
    if mode != "core" and core_root not in objects:
        failures.append(f"missing linked {core_root}")

    base = objects.get("SM_LB_RP01_DockBase")
    base_size = size_mm(base) if base else None
    if base_size is None or not close(base_size, [2600.0, 1400.0, 110.0]):
        failures.append(f"base mismatch {base_size}")

    expected = {
        "SCK_DockDatum": [0.0, 735.0, 310.0],
        "SCK_ChargeContact_L": [-120.0, 735.0, 340.0],
        "SCK_ChargeContact_R": [120.0, 735.0, 340.0],
        "SCK_NetworkContact": [0.0, 735.0, 390.0],
    }
    if mode == "cr01":
        expected.update({"SCK_WaterFill": [-210.0, 735.0, 280.0], "SCK_DirtyExtract": [210.0, 735.0, 280.0]})
    socket_results = {}
    for name, target in expected.items():
        obj = objects.get(name)
        actual = world_mm(obj) if obj else None
        passed = actual is not None and close(actual, target)
        socket_results[name] = {"expected_blender_mm": target, "actual_blender_mm": actual, "pass": passed}
        if not passed:
            failures.append(f"socket mismatch {name}: {actual}")

    controls = {}
    dock_width = {"min": [-1300.0, -1e9, -1e9], "max": [1300.0, 1e9, 1e9]}
    rack_access = {"min": [640.0, 700.0, 180.0], "max": [1185.0, 1210.0, 1340.0]}
    for name in ("SM_LB_RP01_DockDiagnosticsPanel", "SM_LB_RP01_DockServiceHMI", "SM_LB_RP01_DockEStop"):
        obj = objects.get(name)
        if not obj:
            failures.append(f"missing shared control {name}")
            continue
        bounds = bounds_mm(obj)
        within_width = bounds["min"][0] >= dock_width["min"][0] - 1.0 and bounds["max"][0] <= dock_width["max"][0] + 1.0
        clears_rack = not intersects(bounds, rack_access)
        controls[name] = {"bounds_blender_mm": bounds, "within_2600mm_width": within_width, "clears_mr01_rack_access": clears_rack}
        if not within_width or not clears_rack:
            failures.append(f"shared control packaging failed {name}: {controls[name]}")

    variant = {}
    if mode == "mr01":
        tools = sorted(o.name for o in objects if re.match(r"^SM_LB_MR01_T[1-8]_", o.name))
        cradles = sorted(o.name for o in objects if re.match(r"^SM_LB_MR01_DockToolCradle_\d\d$", o.name))
        rack_sockets = sorted(o.name for o in objects if re.match(r"^SCK_DockToolRack_\d\d$", o.name))
        pivots = {"PVT_DockCalibrationProbe": [0.0, 900.0, 950.0], "PVT_DockToolRackDoor": [500.0, 1000.0, 900.0], "PVT_DockWasteDrawer": [-500.0, 900.0, 420.0]}
        for name, target in pivots.items():
            actual = world_mm(objects.get(name)) if objects.get(name) else None
            if actual is None or not close(actual, target):
                failures.append(f"pivot mismatch {name}: {actual}")
        if [len(tools), len(cradles), len(rack_sockets)] != [8, 8, 8]:
            failures.append(f"eight-tool invariant failed: {len(tools)}/{len(cradles)}/{len(rack_sockets)}")
        variant = {"tools": tools, "cradles": cradles, "rack_sockets": rack_sockets, "pivots": pivots}
    elif mode == "cr01":
        shifted = [o.name for o in objects if o.get("lb_v005_robot_centred_shift_mm") == 1445.0]
        if len(shifted) != 60:
            failures.append(f"CR shifted-object count mismatch {len(shifted)}")
        variant = {"shifted_cleaning_object_count": len(shifted), "outside_envelope": "TBC"}

    linked_libraries = sorted(str(lib.filepath) for lib in bpy.data.libraries)
    linked_count = len([o for o in objects if o.library])
    expected_core_folder = "DockCore_Candidate_v003" if family == "v003" else "DockCore_Candidate_v004"
    if mode != "core" and (len(linked_libraries) != 1 or expected_core_folder not in linked_libraries[0] or linked_count != 97):
        failures.append(f"shared-core link mismatch: {linked_libraries}, objects={linked_count}")
    bad_scales = [o.name for o in objects if any(abs(v - 1.0) > 1e-6 for v in o.scale)]
    if bad_scales:
        failures.append(f"non-unit scales {bad_scales}")

    payload = {
        "$schema": f"cairnwell/validation/service-dock-family-{family}/{mode}/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__EXACT_INTERFACES_AND_SERVICE_APERTURE__VISUAL_UNREAL_RUNTIME_GATES_OPEN__NOT_PROMOTED" if not failures else "FAIL__SOURCE_GATE",
        "mode": mode,
        "blend": str(blend),
        "blend_sha256": sha256(blend),
        "base_size_blender_mm": base_size,
        "sockets": socket_results,
        "shared_controls": controls,
        "linked_libraries": linked_libraries,
        "linked_object_count": linked_count,
        "variant": variant,
        "bad_scales": bad_scales,
        "failures": failures,
        "fleet_requirement": {"cleaning_robots": 2, "cleaning_docks": 2, "maintenance_robots": 2, "maintenance_docks": 2},
        "holds": ["No Unreal intake yet", "No moving sweep/collision/navigation/charging proof yet", "CR01 v065 fit remains unproved", "No Press Shop placement promotion"],
        "promotion_authorized": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "failures": failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
