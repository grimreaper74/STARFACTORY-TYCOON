"""Validate exact sockets/base and fabricated-detail inventory of RP01 core v002."""
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
    return [round(value * 1000.0, 3) for value in obj.matrix_world.translation]


def size_mm(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return [round((max(point[i] for point in points) - min(point[i] for point in points)) * 1000.0, 3) for i in range(3)]


def close(actual, expected, tolerance=1.0):
    return all(abs(actual[i] - expected[i]) <= tolerance for i in range(3))


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args:
        raise SystemExit("Output validation JSON required")
    output = Path(args[0]).resolve()
    blend = Path(bpy.data.filepath).resolve()
    objects = bpy.data.objects
    failures = []
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
    sockets = {}
    for name, target in expected.items():
        obj = objects.get(name)
        actual = world_mm(obj) if obj else None
        passed = actual is not None and close(actual, target)
        sockets[name] = {"expected_blender_mm": target, "actual_blender_mm": actual, "pass": passed}
        if not passed:
            failures.append(f"socket mismatch {name}: {actual}")
    required = [
        "ROOT_LB_RP01_DOCK_CORE_V002", "SM_LB_RP01_DockCanopy", "SM_LB_RP01_DockCanopyFrontFascia",
        "SM_LB_RP01_DockRearServiceDoor_L", "SM_LB_RP01_DockRearServiceDoor_R",
        "SM_LB_RP01_DockOverheadCableTray", "SM_LB_RP01_DockFamilyPlate",
    ]
    missing = [name for name in required if name not in objects]
    if missing:
        failures.append(f"missing v002 fabricated detail: {missing}")
    task_lights = sorted(obj.name for obj in objects if re.match(r"^SM_LB_RP01_DockTaskLight_", obj.name))
    anchor_plates = sorted(obj.name for obj in objects if re.match(r"^SM_LB_RP01_DockAnchorPlate_", obj.name))
    if len(task_lights) != 3:
        failures.append(f"expected three task-light fixtures, found {len(task_lights)}")
    if len(anchor_plates) != 4:
        failures.append(f"expected four anchor plates, found {len(anchor_plates)}")
    bad_scales = [obj.name for obj in objects if any(abs(value - 1.0) > 1e-6 for value in obj.scale)]
    if bad_scales:
        failures.append(f"non-unit scales: {bad_scales}")
    payload = {
        "$schema": "cairnwell/validation/rp01-dock-core-source-v002/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__EXACT_SHARED_BASE_AND_SOCKETS_WITH_FABRICATED_DETAIL__VARIANT_VISUAL_UNREAL_GATES_OPEN__NOT_PROMOTED" if not failures else "FAIL__SOURCE_GATE",
        "blend": str(blend),
        "blend_sha256": sha256(blend),
        "object_count": len(objects),
        "base_size_blender_mm": base_size,
        "sockets": sockets,
        "required_detail": required,
        "missing_detail": missing,
        "task_lights": task_lights,
        "anchor_plates": anchor_plates,
        "bad_scales": bad_scales,
        "failures": failures,
        "promotion_authorized": False
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "objects": payload["object_count"], "failures": failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
