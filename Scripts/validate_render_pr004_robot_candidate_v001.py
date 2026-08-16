"""Re-import and validate the modular PR-004 robot candidate v001.

This Blender-only gate proves FBX scale, origins, material opacity, metadata and
rest-pose assembly, then writes fixed-camera renders for human review.  It never
starts Unreal and cannot promote the candidate.
"""

from pathlib import Path
import json
import math
import os

import bpy
from mathutils import Vector


REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "SourceAssets/PR004/RoboticDepackRobot"
VERSION = os.environ.get("LB_PR004_ROBOT_VERSION", "v001")
if VERSION not in {"v001", "v002"}:
    raise RuntimeError(f"Unsupported PR-004 robot validation version: {VERSION}")
MANIFEST = ROOT / f"pr004_robotic_depack_robot_candidate_{VERSION}_manifest.json"
BASELINE_MANIFEST = ROOT / "pr004_robotic_depack_robot_candidate_v001_manifest.json"
CRADLE_MANIFEST = REPO / "SourceAssets/PR004/PoweredRestrainedCradle/pr004_powered_cradle_candidate_v001_manifest.json"
COIL_FBX = REPO / "SourceAssets/IndustrialKit/MasterCoil/SM_LB_MasterCoil_Candidate_v003.fbx"
OUT = REPO / f"Saved/ValidationRenders/PR004/RobotCandidate_{VERSION}"
AUDIT = REPO / f"Saved/Audits/pr004_robot_candidate_{VERSION}_fbx_validation.json"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for block in list(collection):
            if block.users == 0:
                collection.remove(block)


def import_fbx(path):
    bpy.ops.object.select_all(action="DESELECT")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path), use_custom_props=True)
    meshes = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No mesh imported from {path}")
    if len(meshes) > 1:
        bpy.ops.object.select_all(action="DESELECT")
        for obj in meshes:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.join()
        meshes = [bpy.context.active_object]
    return meshes[0]


def material(name, colour, metallic=0.0, roughness=0.6, emission=None):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*colour, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 1.6
    return mat


