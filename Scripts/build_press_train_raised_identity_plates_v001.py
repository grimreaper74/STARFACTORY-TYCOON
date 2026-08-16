"""Build reusable fabricated stage plates with raised S01-S07 mesh lettering."""

import bpy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PressTrains/Shared/RaisedIdentityPlates_v001"
FBX = OUT / "FBX"
OUT.mkdir(parents=True, exist_ok=True)
FBX.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "MILLIMETERS"
scene.unit_settings.scale_length = 1.0

palette = {
    "CA_MW_TrainAccent": ((0.018, 0.12, 0.31, 1), 0.30, 0.47),
    "CA_MW_LabelWhite": ((0.70, 0.78, 0.75, 1), 0.12, 0.38),
    "CA_MW_WorkedSteel": ((0.12, 0.14, 0.15, 1), 0.86, 0.44),
}
materials = {}
for name, (colour, metallic, roughness) in palette.items():
    material = bpy.data.materials.new(name)
    material.diffuse_color = colour
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    materials[name] = material

font_path = Path(r"C:\Windows\Fonts\bahnschrift.ttf")
font = bpy.data.fonts.load(str(font_path)) if font_path.is_file() else None


def box(parts, name, dims, loc, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=tuple(value / 1000 for value in loc))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = tuple(value / 1000 for value in dims)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(materials[material])
    if bevel:
        modifier = obj.modifiers.new("FabricatedEdge", "BEVEL")
        modifier.width = bevel / 1000
        modifier.segments = 3
    parts.append(obj)
    return obj


def raised_text(parts, code):
    bpy.ops.object.text_add(location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = f"Raised_{code}"
    obj.data.body = code
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = 0.255
    obj.data.extrude = 0.012
    obj.data.bevel_depth = 0.004
    obj.data.bevel_resolution = 2
    if font is not None:
        obj.data.font = font
    obj.data.materials.append(materials["CA_MW_LabelWhite"])
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    # Font is authored in XY with +Z depth. Map it to a facade plane:
    # local X -> world Y, local Y -> world Z, local Z -> world -X.
    for vertex in obj.data.vertices:
        x, y, z = vertex.co
        vertex.co = (-z - 0.031, x, y)
    parts.append(obj)


def finish(code, parts):
    name = f"SM_CA_MW_PT_{code}RaisedIdentityPlate_v001"
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
    points = [[round(value * 1000, 3) for value in corner] for corner in obj.bound_box]
    minimum = [min(row[index] for row in points) for index in range(3)]
    maximum = [max(row[index] for row in points) for index in range(3)]
    path = FBX / f"{name}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
        use_mesh_modifiers=True, add_leaf_bones=False)
    record = {
        "asset": name, "stage_code": code,
        "file": str(path.relative_to(OUT)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        "measured_dimensions_mm": [round(value * 1000, 3) for value in obj.dimensions],
        "local_aabb_mm": {"min": minimum, "max": maximum},
        "pivot": "physical plate centre; raised lettering faces local -X",
        "collision_role": "no_collision_identity_presentation",
        "material_slots": [slot.material.name for slot in obj.material_slots],
    }
    bpy.data.objects.remove(obj, do_unlink=True)
    return record


assets = []
for index in range(1, 8):
    code = f"S{index:02d}"
    parts = []
    box(parts, f"{code}_Plate", (50, 1200, 400), (0, 0, 0), "CA_MW_TrainAccent", 28)
    for y in (-520, 520):
        box(parts, f"{code}_Fastener_{y}", (72, 58, 58), (-10, y, 0), "CA_MW_WorkedSteel", 10)
    raised_text(parts, code)
    assets.append(finish(code, parts))

blend_path = OUT / "CA_MW_PressTrain_RaisedIdentityPlates_v001.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
manifest = {
    "$schema": "cairnwell/source/press-train-raised-identity-plates-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "authority": "Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md; Pro Sheets 04/05",
    "source_blend": blend_path.name,
    "coordinate_system": "physical plate centre; raised lettering faces local -X; millimetres",
    "reuse": "shared S01-S07 plate geometry; train accent material overridden per Train A-D",
    "world_placement": "TBC_NOT_INVENTED", "assets": assets,
    "promotion_authorized": False, "press_shop_complete": False,
}
(OUT / "PRESS_TRAIN_RAISED_IDENTITY_PLATES_MANIFEST_v001.json").write_text(
    json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({
    "status": "PASS__SEVEN_RAISED_STAGE_IDENTITY_PLATES_BUILT__SOURCE_AUDIT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "asset_count": len(assets),
    "assets": [{"asset": row["asset"], "dimensions_mm": row["measured_dimensions_mm"]} for row in assets],
}, indent=2))
