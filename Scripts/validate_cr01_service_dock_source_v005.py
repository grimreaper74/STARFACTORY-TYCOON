"""Exact source gate for robot-centred linked-core CR01 service dock v005."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector


EXPECTED_V004_SHA256 = "2FD9789F8352C763F3EB4EB779C176BC9B06D0A56E87A22E221ADEDF1E430C90"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def world_mm(obj: bpy.types.Object) -> list[float]:
    return [round(value * 1000.0, 3) for value in obj.matrix_world.translation]


def close(actual: list[float], expected: list[float], tolerance: float = 1.0) -> bool:
    return all(abs(actual[index] - expected[index]) <= tolerance for index in range(3))


def bounds_mm(obj: bpy.types.Object) -> list[float]:
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = [min(point[i] for point in points) for i in range(3)]
    maximum = [max(point[i] for point in points) for i in range(3)]
    return [round((maximum[i] - minimum[i]) * 1000.0, 3) for i in range(3)]


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        raise SystemExit("Usage: -- immutable_v004.blend output_validation.json")
    v004 = Path(args[0]).resolve()
    output = Path(args[1]).resolve()
    blend = Path(bpy.data.filepath).resolve()
    failures = []
    if sha256(v004) != EXPECTED_V004_SHA256:
        failures.append("immutable CR01 v004 source hash changed")

    root = bpy.data.objects.get("ROOT_LB_CR01_SERVICE_DOCK_V005")
    if not root:
        failures.append("missing v005 root")
    expected = {
        "SCK_DockDatum": [0.0, 735.0, 310.0],
        "SCK_ChargeContact_L": [-120.0, 735.0, 340.0],
        "SCK_ChargeContact_R": [120.0, 735.0, 340.0],
        "SCK_NetworkContact": [0.0, 735.0, 390.0],
        "SCK_WaterFill": [-210.0, 735.0, 280.0],
        "SCK_DirtyExtract": [210.0, 735.0, 280.0],
    }
    socket_results = {}
    for name, expected_location in expected.items():
        obj = bpy.data.objects.get(name)
        actual = world_mm(obj) if obj else None
        passed = actual is not None and close(actual, expected_location)
        socket_results[name] = {"expected_blender_mm": expected_location, "actual_blender_mm": actual, "pass": passed}
        if not passed:
            failures.append(f"socket mismatch {name}: {actual}")

    base = bpy.data.objects.get("SM_LB_RP01_DockBase")
    base_size = bounds_mm(base) if base else None
    if base_size is None or not close(base_size, [2600.0, 1400.0, 110.0]):
        failures.append(f"linked shared base size mismatch: {base_size}")

    linked_libraries = sorted(str(library.filepath) for library in bpy.data.libraries)
    linked_objects = [obj.name for obj in bpy.data.objects if obj.library]
    linked_collections = sorted(collection.name for collection in bpy.data.collections if collection.library)
    if len(linked_libraries) != 1 or len(linked_objects) != 38:
        failures.append(f"shared link proof mismatch: libraries={linked_libraries}, linked_objects={len(linked_objects)}")
    for name in ("LB_RP01_DOCK_SHARED", "LB_RP01_DOCK_SOCKETS"):
        if name not in linked_collections:
            failures.append(f"missing linked collection {name}")
    for old_name in ("10_LB_RP01_DOCK_SHARED_STATIC", "11_LB_RP01_DOCK_SHARED_MOVING"):
        if old_name in bpy.data.collections:
            failures.append(f"superseded local common collection remains: {old_name}")

    shifted = [obj.name for obj in bpy.data.objects if obj.get("lb_v005_robot_centred_shift_mm") == 1445.0]
    cleaning_static = bpy.data.collections.get("20_LB_CR01_DOCK_STATIC")
    cleaning_moving = bpy.data.collections.get("21_LB_CR01_DOCK_MOVING")
    expected_shift_count = (len(cleaning_static.objects) if cleaning_static else 0) + (len(cleaning_moving.objects) if cleaning_moving else 0) + 2
    if len(shifted) != expected_shift_count:
        failures.append(f"robot-centred shift coverage mismatch: shifted={len(shifted)}, expected={expected_shift_count}")

    bad_scales = []
    for obj in bpy.data.objects:
        if any(abs(value - 1.0) > 1e-6 for value in obj.scale):
            bad_scales.append({"name": obj.name, "scale": [round(value, 6) for value in obj.scale]})
    if bad_scales:
        failures.append(f"non-unit object scales: {len(bad_scales)}")
    names_text = "\n".join(obj.name for obj in bpy.data.objects).lower()
    if "line boss" in names_text or "lineboss" in names_text:
        failures.append("forbidden in-world working-title token found")

    payload = {
        "$schema": "cairnwell/validation/cr01-service-dock-source-v005/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__ROBOT_CENTRED_LINKED_SHARED_CORE_AND_SIX_EXACT_INTERFACES__VISUAL_UNREAL_RUNTIME_GATES_OPEN__NOT_PROMOTED" if not failures else "FAIL__SOURCE_GATE",
        "blend": str(blend),
        "blend_sha256": sha256(blend),
        "immutable_v004": str(v004),
        "immutable_v004_sha256": sha256(v004),
        "shared_base_size_blender_mm": base_size,
        "sockets": socket_results,
        "linked_libraries": linked_libraries,
        "linked_collections": linked_collections,
        "linked_object_count": len(linked_objects),
        "shifted_cleaning_object_count": len(shifted),
        "bad_scales": bad_scales,
        "failures": failures,
        "fleet_installation_requirement": {"CR01_robots": 2, "CR01_dock_instances": 2},
        "holds": [
            "CR01 outside envelope remains TBC because the supplied sheets conflict.",
            "Actual CR01 v065 fit, visual review, clean export/reimport, Unreal collision, navigation, charging/wet-service runtime and fixed-camera gates remain open.",
            "The Press Shop capacity study does not install or promote either berth."
        ],
        "promotion_authorized": False
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "failures": failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
