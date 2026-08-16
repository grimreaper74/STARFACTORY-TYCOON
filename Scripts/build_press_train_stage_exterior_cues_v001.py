"""Build four reusable operator-side process cue modules for enclosed press stages."""

import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PressTrains/Shared/StageExteriorCues_v001"
FBX = OUT / "FBX"
OUT.mkdir(parents=True, exist_ok=True)
FBX.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "MILLIMETERS"
scene.unit_settings.scale_length = 1.0

PALETTE = {
    "CA_MW_FoundryCharcoal": ((0.012, 0.016, 0.018, 1), 0.48, 0.58),
    "CA_MW_CairnwellGreen": ((0.008, 0.075, 0.052, 1), 0.30, 0.56),
    "CA_MW_SafetyYellow": ((0.80, 0.43, 0.006, 1), 0.18, 0.48),
    "CA_MW_ServiceGrey": ((0.075, 0.088, 0.092, 1), 0.55, 0.57),
    "CA_MW_WorkedSteel": ((0.13, 0.15, 0.16, 1), 0.88, 0.42),
    "CA_MW_InspectionGlass": ((0.005, 0.055, 0.060, 1), 0.10, 0.25),
    "CA_MW_TrainAAccent": ((0.020, 0.13, 0.34, 1), 0.25, 0.47),
    "CA_MW_StatusGreen": ((0.010, 0.44, 0.16, 1), 0.08, 0.30),
    "CA_MW_StatusAmber": ((0.95, 0.34, 0.01, 1), 0.08, 0.32),
}
materials = {}
for name, (colour, metallic, roughness) in PALETTE.items():
    material = bpy.data.materials.new(name)
    material.diffuse_color = colour
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    materials[name] = material


def box(parts, name, dims, loc, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=tuple(v / 1000 for v in loc))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = tuple(v / 1000 for v in dims)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(materials[material])
    if bevel:
        mod = obj.modifiers.new("FabricatedEdge", "BEVEL")
        mod.width = bevel / 1000
        mod.segments = 2
    parts.append(obj)
    return obj


def cylinder(parts, name, diameter, depth, loc, material, axis="Z", vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=diameter / 2000, depth=depth / 1000,
        location=tuple(v / 1000 for v in loc))
    obj = bpy.context.object
    obj.name = name
    if axis == "X":
        obj.rotation_euler[1] = math.radians(90)
    elif axis == "Y":
        obj.rotation_euler[0] = math.radians(90)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(materials[material])
    parts.append(obj)
    return obj


