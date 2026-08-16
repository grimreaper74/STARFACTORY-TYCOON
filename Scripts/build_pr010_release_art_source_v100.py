"""Build dimensioned modular PR-010 v100 release-art source in Blender 5.2."""

import bpy
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v100"
FBX = OUT / "FBX"
OUT.mkdir(parents=True, exist_ok=True)
FBX.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "MILLIMETERS"
scene.unit_settings.scale_length = 1.0

palette = {
    "CA_MW_FoundryCharcoal": (0.018, 0.025, 0.028, 1),
    "CA_MW_CairnwellGreen": (0.025, 0.19, 0.145, 1),
    "CA_MW_SafetyYellow": (0.95, 0.57, 0.0, 1),
    "CA_MW_ServiceGrey": (0.42, 0.46, 0.48, 1),
    "CA_MW_WorkedSteel": (0.23, 0.27, 0.29, 1),
    "CA_MW_ScreenOnline": (0.01, 0.55, 0.40, 1),
    "CA_MW_SensorGlass": (0.01, 0.20, 0.22, 1),
    "CA_MW_White": (0.75, 0.78, 0.77, 1),
}
mats = {}
for name, colour in palette.items():
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = colour
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Metallic"].default_value = 0.75 if "Steel" in name or "Grey" in name else 0.15
    bsdf.inputs["Roughness"].default_value = 0.36 if "Steel" in name else 0.48
    mats[name] = mat

assets = {}


def box(name, dims_mm, loc_mm, material, rot_deg=(0, 0, 0), bevel_mm=0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=tuple(v / 1000 for v in loc_mm), rotation=tuple(math.radians(v) for v in rot_deg))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = tuple(v / 1000 for v in dims_mm)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mats[material])
    if bevel_mm:
        modifier = obj.modifiers.new("EdgeBevel", "BEVEL")
        modifier.width = bevel_mm / 1000
        modifier.segments = 2
    return obj


def cylinder(name, diameter_mm, depth_mm, loc_mm, material, axis="Z", vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=diameter_mm / 2000, depth=depth_mm / 1000, location=tuple(v / 1000 for v in loc_mm))
    obj = bpy.context.object
    obj.name = name
    if axis == "X": obj.rotation_euler[1] = math.radians(90)
    elif axis == "Y": obj.rotation_euler[0] = math.radians(90)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(mats[material])
    return obj


def torus(name, major_mm, minor_mm, loc_mm, material, rot_deg=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_mm/1000, minor_radius=minor_mm/1000, major_segments=32, minor_segments=10,
                                    location=tuple(v/1000 for v in loc_mm), rotation=tuple(math.radians(v) for v in rot_deg))
    obj = bpy.context.object; obj.name = name; obj.data.materials.append(mats[material]); return obj


def join_asset(asset, parts, expected_mm, notes):
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts: part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = asset
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # Every Unreal module uses the shared floor/datum origin authored above;
    # do not inherit the first joined part's offset as the FBX pivot.
    scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
    assets[asset] = {"object": obj, "expected_dimensions_mm": expected_mm, "notes": notes}
    return obj


# 2700 x 80 x 1200 mm framed open-grid guard panel; 180 mm clear grid.
parts = [
    box("GuardBottom", (2700, 80, 60), (0, 0, 30), "CA_MW_SafetyYellow", bevel_mm=8),
    box("GuardTop", (2700, 80, 60), (0, 0, 1170), "CA_MW_SafetyYellow", bevel_mm=8),
    box("GuardLeft", (60, 80, 1200), (-1320, 0, 600), "CA_MW_SafetyYellow", bevel_mm=8),
    box("GuardRight", (60, 80, 1200), (1320, 0, 600), "CA_MW_SafetyYellow", bevel_mm=8),
]
for x in range(-1170, 1171, 180): parts.append(box(f"MeshV{x}", (12, 18, 1080), (x, -5, 600), "CA_MW_WorkedSteel"))
for z in range(150, 1051, 180): parts.append(box(f"MeshH{z}", (2580, 18, 12), (0, -5, z), "CA_MW_WorkedSteel"))
join_asset("SM_CA_MW_PR010_GuardPanel_OpenMesh_v100", parts, [2700, 80, 1200], "Approved open-grid end protection; visual mesh only, v099 collision proxies retained")

# 2400 x 800 x 180 mm moving transfer cradle with real frame and rollers.
parts = [
    box("CradleSideL", (2400, 90, 120), (0, -355, 70), "CA_MW_SafetyYellow", bevel_mm=12),
    box("CradleSideR", (2400, 90, 120), (0, 355, 70), "CA_MW_SafetyYellow", bevel_mm=12),
    box("CradleCrossA", (120, 620, 100), (-1080, 0, 60), "CA_MW_FoundryCharcoal", bevel_mm=8),
    box("CradleCrossB", (120, 620, 100), (0, 0, 60), "CA_MW_FoundryCharcoal", bevel_mm=8),
    box("CradleCrossC", (120, 620, 100), (1080, 0, 60), "CA_MW_FoundryCharcoal", bevel_mm=8),
]
for y in (-280, -140, 0, 140, 280): parts.append(cylinder(f"CradleRoll{y}", 70, 2200, (0, y, 145), "CA_MW_WorkedSteel", axis="X", vertices=32))
parts.extend((box("CradleStopL", (80, 80, 180), (-1160, 0, 90), "CA_MW_SafetyYellow", bevel_mm=8), box("CradleStopR", (80, 80, 180), (1160, 0, 90), "CA_MW_SafetyYellow", bevel_mm=8)))
join_asset("SM_CA_MW_PR010_InfeedTransferCradle_v100", parts, [2400, 800, 180], "M01 moving body inside fixed 13 m shuttle envelope")