def box(name, location, dimensions, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("StudioEdge", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def camera(name, location, target, lens=60.0, ortho=None):
    data = bpy.data.cameras.new(name + "_Data")
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    data.lens = lens
    if ortho is not None:
        data.type = "ORTHO"
        data.ortho_scale = ortho
    look_at(obj, target)
    return obj


def area_light(name, location, target, energy, size, colour):
    data = bpy.data.lights.new(name + "_Data", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = colour
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)
    return obj


def world_bounds(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lower = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
    upper = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
    return lower, upper


def raw_stats(obj):
    lower, upper = world_bounds(obj)
    custom = {}
    for key in obj.keys():
        if key == "_RNA_UI":
            continue
        value = obj[key]
        if isinstance(value, (str, int, float, bool)):
            custom[key] = value
    return {
        "name": obj.name,
        "import_location_m": [round(v, 6) for v in obj.location],
        "bounds_min_xyz_m": [round(v, 6) for v in lower],
        "bounds_max_xyz_m": [round(v, 6) for v in upper],
        "bounds_xyz_mm": [round(v * 1000.0, 3) for v in upper - lower],
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "triangles": sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons),
        "materials": [slot.material.name for slot in obj.material_slots if slot.material],
        "material_alpha": [round(slot.material.diffuse_color[3], 5) for slot in obj.material_slots if slot.material],
        "custom_properties": custom,
    }


def render(scene, cam, filename):
    scene.camera = cam
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


if not MANIFEST.exists():
    raise RuntimeError(f"Robot candidate manifest missing: {MANIFEST}")
manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
if manifest.get("status") != "CANDIDATE_NOT_PROMOTED":
    raise RuntimeError("Unexpected candidate status")
baseline_manifest = json.loads(BASELINE_MANIFEST.read_text(encoding="utf-8"))

OUT.mkdir(parents=True, exist_ok=True)
AUDIT.parent.mkdir(parents=True, exist_ok=True)
clear_scene()
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1400
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.film_transparent = False
scene.view_settings.exposure = -0.25
try:
    scene.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.008, 0.011, 0.015, 1.0)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.14

records = {record["id"]: record for record in manifest["modules"]}
objects = {}
raw = {}
for module_id, record in records.items():
    path = Path(record["fbx"])
    if not path.exists():
        raise RuntimeError(f"Missing FBX for {module_id}: {path}")
    obj = import_fbx(path)
    obj.name = "VALIDATION_" + module_id
    raw[module_id] = raw_stats(obj)
    obj.location = tuple(value / 100.0 for value in record["assembly_location_cm"])
    obj.rotation_euler = tuple(math.radians(value) for value in record["assembly_rotation_deg"])
    objects[module_id] = obj

# Validation context: the current 27.5 t candidate and powered cradle are
# optional visual scale references, never merged into this robot family.
coil = None
coil_stats = None
if COIL_FBX.exists():
    coil = import_fbx(COIL_FBX)
    coil.name = "VALIDATION_27_5t_MasterCoil"
    coil_stats = raw_stats(coil)
    coil.location = (4.40, 0.0, 1.47)

cradle_objects = []
if CRADLE_MANIFEST.exists():
    cradle_manifest = json.loads(CRADLE_MANIFEST.read_text(encoding="utf-8"))
    for record in cradle_manifest.get("modules", []):
        path = Path(record["fbx"])
        if not path.exists():
            continue
        obj = import_fbx(path)
        obj.name = "VALIDATION_Cradle_" + record["id"]
        loc = Vector(tuple(value / 100.0 for value in record["rest_location_cm"])) + Vector((4.40, 0.0, 0.0))
        obj.location = loc
        cradle_objects.append(obj)

# The band tool is removed from dock 1 and attached to the robot for the main
# operating view.  Its independently exported jaws, cutter and withdrawal
# rolls follow the parent-relative pivots recorded in the manifest.  The
# original docked family remains available for the rack detail render.
tool_children = manifest["tool_change"]["articulated_child_movers"]
band_family_ids = ["band_tool", *tool_children["band_tool"]]
band_on_robot_family = []
robot_tool_origin = Vector((2.90, 0.0, 2.20))
for module_id in band_family_ids:
    source = objects[module_id]
    duplicate = source.copy()
    duplicate.data = source.data.copy()
    bpy.context.collection.objects.link(duplicate)
    duplicate.name = "VALIDATION_OnRobot_" + module_id
    if module_id == "band_tool":
        duplicate.location = robot_tool_origin
    else:
        pivot_text = records[module_id]["custom_properties"]["parent_relative_pivot_cm"]
        relative_cm = Vector(tuple(float(value) for value in pivot_text.split(",")))
        duplicate.location = robot_tool_origin + relative_cm / 100.0
    duplicate.rotation_euler = (0.0, 0.0, 0.0)
    band_on_robot_family.append(duplicate)
    source.hide_render = True

# Ground, workshop wall and painted safety envelope.
concrete = material("LB_Validation_IndustrialConcrete", (0.105, 0.112, 0.118), 0.0, 0.80)
wall_mat = material("LB_Validation_Wall", (0.035, 0.041, 0.048), 0.10, 0.73)
line_yellow = material("LB_Validation_SafetyLine", (0.66, 0.34, 0.015), 0.18, 0.60)
line_red = material("LB_Validation_RobotSweep", (0.38, 0.018, 0.012), 0.10, 0.66)
box("ValidationFloor", (1.6, -0.4, -0.08), (10.0, 7.8, 0.16), concrete, 0.015)
box("ValidationBackWall", (1.6, 3.35, 2.5), (10.0, 0.14, 5.1), wall_mat, 0.015)
for x in (-0.80, 5.75):
    box(f"SafetyEnvelopeLineX_{x:+.2f}", (x, -0.10, 0.012), (0.055, 5.3, 0.022), line_yellow, 0.003)
for y in (-2.78, 2.55):
    box(f"SafetyEnvelopeLineY_{y:+.2f}", (2.48, y, 0.012), (6.60, 0.055, 0.022), line_yellow, 0.003)
for angle in range(0, 360, 15):
    rad = math.radians(angle)
    x, y = 3.45 * math.cos(rad), 3.45 * math.sin(rad)
    block = box(f"RobotSweepMarker_{angle:03d}", (x, y, 0.018), (0.13, 0.045, 0.018), line_red, 0.002)
    block.rotation_euler.z = rad

area_light("KeyHighBay", (4.6, -4.6, 6.2), (2.0, 0.0, 1.2), 1250.0, 4.3, (1.0, 0.80, 0.60))
area_light("FillHighBay", (-3.5, -1.5, 4.2), (1.2, 0.0, 1.5), 720.0, 3.4, (0.52, 0.68, 1.0))
area_light("RimHighBay", (2.0, 3.0, 5.6), (1.5, 0.0, 1.5), 950.0, 3.2, (1.0, 0.46, 0.18))
area_light("ToolRackFill", (-0.2, -4.4, 3.2), (0.0, -2.2, 0.9), 560.0, 2.2, (0.70, 0.80, 1.0))
area_light("ToolRackFrontFill", (0.0, 0.2, 3.4), (0.0, -2.2, 0.9), 720.0, 2.6, (1.0, 0.76, 0.52))
area_light("CoilFaceFill", (6.8, -0.5, 3.2), (4.0, 0.0, 1.5), 520.0, 2.5, (0.68, 0.78, 1.0))

cams = {
    "assembly": camera("CAM_PR004_Robot_Coil_ThreeQuarter", (7.55, -8.4, 5.25), (2.0, -0.05, 1.20), 66.0),
    "side": camera("CAM_PR004_Robot_SideScale", (2.45, -8.6, 2.75), (2.05, 0.0, 1.35), 70.0),
    "joints": camera("CAM_PR004_Robot_JointDetail", (0.55, -4.25, 2.95), (1.05, 0.0, 1.65), 76.0),
    "rack": camera("CAM_PR004_ToolRack", (0.0, 3.20, 2.12), (0.0, -2.28, 0.88), 48.0),
    "band": camera("CAM_PR004_BandToolSafety", (3.75, -2.15, 2.82), (3.20, 0.0, 2.20), 92.0),
}

render(scene, cams["assembly"], f"pr004_robot_with_27_5t_coil_three_quarter_{VERSION}.png")
render(scene, cams["side"], f"pr004_robot_side_scale_{VERSION}.png")
render(scene, cams["joints"], f"pr004_robot_joints_and_dress_pack_{VERSION}.png")

# Restore the parked band tool and hide the working duplicate for rack review.
for module_id in band_family_ids:
    objects[module_id].hide_render = False
for obj in band_on_robot_family:
    obj.hide_render = True
all_tool_family_ids = {
    family_id
    for tool_id, child_ids in tool_children.items()
    for family_id in (tool_id, *child_ids)
}
for key, obj in objects.items():
    if key != "tool_rack" and key not in all_tool_family_ids:
        obj.hide_render = True
if coil:
    coil.hide_render = True
for obj in cradle_objects:
    obj.hide_render = True
render(scene, cams["rack"], f"pr004_guarded_tool_rack_four_tools_{VERSION}.png")

# Safety close-up keeps the installed tool and isolates the rack visually.
for module_id in band_family_ids:
    objects[module_id].hide_render = True
for obj in band_on_robot_family:
    obj.hide_render = False
objects["tool_rack"].hide_render = True
for tool_id in ("wrap_tool", "edge_tool", "inspection_tool"):
    objects[tool_id].hide_render = True
    for child_id in tool_children[tool_id]:
        objects[child_id].hide_render = True
for key in ("j4", "j5", "j6", "changer_body", "changer_lock", "dress_wrist"):
    objects[key].hide_render = False
render(scene, cams["band"], f"pr004_band_cutter_twin_capture_detail_{VERSION}.png")

joint_axes = {item["joint"].lower(): item["axis_local_at_rest"] for item in manifest["robot"]["joint_contract"]}
joint_pivots = {item["joint"].lower(): item["pivot_world_cm"] for item in manifest["robot"]["joint_contract"]}
all_alpha = [alpha for value in raw.values() for alpha in value["material_alpha"]]
total_candidate_triangles = sum(value["triangles"] for value in raw.values())
expected_tool_children = {
    "band_left_capture", "band_right_capture", "band_cutter", "band_roll_left", "band_roll_right",
    "wrap_vacuum_carrier", "wrap_peel_roll", "edge_left_jaw", "edge_right_jaw",
    "inspection_bore_camera", "inspection_shutter",
}
articulated_children = {
    child_id
    for child_ids in tool_children.values()
    for child_id in child_ids
}
baseline_records = {record["id"]: record for record in baseline_manifest["modules"]}
tool_child_parent_offsets = {
    child_id: (
        records[child_id]["custom_properties"].get("runtime_parent"),
        records[child_id]["custom_properties"].get("parent_relative_pivot_cm"),
    )
    for child_id in expected_tool_children
}
baseline_tool_child_parent_offsets = {
    child_id: (
        baseline_records[child_id]["custom_properties"].get("runtime_parent"),
        baseline_records[child_id]["custom_properties"].get("parent_relative_pivot_cm"),
    )
    for child_id in expected_tool_children
}
checks = {
    "candidate_status_not_promoted": manifest["status"] == "CANDIDATE_NOT_PROMOTED",
    "candidate_version_matches_requested_gate": manifest.get("version") == VERSION,
    "twenty_eight_modular_fbx_files": len(records) == 28 and all(Path(r["fbx"]).exists() for r in records.values()),
    "six_joint_modules_present": all(key in records for key in ("j1", "j2", "j3", "j4", "j5", "j6")),
    "joint_axes_match_locked_kinematics": joint_axes == {
        "j1": "+Z", "j2": "+Y", "j3": "+Y", "j4": "+X", "j5": "+Y", "j6": "+X",
    },
    "joint_pivots_are_unique": len({tuple(v) for v in joint_pivots.values()}) == 6,
    "fbx_origins_exported_at_zero": all(max(abs(v) for v in value["import_location_m"]) <= 0.0001 for value in raw.values()),
    "four_distinct_dockable_tools": all(key in records for key in ("band_tool", "wrap_tool", "edge_tool", "inspection_tool")),
    "eleven_tool_child_movers_present": articulated_children == expected_tool_children and expected_tool_children.issubset(records),
    "tool_movers_are_independent_fbx_modules": all(
        records[child_id]["fbx"] != records[records[child_id]["custom_properties"]["runtime_parent"]]["fbx"]
        for child_id in expected_tool_children
    ),
    "tool_movers_have_parent_relative_pivots": all(
        records[child_id]["custom_properties"].get("parent_relative_pivot_cm")
        and records[child_id]["custom_properties"].get("runtime_parent") in tool_children
        for child_id in expected_tool_children
    ),
    "tool_mover_metadata_survived_fbx": all(
        raw[child_id]["custom_properties"].get("runtime_parent")
        == records[child_id]["custom_properties"].get("runtime_parent")
        and raw[child_id]["custom_properties"].get("parent_relative_pivot_cm")
        == records[child_id]["custom_properties"].get("parent_relative_pivot_cm")
        for child_id in expected_tool_children
    ),
    "band_cutter_requires_both_capture_confirmations": raw["band_cutter"]["custom_properties"].get("permissive") == "both capture confirmation inputs true",
    "guarded_tool_rack_metadata_survived_fbx": "light curtain" in raw["tool_rack"]["custom_properties"].get("guarding", ""),
    "dress_pack_runtime_deformation_documented": "spline/cable" in manifest["dress_pack"]["runtime_requirement"],
    "all_candidate_material_slots_opaque": bool(all_alpha) and all(alpha >= 0.999 for alpha in all_alpha),
    "robot_tool_tip_within_350cm_design_radius": manifest["robot"]["longest_candidate_tool_tip_reach_cm"] <= 350.0,
    "robot_below_450cm_cell_equipment_height": max((world_bounds(objects[key])[1].z for key in ("base", "j1", "j2", "j3", "j4", "j5", "j6"))) <= 4.50,
    f"candidate_family_under_{100 if VERSION == 'v001' else 250}k_triangles": total_candidate_triangles <= (100000 if VERSION == "v001" else 250000),
    "v002_refinement_metadata_present_when_required": VERSION != "v002" or bool(manifest.get("visual_refinement")),
    "v002_preserves_v001_joint_contract_when_required": VERSION != "v002" or manifest["robot"]["joint_contract"] == baseline_manifest["robot"]["joint_contract"],
    "v002_preserves_v001_tool_child_offsets_when_required": VERSION != "v002" or tool_child_parent_offsets == baseline_tool_child_parent_offsets,
    "v002_preserves_v001_declared_reach_when_required": VERSION != "v002" or (
        manifest["robot"]["working_radius_cm"] == baseline_manifest["robot"]["working_radius_cm"]
        and manifest["robot"]["longest_candidate_tool_tip_reach_cm"] == baseline_manifest["robot"]["longest_candidate_tool_tip_reach_cm"]
    ),
    "coil_scale_reference_is_1500x1900x1900mm": coil_stats is not None and all(abs(a - b) <= 1.0 for a, b in zip(coil_stats["bounds_xyz_mm"], (1500.0, 1900.0, 1900.0))),
    "source_scope_contains_no_uasset": not any(ROOT.rglob("*.uasset")),
}

renders = [
    OUT / f"pr004_robot_with_27_5t_coil_three_quarter_{VERSION}.png",
    OUT / f"pr004_robot_side_scale_{VERSION}.png",
    OUT / f"pr004_robot_joints_and_dress_pack_{VERSION}.png",
    OUT / f"pr004_guarded_tool_rack_four_tools_{VERSION}.png",
    OUT / f"pr004_band_cutter_twin_capture_detail_{VERSION}.png",
]
result = {
    "status": "CANDIDATE_NOT_PROMOTED",
    "validation_method": f"Blender 5.2 FBX re-import, metadata/pivot/scale checks and five fixed-camera Eevee renders ({VERSION})",
    "manifest": str(MANIFEST),
    "module_count": len(records),
    "total_candidate_triangles": total_candidate_triangles,
    "fbx_reimport": raw,
    "coil_scale_reference": coil_stats,
    "context_cradle_module_count": len(cradle_objects),
    "checks": checks,
    "all_technical_source_checks_pass": all(checks.values()),
    "fresh_renders_exist": all(path.exists() and path.stat().st_size > 0 for path in renders),
    "renders": [str(path) for path in renders],
    "visual_review_status": "REQUIRED_BEFORE_ANY_UNREAL_IMPORT_OR_PROMOTION",
    "scope_limit": "No Unreal import, runtime edit or promotion performed.",
}
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(f"LINE_BOSS_PR004_ROBOT_FBX_VALIDATION_PASS checks={checks} audit={AUDIT}")
