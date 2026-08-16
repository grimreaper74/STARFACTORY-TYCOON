"""Build a review-only combined MR01 v022 + service dock v002 fit scene."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector


EXPECTED_ROBOT_SHA256 = "432233FA43ACB2D67A2E58DE8110272032D10EB53A82AF5971F8ACD3E895EBE8"
EXPECTED_DOCK_SHA256 = "A713BFF3451CB26EFF5A84483BE942E291137F517ACC197F2FB4C7850BDB97B1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def bounds(objects: list[bpy.types.Object]) -> dict:
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    minimum = [min(point[i] for point in points) * 1000.0 for i in range(3)]
    maximum = [max(point[i] for point in points) * 1000.0 for i in range(3)]
    return {
        "min_blender_mm": [round(value, 3) for value in minimum],
        "max_blender_mm": [round(value, 3) for value in maximum],
        "size_blender_mm": [round(maximum[i] - minimum[i], 3) for i in range(3)],
    }


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 4:
        raise SystemExit("Usage: -- dock_v002.blend output_review.blend audit.json render.png")
    dock_path = Path(args[0]).resolve()
    output = Path(args[1]).resolve()
    audit_path = Path(args[2]).resolve()
    render_path = Path(args[3]).resolve()
    robot_path = Path(bpy.data.filepath).resolve()
    robot_hash = sha256(robot_path)
    dock_hash = sha256(dock_path)
    expected_dock_hash = args[4].upper() if len(args) >= 5 else EXPECTED_DOCK_SHA256
    if robot_hash != EXPECTED_ROBOT_SHA256:
        raise RuntimeError(f"Unexpected MR01 v022 source hash: {robot_hash}")
    if dock_hash != expected_dock_hash:
        raise RuntimeError(f"Unexpected dock v002 hash: {dock_hash}")

    required = [
        "30_LB_MR01_DOCK_STATIC", "31_LB_MR01_DOCK_MOVING",
        "32_LB_MR01_DOCK_TOOLS", "50_LB_MR01_DOCK_SOCKETS_PIVOTS",
    ]
    with bpy.data.libraries.load(str(dock_path), link=True) as (source, target):
        missing = [name for name in required if name not in source.collections]
        if missing:
            raise RuntimeError(f"Dock collections missing: {missing}")
        target.collections = required
    for linked in target.collections:
        bpy.context.scene.collection.children.link(linked)
    shared_path = Path(args[5]).resolve() if len(args) >= 6 else (
        dock_path.parents[2] / "RP01" / "DockCore_Candidate_v001" / "LB_RP01_DockCore_v001.blend"
    )
    with bpy.data.libraries.load(str(shared_path), link=True) as (shared_source, shared_target):
        shared_required = ["LB_RP01_DOCK_SHARED", "LB_RP01_DOCK_SOCKETS"]
        shared_missing = [name for name in shared_required if name not in shared_source.collections]
        if shared_missing:
            raise RuntimeError(f"Shared dock-core collections missing: {shared_missing}")
        shared_target.collections = shared_required
    for linked in shared_target.collections:
        bpy.context.scene.collection.children.link(linked)
    bpy.context.view_layer.update()

    for name in ("90_LB_MR01_VALIDATION_REFERENCE", "91_LB_MR01_V013_EVIDENCE_ONLY"):
        collection = bpy.data.collections.get(name)
        if collection:
            collection.hide_render = True
            collection.hide_viewport = True
    for obj in list(bpy.data.objects):
        if obj.type in {"LIGHT", "CAMERA"}:
            bpy.data.objects.remove(obj, do_unlink=True)

    robot_collections = {
        "10_LB_RP01_EXACT_SHARED_LINKED", "20_LB_MR01_STATIC", "21_LB_MR01_MOVING",
        "22_LB_MR01_ARM_SKELETAL", "24_LB_MR01_FLEXIBLE_DRESS_CANDIDATE",
        "25_LB_MR01_V013_INSTALLED_TOOLS", "28_LB_MR01_V014_VISUAL_REWORK",
    }
    robot_meshes = [obj for obj in bpy.data.objects if obj.type == "MESH" and not obj.library and robot_collections.intersection(c.name for c in obj.users_collection)]
    robot_bounds = bounds(robot_meshes)
    robot_width = robot_bounds["size_blender_mm"][0]
    portal_width = 1260.0
    lateral_clearance = (portal_width - robot_width) / 2.0
    failures = []
    if abs(robot_width - 930.0) > 1.0:
        failures.append(f"robot width not 930 mm after v022 correction: {robot_width}")
    if lateral_clearance < 100.0:
        failures.append(f"dock portal lateral clearance below 100 mm each side: {lateral_clearance}")

    # The MR01 and dock share the same CFR and exact SCK_DockDatum. Confirm the
    # linked socket agrees with the retained robot socket rather than offsetting
    # presentation geometry by eye.
    socket_candidates = [obj for obj in bpy.data.objects if obj.name.startswith("SCK_DockDatum")]
    socket_results = []
    for obj in socket_candidates:
        socket_results.append({
            "name": obj.name,
            "library": str(obj.library.filepath) if obj.library else None,
            "blender_mm": [round(value * 1000.0, 3) for value in obj.matrix_world.translation],
        })
    if len(socket_candidates) < 2:
        failures.append(f"expected robot and dock datum sockets, found {len(socket_candidates)}")
    elif any(any(abs(a - b) > 1.0 for a, b in zip(socket_results[0]["blender_mm"], row["blender_mm"])) for row in socket_results[1:]):
        failures.append(f"robot/dock datum sockets disagree: {socket_results}")

    # Create review stage only; this file is never an import source.
    review = bpy.data.collections.new("99_LB_MR01_DOCK_FIT_REVIEW_ONLY")
    bpy.context.scene.collection.children.link(review)
    floor_mat = bpy.data.materials.new("M_CA_FitReview_SealedConcrete")
    floor_mat.diffuse_color = (0.12, 0.13, 0.135, 1.0)
    floor_mat.use_nodes = True
    floor_bsdf = floor_mat.node_tree.nodes.get("Principled BSDF")
    floor_bsdf.inputs["Base Color"].default_value = floor_mat.diffuse_color
    floor_bsdf.inputs["Roughness"].default_value = 0.74
    bpy.ops.mesh.primitive_plane_add(size=14.0, location=(0.0, 0.8, -0.015))
    floor = bpy.context.object
    floor.name = "REVIEW_ONLY_SealedConcrete"
    floor.data.materials.append(floor_mat)
    for source_collection in list(floor.users_collection):
        source_collection.objects.unlink(floor)
    review.objects.link(floor)

    for name, location, energy, size, colour in (
        ("REVIEW_Key", (-3.5, -3.0, 5.0), 1350.0, 4.0, (0.86, 0.93, 1.0)),
        ("REVIEW_Fill", (4.0, -1.0, 3.5), 950.0, 3.0, (1.0, 0.78, 0.55)),
        ("REVIEW_Top", (0.0, 2.0, 5.5), 1200.0, 3.5, (0.8, 0.9, 1.0)),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        data.color = colour
        light = bpy.data.objects.new(name, data)
        light.location = location
        review.objects.link(light)
        look_at(light, (0.0, 0.7, 0.7))
    camera_data = bpy.data.cameras.new("CAM_MR01_DockFitReview")
    camera_data.lens = 50.0
    camera = bpy.data.objects.new("CAM_MR01_DockFitReview", camera_data)
    camera.location = (3.9, -5.3, 2.65)
    review.objects.link(camera)
    look_at(camera, (0.0, 0.45, 0.72))
    bpy.context.scene.camera = camera

    world = bpy.context.scene.world or bpy.data.worlds.new("MR01_DockFitWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.025, 0.03, 0.035, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene["lb_review_only"] = True
    scene["lb_promotion_authorized"] = False

    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    render_path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(render_path)
    bpy.ops.render.render(write_still=True)

    payload = {
        "$schema": "cairnwell/audit/mr01-v022-service-dock-combined-fit-review/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__EXACT_DATUM_AND_STATIC_PORTAL_CLEARANCE__COMBINED_COLLISION_SWEEP_UNREAL_GATES_OPEN__NOT_PROMOTED" if not failures else "FAIL__COMBINED_STATIC_FIT_GATE",
        "robot_v022": str(robot_path),
        "robot_v022_sha256": robot_hash,
        "dock_source": str(dock_path),
        "dock_source_sha256": dock_hash,
        "shared_core_source": str(shared_path),
        "shared_core_source_sha256": sha256(shared_path),
        "review_blend": str(output),
        "review_blend_sha256": sha256(output),
        "render": str(render_path),
        "render_sha256": sha256(render_path),
        "robot_physical_bounds": robot_bounds,
        "portal_width_mm": portal_width,
        "lateral_clearance_each_side_mm": round(lateral_clearance, 3),
        "datum_sockets": socket_results,
        "failures": failures,
        "holds": [
            "This is a linked review scene, not an Unreal import source or production placement.",
            "Mesh-pair collision, moving door/probe/drawer sweeps and approach navigation remain open.",
            "Dock v002 and MR01 v022 remain below release visual fidelity and are not promoted.",
        ],
        "promotion_authorized": False,
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "clearance_each_side_mm": payload["lateral_clearance_each_side_mm"], "failures": failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
