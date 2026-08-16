"""Build physical, reusable Press Train A-D identity signs for Blender/Unreal.

Visual-modelling dimensions are deliberately TBC.  Lettering is converted to mesh
before export so the Unreal assets do not inherit TextRender mirroring/back-face
problems seen in rejected map candidates v391 and v393.
"""

import bpy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/Candidate/PressShop/TrainIdentity/PhysicalSigns_v396"
FBX = OUT / "FBX"
OUT.mkdir(parents=True, exist_ok=True)
FBX.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "MILLIMETERS"
scene.unit_settings.scale_length = 1.0


def material(name, colour, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = colour
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


MATS = {
    "green": material("CA_MW_Identity_CairnwellGreen", (0.014, 0.105, 0.068, 1), 0.20, 0.31),
    "graphite": material("CA_MW_Identity_Graphite", (0.025, 0.032, 0.034, 1), 0.72, 0.28),
    "white": material("CA_MW_Identity_LetterWhite", (0.78, 0.86, 0.82, 1), 0.08, 0.34),
    "yellow": material("CA_MW_Identity_SafetyYellow", (0.98, 0.58, 0.015, 1), 0.22, 0.30),
}

font_path = Path(r"C:\Windows\Fonts\bahnschrift.ttf")
FONT = bpy.data.fonts.load(str(font_path)) if font_path.is_file() else None


def cube(parts, name, dims_mm, loc_mm, mat_key, bevel_mm=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=tuple(v / 1000.0 for v in loc_mm))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = tuple(v / 1000.0 for v in dims_mm)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(MATS[mat_key])
    if bevel_mm:
        mod = obj.modifiers.new("FabricatedEdge", "BEVEL")
        mod.width = bevel_mm / 1000.0
        mod.segments = 3
    parts.append(obj)
    return obj


def mesh_text(parts, name, text, size_mm, centre_y_mm, centre_z_mm, mat_key):
    bpy.ops.object.text_add(location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = text
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size_mm / 1000.0
    obj.data.extrude = 0.010
    obj.data.bevel_depth = 0.0018
    obj.data.bevel_resolution = 2
    obj.data.space_character = 1.0
    if FONT is not None:
        obj.data.font = FONT
    obj.data.materials.append(MATS[mat_key])
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    # Font XY face becomes sign YZ face; lettering projects from local -X.
    for vertex in obj.data.vertices:
        x, y, z = vertex.co
        vertex.co = (-z - 0.055, x + centre_y_mm / 1000.0, y + centre_z_mm / 1000.0)
    parts.append(obj)
    return obj


def export_sign(train):
    parts = []
    # Approximate visual envelope 2600 W x 760 H x 110 D mm; all values TBC.
    cube(parts, f"Train{train}_MainPanel", (110, 2600, 760), (0, 0, 0), "green", 34)
    cube(parts, f"Train{train}_InnerPanel", (18, 2440, 600), (-64, 0, 18), "graphite", 24)
    cube(parts, f"Train{train}_Accent", (22, 2440, 48), (-77, 0, -298), "yellow", 12)
    for y in (-1210, 1210):
        for z in (-300, 300):
            cube(parts, f"Train{train}_Fastener_{y}_{z}", (35, 44, 44), (-81, y, z), "yellow", 8)
    mesh_text(parts, f"Train{train}_Title", f"PRESS TRAIN {train}", 255, 0, 106, "white")
    mesh_text(parts, f"Train{train}_Stages", "S01  -  S07", 125, 0, -136, "white")

    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = f"SM_CA_MW_PressTrainIdentity_{train}_v396"
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")

    path = FBX / f"{obj.name}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, object_types={"MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True,
        mesh_smooth_type="FACE", add_leaf_bones=False, use_custom_props=True)
    record = {
        "asset": obj.name,
        "train": train,
        "file": str(path.relative_to(OUT)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        "measured_dimensions_mm": [round(v * 1000.0, 3) for v in obj.dimensions],
        "material_slots": [slot.material.name for slot in obj.material_slots],
        "lettering": f"PRESS TRAIN {train} / S01-S07",
        "collision_role": "NoCollision visual identity",
        "engineering_dimensions": "TBC_NOT_FOR_MANUFACTURING",
    }
    bpy.data.objects.remove(obj, do_unlink=True)
    return record


assets = [export_sign(train) for train in "ABCD"]
blend = OUT / "CA_MW_PressShop_PhysicalTrainIdentitySigns_v396.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
manifest = {
    "$schema": "cairnwell/source/press-shop-physical-train-identity-v396/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "purpose": "Reusable physical A-D train identity; replaces rejected TextRender experiments v391/v393",
    "authority": "Cairnwell/Moorcross visual identity only; all dimensions TBC",
    "source_blend": blend.name,
    "assets": assets,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
(OUT / "PHYSICAL_TRAIN_IDENTITY_MANIFEST_v396.json").write_text(
    json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "status": "PASS__FOUR_PHYSICAL_TRAIN_SIGNS_BUILT__UNREAL_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "asset_count": len(assets),
    "assets": [{"asset": row["asset"], "dimensions_mm": row["measured_dimensions_mm"]} for row in assets],
}, indent=2))