# Remote HMI housing at the authoritative coordination point.
parts = [
    box("HMIBase", (760, 500, 120), (0, 0, 60), "CA_MW_FoundryCharcoal", bevel_mm=18),
    box("HMIPost", (520, 360, 820), (0, 30, 500), "CA_MW_ServiceGrey", bevel_mm=20),
    # Keep the tilted operator face within the fixed 760 x 500 mm plan envelope.
    box("HMIConsole", (760, 450, 260), (0, 0, 990), "CA_MW_FoundryCharcoal", rot_deg=(-10, 0, 0), bevel_mm=22),
    box("HMIScreen", (590, 28, 320), (0, -205, 1130), "CA_MW_ScreenOnline", rot_deg=(-10, 0, 0), bevel_mm=10),
    box("HMIHeader", (700, 55, 210), (0, -200, 1390), "CA_MW_CairnwellGreen", bevel_mm=12),
    box("HMITrimL", (35, 45, 400), (-350, -190, 1130), "CA_MW_SafetyYellow"),
    box("HMITrimR", (35, 45, 400), (350, -190, 1130), "CA_MW_SafetyYellow"),
    cylinder("HMIEStop", 95, 65, (255, -210, 950), "CA_MW_SafetyYellow", axis="Y", vertices=32),
    cylinder("HMIBeacon", 90, 180, (0, 0, 1560), "CA_MW_SensorGlass", axis="Z", vertices=32),
]
join_asset("SM_CA_MW_PR010_RemoteHMIHousing_v100", parts, [760, 500, 1650], "Remote-only coordination HMI; screen UI remains Unreal-driven")

# Compact safety scanner.
parts = [
    box("ScannerBase", (220, 220, 80), (0, 0, 40), "CA_MW_FoundryCharcoal", bevel_mm=16),
    box("ScannerBody", (150, 140, 180), (0, 0, 150), "CA_MW_SafetyYellow", bevel_mm=14),
    box("ScannerLens", (120, 18, 70), (0, -78, 175), "CA_MW_SensorGlass", bevel_mm=8),
]
join_asset("SM_CA_MW_PR010_SafetyScanner_v100", parts, [220, 220, 240], "Four lane-end safety scanners")

# Recoverable tow point with visible forged loop.
parts = [
    box("TowBase", (240, 180, 50), (0, 0, 25), "CA_MW_FoundryCharcoal", bevel_mm=10),
    cylinder("TowStem", 70, 180, (0, 0, 130), "CA_MW_SafetyYellow", axis="Z", vertices=24),
    torus("TowLoop", 75, 18, (0, 0, 247), "CA_MW_SafetyYellow", rot_deg=(90, 0, 0)),
]
join_asset("SM_CA_MW_PR010_TowPoint_v100", parts, [240, 180, 340], "Recovery tow point at each lane end")

exports = []
for asset, data in assets.items():
    obj = data["object"]
    original = obj.location.copy()
    obj.location = (0, 0, 0)
    bpy.ops.object.select_all(action="DESELECT"); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    path = FBX / f"{asset}.fbx"
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                             bake_space_transform=False, add_leaf_bones=False, path_mode="AUTO", use_mesh_modifiers=True)
    obj.location = original
    dims = [round(value * 1000, 3) for value in obj.dimensions]
    exports.append({"asset": asset, "file": str(path.relative_to(OUT)), "bytes": path.stat().st_size, "measured_dimensions_mm": dims,
                    "expected_dimensions_mm": data["expected_dimensions_mm"], "notes": data["notes"], "material_slots": [slot.material.name for slot in obj.material_slots]})

blend = OUT / "CA_MW_PR010_ReleaseArt_v100.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
manifest = {
    "$schema": "cairnwell/source/pr010-release-art-v100/v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
    "station": "PR010", "source_blend": blend.name, "blender_version": bpy.app.version_string,
    "authority": "Pro Sheet 03 plus accepted v099 collision/navigation/runtime contracts",
    "assets": exports, "promotion_authorized": False,
}
(OUT / "PR010_RELEASE_ART_MANIFEST_v100.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({"status": "PASS__PR010_V100_DIMENSIONED_SOURCE_BUILT__UNREAL_GATES_REQUIRED__NOT_PROMOTED", "assets": len(exports), "blend": str(blend)}, indent=2))
