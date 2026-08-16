"""Exact Blender-source gate for LB-MR01 service/tool dock candidate v001."""
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


def world_location_mm(obj: bpy.types.Object) -> list[float]:
    return [round(value * 1000.0, 3) for value in obj.matrix_world.translation]


def world_bounds_mm(obj: bpy.types.Object) -> dict:
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = [min(point[i] for point in points) * 1000.0 for i in range(3)]
    maximum = [max(point[i] for point in points) * 1000.0 for i in range(3)]
    return {
        "min": [round(value, 3) for value in minimum],
        "max": [round(value, 3) for value in maximum],
        "size": [round(maximum[i] - minimum[i], 3) for i in range(3)],
    }


def close(actual: list[float], expected: list[float], tolerance: float = 1.0) -> bool:
    return all(abs(actual[index] - expected[index]) <= tolerance for index in range(3))


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if not args:
        raise SystemExit("Output JSON path required")
    output = Path(args[0]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    blend = Path(bpy.data.filepath).resolve()

    failures: list[str] = []
    objects = bpy.data.objects
    base = objects.get("SM_LB_RP01_DockBase")
    if not base:
        failures.append("missing linked SM_LB_RP01_DockBase")
        base_bounds = None
    else:
        base_bounds = world_bounds_mm(base)
        if not close(base_bounds["size"], [2600.0, 1400.0, 110.0], 1.0):
            failures.append(f"shared base size mismatch: {base_bounds['size']}")

    expected_sockets = {
        "SCK_DockDatum": [0.0, 735.0, 310.0],
        "SCK_ChargeContact_L": [-120.0, 735.0, 340.0],
        "SCK_ChargeContact_R": [120.0, 735.0, 340.0],
        "SCK_NetworkContact": [0.0, 735.0, 390.0],
    }
    socket_results = {}
    for name, expected in expected_sockets.items():
        obj = objects.get(name)
        actual = world_location_mm(obj) if obj else None
        passed = actual is not None and close(actual, expected, 1.0)
        socket_results[name] = {"expected_blender_mm": expected, "actual_blender_mm": actual, "pass": passed}
        if not passed:
            failures.append(f"socket mismatch: {name}: {actual}")

    expected_pivots = {
        "PVT_DockCalibrationProbe": [0.0, 900.0, 950.0],
        "PVT_DockToolRackDoor": [500.0, 1000.0, 900.0],
        "PVT_DockWasteDrawer": [-500.0, 900.0, 420.0],
    }
    pivot_results = {}
    for name, expected in expected_pivots.items():
        obj = objects.get(name)
        actual = world_location_mm(obj) if obj else None
        passed = actual is not None and close(actual, expected, 1.0)
        pivot_results[name] = {"expected_blender_mm": expected, "actual_blender_mm": actual, "pass": passed}
        if not passed:
            failures.append(f"pivot mismatch: {name}: {actual}")

    required_parenting = {
        "SM_LB_MR01_DockCalibrationProbe": "PVT_DockCalibrationProbe",
        "SM_LB_MR01_DockToolRackDoor": "PVT_DockToolRackDoor",
        "SM_LB_MR01_DockWasteDrawer": "PVT_DockWasteDrawer",
    }
    parenting_results = {}
    for child_name, parent_name in required_parenting.items():
        child = objects.get(child_name)
        actual_parent = child.parent.name if child and child.parent else None
        passed = actual_parent == parent_name
        parenting_results[child_name] = {"expected_parent": parent_name, "actual_parent": actual_parent, "pass": passed}
        if not passed:
            failures.append(f"moving parent mismatch: {child_name}: {actual_parent}")

    tool_pattern = re.compile(r"^SM_LB_MR01_T([1-8])_")
    tools = sorted(obj.name for obj in objects if tool_pattern.match(obj.name))
    tool_ids = sorted(int(tool_pattern.match(name).group(1)) for name in tools)
    if tool_ids != list(range(1, 9)) or len(tools) != 8:
        failures.append(f"expected exactly T1-T8 once each, found {tools}")
    cradles = sorted(obj.name for obj in objects if re.match(r"^SM_LB_MR01_DockToolCradle_\d\d$", obj.name))
    if len(cradles) != 8:
        failures.append(f"expected eight tool cradles, found {len(cradles)}")
    rack_sockets = sorted(obj.name for obj in objects if re.match(r"^SCK_DockToolRack_\d\d$", obj.name))
    if len(rack_sockets) != 8:
        failures.append(f"expected eight rack sockets, found {len(rack_sockets)}")

    linked_libraries = sorted(str(library.filepath) for library in bpy.data.libraries)
    linked_objects = [obj.name for obj in objects if obj.library]
    linked_collections = sorted(collection.name for collection in bpy.data.collections if collection.library)
    if len(linked_libraries) != 1 or len(linked_objects) != 38:
        failures.append(f"shared link proof mismatch: libraries={linked_libraries}, linked_objects={len(linked_objects)}")
    for required_collection in ("LB_RP01_DOCK_SHARED", "LB_RP01_DOCK_SOCKETS"):
        if required_collection not in linked_collections:
            failures.append(f"missing linked collection {required_collection}")

    bad_scales = []
    for obj in objects:
        if any(abs(value - 1.0) > 1e-6 for value in obj.scale):
            bad_scales.append({"name": obj.name, "scale": [round(value, 6) for value in obj.scale]})
    if bad_scales:
        failures.append(f"non-unit object scales: {len(bad_scales)}")

    names_text = "\n".join(obj.name for obj in objects).lower()
    if "line boss" in names_text or "lineboss" in names_text:
        failures.append("forbidden in-world working-title token found")

    payload = {
        "$schema": "cairnwell/validation/mr01-service-dock-source-v001/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__SOURCE_DIMENSIONS_INTERFACES_PIVOTS_SHARED_LINK_AND_EIGHT_TOOLS__VISUAL_UNREAL_RUNTIME_GATES_OPEN__NOT_PROMOTED" if not failures
                  else "FAIL__SOURCE_GATE",
        "blend": str(blend),
        "blend_sha256": sha256(blend),
        "blender_version": bpy.app.version_string,
        "shared_base_bounds_mm": base_bounds,
        "sockets": socket_results,
        "pivots": pivot_results,
        "moving_parenting": parenting_results,
        "tools": tools,
        "tool_cradles": cradles,
        "tool_rack_sockets": rack_sockets,
        "linked_libraries": linked_libraries,
        "linked_collections": linked_collections,
        "linked_object_count": len(linked_objects),
        "bad_scales": bad_scales,
        "failures": failures,
        "fleet_installation_requirement": {"MR01_robots": 2, "MR01_dock_instances": 2},
        "holds": [
            "The linked RP01 dock core is a new candidate and has not yet been relinked into a CR01 successor.",
            "Visual, clean-reload/export, Unreal import, collision, navigation, charging/runtime and fixed-camera gates remain open.",
            "The Press Shop placement-capacity study does not install or promote either berth."
        ],
        "promotion_authorized": False,
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "failures": failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