def finish(name, parts, role, cue):
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
    points = [[round(v * 1000, 3) for v in corner] for corner in obj.bound_box]
    minimum = [min(row[i] for row in points) for i in range(3)]
    maximum = [max(row[i] for row in points) for i in range(3)]
    path = FBX / f"{name}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
        use_mesh_modifiers=True, add_leaf_bones=False)
    record = {
        "asset": name, "file": str(path.relative_to(OUT)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        "measured_dimensions_mm": [round(v * 1000, 3) for v in obj.dimensions],
        "local_aabb_mm": {"min": minimum, "max": maximum},
        "role": role, "visual_process_cue": cue,
        "pivot": "facade module datum; X=operator-side depth, Y=stage transverse, Z=up",
        "collision_role": "no_collision_presentation_until_release_gate",
        "material_slots": [slot.material.name for slot in obj.material_slots],
    }
    bpy.data.objects.remove(obj, do_unlink=True)
    return record


assets = []

# S03 secondary forming: paired servo-pressure accumulators and a central manifold.
parts = []
box(parts, "S03Backplate", (180, 2220, 1780), (0, 0, 4050), "CA_MW_FoundryCharcoal", 38)
box(parts, "S03Manifold", (260, 920, 520), (-170, 0, 4050), "CA_MW_ServiceGrey", 28)
for y in (-690, 690):
    cylinder(parts, f"S03Accumulator_{y}", 480, 1120, (-210, y, 4200), "CA_MW_CairnwellGreen", vertices=28)
    cylinder(parts, f"S03Cap_{y}", 530, 120, (-210, y, 4760), "CA_MW_WorkedSteel", vertices=28)
    box(parts, f"S03Servo_{y}", (330, 360, 380), (-260, y, 3450), "CA_MW_TrainAAccent", 22)
for y in (-440, 0, 440):
    cylinder(parts, f"S03PressureLine_{y}", 86, 1320, (-360, y, 3920), "CA_MW_SafetyYellow", axis="Y", vertices=16)
box(parts, "S03Status", (110, 480, 130), (-390, 0, 4650), "CA_MW_StatusGreen", 12)
assets.append(finish(
    "SM_CA_MW_PT_S03SecondaryFormExteriorCue_v001", parts,
    "s03_secondary_form_operator_process_cue",
    "paired forming-pressure accumulators, servo blocks and manifold"))

# S04 trim: a visibly sloped guarded scrap chute and takeaway mouth.
parts = []
box(parts, "S04Backplate", (180, 2320, 1840), (0, 0, 2350), "CA_MW_FoundryCharcoal", 38)
box(parts, "S04TrimMouth", (330, 1500, 620), (-220, 0, 2750), "CA_MW_ServiceGrey", 34)
chute = box(parts, "S04ScrapChute", (430, 1920, 460), (-300, 160, 1980), "CA_MW_SafetyYellow", 28)
chute.rotation_euler[0] = math.radians(-12)
box(parts, "S04ScrapTakeaway", (520, 980, 720), (-330, 520, 1380), "CA_MW_CairnwellGreen", 34)
for y in (-760, 760):
    box(parts, f"S04ChuteGuard_{y}", (180, 130, 1150), (-420, y, 2130), "CA_MW_WorkedSteel", 15)
for y in (-540, 0, 540):
    box(parts, f"S04ShearWitness_{y}", (120, 260, 90), (-405, y, 2940), "CA_MW_StatusAmber", 10)
assets.append(finish(
    "SM_CA_MW_PT_S04TrimScrapExteriorCue_v001", parts,
    "s04_trim_press_operator_process_cue",
    "guarded trim mouth, sloped scrap chute and takeaway housing"))

# S05 pierce: four removable slug drawers with witness ports.
parts = []
box(parts, "S05Backplate", (180, 2260, 1900), (0, 0, 2320), "CA_MW_FoundryCharcoal", 38)
box(parts, "S05CollectorHeader", (300, 1840, 420), (-210, 0, 3000), "CA_MW_ServiceGrey", 25)
for y in (-660, -220, 220, 660):
    box(parts, f"S05SlugDrawer_{y}", (420, 360, 760), (-260, y, 2100), "CA_MW_CairnwellGreen", 24)
    box(parts, f"S05DrawerFace_{y}", (120, 250, 520), (-500, y, 2100), "CA_MW_ServiceGrey", 16)
    box(parts, f"S05Witness_{y}", (90, 120, 100), (-570, y, 2260), "CA_MW_StatusAmber", 9)
    box(parts, f"S05Handle_{y}", (90, 180, 55), (-580, y, 1900), "CA_MW_SafetyYellow", 8)
box(parts, "S05DropChannel", (320, 980, 500), (-220, 0, 1280), "CA_MW_WorkedSteel", 24)
assets.append(finish(
    "SM_CA_MW_PT_S05PierceSlugExteriorCue_v001", parts,
    "s05_pierce_press_operator_process_cue",
    "four removable slug-collection drawers, witness ports and drop channel"))

# S06 final restrike: calibrated load-cell towers and quality confirmation bar.
parts = []
box(parts, "S06Backplate", (180, 2240, 1780), (0, 0, 3980), "CA_MW_FoundryCharcoal", 38)
for y in (-720, -240, 240, 720):
    cylinder(parts, f"S06LoadCell_{y}", 260, 960, (-220, y, 4020), "CA_MW_WorkedSteel", vertices=24)
    cylinder(parts, f"S06LoadCap_{y}", 320, 110, (-220, y, 4500), "CA_MW_CairnwellGreen", vertices=24)
    box(parts, f"S06Signal_{y}", (100, 180, 90), (-390, y, 4350), "CA_MW_StatusGreen", 9)
box(parts, "S06QualityBar", (280, 1860, 300), (-230, 0, 3360), "CA_MW_TrainAAccent", 22)
for y in (-600, -200, 200, 600):
    box(parts, f"S06Gauge_{y}", (110, 260, 150), (-400, y, 3360), "CA_MW_StatusGreen", 10)
assets.append(finish(
    "SM_CA_MW_PT_S06RestrikeQualityExteriorCue_v001", parts,
    "s06_final_restrike_operator_process_cue",
    "four load-cell towers and a quality-confirmation signal bar"))

blend_path = OUT / "CA_MW_PressTrain_StageExteriorCues_v001.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
manifest = {
    "$schema": "cairnwell/source/press-train-stage-exterior-cues-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "authority": "Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md; Pro Sheets 04/05",
    "source_blend": blend_path.name,
    "coordinate_system": "local facade module coordinates; millimetres; world placement TBC",
    "design_model": "CCTV-first enclosed machinery with large stage-specific exterior process evidence",
    "world_placement": "TBC_NOT_INVENTED", "assets": assets,
    "promotion_authorized": False, "press_shop_complete": False,
}
(OUT / "PRESS_TRAIN_STAGE_EXTERIOR_CUES_MANIFEST_v001.json").write_text(
    json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({
    "status": "PASS__PRESS_TRAIN_STAGE_EXTERIOR_CUES_V001_BUILT__SOURCE_AUDIT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "asset_count": len(assets),
    "assets": [{"asset": row["asset"], "dimensions_mm": row["measured_dimensions_mm"]} for row in assets],
}, indent=2))
