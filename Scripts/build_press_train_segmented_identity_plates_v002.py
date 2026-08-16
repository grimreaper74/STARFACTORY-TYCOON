"""Build reusable fabricated stage plates with explicit segmented S01-S07 geometry."""

import bpy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PressTrains/Shared/SegmentedIdentityPlates_v002"
FBX = OUT / "FBX"
OUT.mkdir(parents=True, exist_ok=True)
FBX.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "MILLIMETERS"
scene.unit_settings.scale_length = 1.0

palette = {
    "CA_MW_TrainAccent": ((0.012, 0.085, 0.25, 1), 0.34, 0.46),
    "CA_MW_LabelWhite": ((0.76, 0.86, 0.82, 1), 0.18, 0.34),
    "CA_MW_WorkedSteel": ((0.11, 0.13, 0.14, 1), 0.88, 0.42),
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
        modifier.segments = 2
    parts.append(obj)
    return obj


SEGMENTS = {
    "S": "afgcd", "0": "abcedf", "1": "bc", "2": "abged",
    "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgecd", "7": "abc",
}


def glyph(parts, character, centre_y, prefix):
    # Plate is a YZ face. Raised character blocks sit in front at local -X.
    horizontal = {
        "a": (centre_y, 118), "g": (centre_y, 0), "d": (centre_y, -118),
    }
    vertical = {
        "f": (centre_y - 78, 60), "b": (centre_y + 78, 60),
        "e": (centre_y - 78, -60), "c": (centre_y + 78, -60),
    }
    for segment in SEGMENTS[character]:
        if segment in horizontal:
            y, z = horizontal[segment]
            box(parts, f"{prefix}_{segment}", (42, 170, 34), (-46, y, z), "CA_MW_LabelWhite", 8)
        else:
            y, z = vertical[segment]
            box(parts, f"{prefix}_{segment}", (42, 34, 108), (-46, y, z), "CA_MW_LabelWhite", 8)


def finish(code, parts):
    name = f"SM_CA_MW_PT_{code}SegmentedIdentityPlate_v002"
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
        "pivot": "physical plate centre; raised segments project toward local -X",
        "collision_role": "no_collision_identity_presentation",
        "material_slots": [slot.material.name for slot in obj.material_slots],
        "glyph_construction": "explicit bevelled cuboids; no font, texture, decal or TextRender dependency",
    }
    bpy.data.objects.remove(obj, do_unlink=True)
    return record


assets = []
for index in range(1, 8):
    code = f"S{index:02d}"
    parts = []
    box(parts, f"{code}_Plate", (58, 1180, 390), (0, 0, 0), "CA_MW_TrainAccent", 24)
    for y in (-525, 525):
        box(parts, f"{code}_Fastener_{y}", (78, 60, 60), (-8, y, 0), "CA_MW_WorkedSteel", 10)
    for character, centre_y in zip(code, (-310, 0, 310)):
        glyph(parts, character, centre_y, f"{code}_{character}_{centre_y}")
    assets.append(finish(code, parts))

blend_path = OUT / "CA_MW_PressTrain_SegmentedIdentityPlates_v002.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
manifest = {
    "$schema": "cairnwell/source/press-train-segmented-identity-plates-v002/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "authority": "Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md; Pro Sheets 04/05",
    "source_blend": blend_path.name,
    "coordinate_system": "physical plate centre; raised segments face local -X; millimetres",
    "reuse": "shared S01-S07 geometry; override train accent material for Train A-D",
    "world_placement": "TBC_NOT_INVENTED", "assets": assets,
    "promotion_authorized": False, "press_shop_complete": False,
}
(OUT / "PRESS_TRAIN_SEGMENTED_IDENTITY_PLATES_MANIFEST_v002.json").write_text(
    json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({
    "status": "PASS__SEVEN_SEGMENTED_STAGE_IDENTITY_PLATES_BUILT__SOURCE_AUDIT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "asset_count": len(assets),
    "assets": [{"asset": row["asset"], "dimensions_mm": row["measured_dimensions_mm"]} for row in assets],
}, indent=2))
