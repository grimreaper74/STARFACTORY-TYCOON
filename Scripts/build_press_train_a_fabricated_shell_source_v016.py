"""Build a midtone, segmented fabricated-shell successor from immutable v015.

This remains a fixed source-only visual overlay. It adds no movers, collision,
navigation or runtime authority and stays inside the proven v295 envelope.
"""

import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
PARENT_DIR = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/PresentationShell_v015"
PARENT = PARENT_DIR / "CA_MW_PressTrainA_PresentationShell_v015.blend"
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/PresentationShell_v016"
FBX_DIR = OUT / "FBX"
RENDERS = OUT / "Renders"
BLEND_OUT = OUT / "CA_MW_PressTrainA_PresentationShell_v016.blend"
FBX_OUT = FBX_DIR / "SM_CA_MW_PTA_PresentationShell_v016.fbx"
MANIFEST = OUT / "PRESS_TRAIN_A_PRESENTATION_SHELL_MANIFEST_v016.json"
VALIDATION = OUT / "PRESS_TRAIN_A_PRESENTATION_SHELL_VALIDATION_v016.json"
for path in (OUT, FBX_DIR, RENDERS):
    path.mkdir(parents=True, exist_ok=True)
if any(path.exists() for path in (BLEND_OUT, FBX_OUT, MANIFEST, VALIDATION)):
    raise RuntimeError("Refusing to overwrite immutable PresentationShell_v016")


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


bpy.ops.wm.open_mainfile(filepath=str(PARENT))
scene = bpy.context.scene
asset = bpy.data.objects.get("SM_CA_MW_PTA_PresentationShell_v015")
if asset is None:
    raise RuntimeError("v015 presentation shell missing")
asset.name = "SM_CA_MW_PTA_PresentationShell_v016"
collection = asset.users_collection[0]

# Retain the five-slot contract but move black/white extremes toward worked
# industrial midtones so detail survives the inherited Unreal hall exposure.
palette = {
    "Green": ((0.045, 0.19, 0.13, 1.0), 0.28, 0.48),
    "Graphite": ((0.15, 0.17, 0.18, 1.0), 0.38, 0.56),
    "DarkMachined": ((0.20, 0.22, 0.23, 1.0), 0.52, 0.43),
    "MachinedSteel": ((0.34, 0.37, 0.39, 1.0), 0.65, 0.38),
    "SafetyYellow": ((0.72, 0.36, 0.018, 1.0), 0.18, 0.50),
}
materials = {}
for material in asset.data.materials:
    key = next((token for token in palette if token.lower() in material.name.lower()), None)
    if key is None:
        raise RuntimeError(f"unmapped inherited material {material.name}")
    colour, metallic, roughness = palette[key]
    material.name = material.name.replace("v015", "v016")
    material.diffuse_color = colour
    material.metallic = metallic
    material.roughness = roughness
    node = material.node_tree.nodes.get("Principled BSDF") if material.use_nodes else None
    if node:
        node.inputs["Base Color"].default_value = colour
        node.inputs["Metallic"].default_value = metallic
        node.inputs["Roughness"].default_value = roughness
    materials[key] = material

parts = [asset]


def relink(obj):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def box(name, location, dimensions, material, bevel=0.04, segments=4, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    relink(obj)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("FabricatedEdge", "BEVEL")
        modifier.width = min(bevel, min(dimensions) * 0.22)
        modifier.segments = segments
    parts.append(obj)
    return obj


def cylinder(name, location, radius, depth, material, rotation=(0, math.pi / 2, 0), vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    relink(obj)
    obj.data.materials.append(material)
    modifier = obj.modifiers.new("MachinedEdge", "BEVEL")
    modifier.width = min(0.018, radius * 0.12)
    modifier.segments = 3
    parts.append(obj)
    return obj


stages = [("S02", 7.5, 10.5, 2.55), ("S03", 15.0, 8.2, 2.30), ("S04", 22.5, 8.2, 2.30), ("S05", 30.0, 8.2, 2.30), ("S06", 37.5, 8.2, 2.30)]
detail_count = 0
for stage, y, height, half_span in stages:
    face_x = 4.35 if stage == "S02" else 4.22
    crown_z = height - 0.82
    # Horizontal shadow reveals split the remaining crown mass into fabricated courses.
    for row, z_offset in enumerate((-0.46, 0.0, 0.46)):
        box(f"{stage}_CrownShadowReveal_{row}", (face_x + 0.326, y, crown_z + z_offset), (0.026, half_span * 1.02, 0.055), materials["Graphite"], 0.012, 3)
        detail_count += 1
    # Narrow vertical ribs and corner gussets replace uninterrupted rectangular reading.
    for side in (-1, 1):
        for rib_index, y_offset in enumerate((0.48, 0.92)):
            rib_y = y + side * y_offset
            box(f"{stage}_CrownRib_{side}_{rib_index}", (face_x + 0.34, rib_y, crown_z), (0.045, 0.085, 1.03), materials["MachinedSteel"], 0.018, 3)
            detail_count += 1
        gusset_y = y + side * (half_span - 0.56)
        box(f"{stage}_UpperGusset_{side}", (face_x + 0.28, gusset_y, crown_z - 0.68), (0.10, 0.56, 0.46), materials["DarkMachined"], 0.07, 5, rotation=(side * 0.18, 0, 0))
        box(f"{stage}_LowerKnee_{side}", (face_x + 0.25, gusset_y, 4.45 if stage == "S02" else 3.65), (0.12, 0.48, 0.72), materials["Graphite"], 0.09, 5, rotation=(side * -0.20, 0, 0))
        detail_count += 2
    # Vent banks and service badges give the large cheek areas a believable function.
    for side in (-1, 1):
        bank_y = y + side * 1.36
        box(f"{stage}_VentBack_{side}", (face_x + 0.319, bank_y, 4.35 if stage == "S02" else 3.55), (0.028, 0.46, 0.78), materials["DarkMachined"], 0.035, 3)
        for slot, z_offset in enumerate((-0.25, -0.125, 0.0, 0.125, 0.25)):
            box(f"{stage}_VentBlade_{side}_{slot}", (face_x + 0.344, bank_y, (4.35 if stage == "S02" else 3.55) + z_offset), (0.024, 0.37, 0.035), materials["MachinedSteel"], 0.008, 2)
            detail_count += 1
        detail_count += 1
    # Repeated fastener rows reinforce a built-up steel assembly rather than a toy block.
    for side in (-1, 1):
        for bolt, z_offset in enumerate((-0.42, 0.0, 0.42)):
            cylinder(f"{stage}_CheekFastener_{side}_{bolt}", (face_x + 0.355, y + side * 1.72, crown_z + z_offset), 0.045, 0.035, materials["MachinedSteel"], vertices=24)
            detail_count += 1
    # A narrow curved-cap suggestion breaks the perfectly flat roof line.
    for side in (-1, 1):
        box(f"{stage}_CrownCapStep_{side}", (face_x, y + side * 0.72, crown_z + 0.79), (0.42, 0.62, 0.13), materials["DarkMachined"], 0.06, 5)
        detail_count += 1

bpy.ops.object.select_all(action="DESELECT")
for part in parts:
    part.select_set(True)
bpy.context.view_layer.objects.active = asset
bpy.ops.object.convert(target="MESH")
bpy.ops.object.join()
asset = bpy.context.object
asset.name = "SM_CA_MW_PTA_PresentationShell_v016"
asset["role"] = "fixed_visual_presentation_shell"
asset["collision_intent"] = "NoCollision"
asset["runtime_authority"] = "retained_components_only"
asset["engineering_status"] = "GAME_VISUAL_DETAIL_TBC"
bpy.context.scene.cursor.location = (0, 0, 0)
bpy.ops.object.origin_set(type="ORIGIN_CURSOR")

bpy.ops.object.select_all(action="DESELECT")
asset.select_set(True)
bpy.context.view_layer.objects.active = asset
bpy.ops.export_scene.fbx(filepath=str(FBX_OUT), use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True, mesh_smooth_type="FACE", add_leaf_bones=False, use_custom_props=True, object_types={"MESH"})

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.world.color = (0.025, 0.03, 0.035)


def look(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


camera_data = bpy.data.cameras.new("PTA_v016_Camera")
camera = bpy.data.objects.new("PTA_v016_Camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
for name, location, target, energy, size in (
    ("Key", (13, -1, 11), (3, 23, 4), 1150, 9),
    ("Fill", (11, 40, 8), (3, 23, 4), 900, 10),
    ("Roof", (4, 23, 16), (3, 23, 4), 1250, 11),
):
    data = bpy.data.lights.new("PTA_v016_" + name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    light = bpy.data.objects.new("PTA_v016_" + name, data)
    scene.collection.objects.link(light)
    light.location = location
    look(light, target)


def render(filename, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look(camera, target)
    scene.render.filepath = str(RENDERS / filename)
    bpy.ops.render.render(write_still=True)


render("01_operator_segmented_v016.png", (14, -3, 7.0), (3.5, 23, 4.5), 58)
render("02_mid_train_segmented_v016.png", (10.5, 17, 5.6), (4.0, 23, 4.2), 62)
render("03_management_segmented_v016.png", (17, 18, 12.5), (3.0, 23, 4.4), 58)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT), check_existing=False)

local_bounds = {
    "min": [min(value[index] for value in asset.bound_box) for index in range(3)],
    "max": [max(value[index] for value in asset.bound_box) for index in range(3)],
}
manifest = {
    "$schema": "cairnwell/source/press-train-presentation-shell-v016/v1",
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SOURCE_ONLY_SEGMENTED_MIDTONE_SHELL__UNREAL_INTAKE_REQUIRED__NOT_PROMOTED",
    "parent_v015_sha256": sha(PARENT),
    "asset_name": asset.name,
    "added_detail_part_count": detail_count,
    "vertices": len(asset.data.vertices),
    "polygons": len(asset.data.polygons),
    "local_bounds_m": local_bounds,
    "material_slots": [material.name for material in asset.data.materials],
    "collision_intent": "NoCollision",
    "retained_authorities_edited": False,
    "moving_parts_duplicated": False,
    "unverified_engineering_values_adopted": False,
    "fbx": {"file": "FBX/" + FBX_OUT.name, "bytes": FBX_OUT.stat().st_size, "sha256": sha(FBX_OUT)},
    "renders": ["Renders/01_operator_segmented_v016.png", "Renders/02_mid_train_segmented_v016.png", "Renders/03_management_segmented_v016.png"],
}
MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
failures = []
if detail_count < 100:
    failures.append(f"insufficient segmentation detail {detail_count}")
if local_bounds["max"][0] > 4.95 or local_bounds["min"][0] < 3.70:
    failures.append(f"X envelope escaped {local_bounds}")
if local_bounds["max"][1] > 40.2 or local_bounds["min"][1] < 3.7:
    failures.append(f"Y envelope escaped {local_bounds}")
if local_bounds["max"][2] > 10.75 or local_bounds["min"][2] < 0.25:
    failures.append(f"Z envelope escaped {local_bounds}")
if len(asset.data.materials) != 5:
    failures.append(f"material slot contract changed {len(asset.data.materials)}")
validation = {
    "status": "PASS__V016_SEGMENTED_MIDTONE_FIXED_SHELL_SOURCE__UNREAL_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V016_SOURCE_NOT_RETAINED",
    "asset_count": 1,
    "stage_count": 5,
    "added_detail_part_count": detail_count,
    "vertices": len(asset.data.vertices),
    "polygons": len(asset.data.polygons),
    "local_bounds_m": local_bounds,
    "material_slot_count": len(asset.data.materials),
    "collision_intent": "NoCollision",
    "retained_authorities_edited": False,
    "promotion_authorized": False,
    "failures": failures,
}
VALIDATION.write_text(json.dumps(validation, indent=2), encoding="utf-8")
print(json.dumps(validation, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
