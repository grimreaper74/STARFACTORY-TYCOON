"""Build Sheet-03-directed PR-010 v102 service-deck and identity modules."""

import bpy
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v102"
FBX = OUT / "FBX"
OUT.mkdir(parents=True, exist_ok=True); FBX.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"; scene.unit_settings.length_unit = "MILLIMETERS"; scene.unit_settings.scale_length = 1.0

palette = {
    "CA_MW_FoundryCharcoal": (0.018, 0.025, 0.028, 1),
    "CA_MW_CairnwellGreen": (0.025, 0.19, 0.145, 1),
    "CA_MW_SafetyYellow": (0.95, 0.57, 0.0, 1),
    "CA_MW_ServiceGrey": (0.42, 0.46, 0.48, 1),
    "CA_MW_WorkedSteel": (0.23, 0.27, 0.29, 1),
    "CA_MW_ScreenOnline": (0.01, 0.55, 0.40, 1),
    "CA_MW_SensorGlass": (0.01, 0.20, 0.22, 1),
}
mats = {}
for name, colour in palette.items():
    mat = bpy.data.materials.new(name); mat.diffuse_color = colour; mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF"); bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Metallic"].default_value = 0.78 if "Steel" in name or "Grey" in name else 0.15
    bsdf.inputs["Roughness"].default_value = 0.42
    mats[name] = mat
assets = {}


def box(name, dims, loc, material, rot=(0, 0, 0), bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=tuple(v/1000 for v in loc), rotation=tuple(math.radians(v) for v in rot))
    obj = bpy.context.object; obj.name = name; obj.dimensions = tuple(v/1000 for v in dims)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); obj.data.materials.append(mats[material])
    if bevel:
        mod = obj.modifiers.new("EdgeBevel", "BEVEL"); mod.width = bevel/1000; mod.segments = 2
    return obj


def cylinder(name, diameter, depth, loc, material, axis="Z", vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=diameter/2000, depth=depth/1000, location=tuple(v/1000 for v in loc))
    obj = bpy.context.object; obj.name = name
    if axis == "X": obj.rotation_euler[1] = math.radians(90)
    elif axis == "Y": obj.rotation_euler[0] = math.radians(90)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True); obj.data.materials.append(mats[material]); return obj


def join_asset(name, parts, expected, notes, authority):
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts: part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.convert(target="MESH"); bpy.ops.object.join()
    obj = bpy.context.object; obj.name = name; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    scene.cursor.location = (0, 0, 0); bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
    assets[name] = {"object": obj, "expected_dimensions_mm": expected, "notes": notes, "authority": authority}


# Recommended presentation module contained inside the fixed 14,000 x 8,400 x 3,600 mm station envelope.
parts = [
    box("HousingFloor", (2900, 1200, 90), (0, 0, 45), "CA_MW_FoundryCharcoal", bevel=10),
    box("HousingRoof", (2900, 1200, 100), (0, 0, 850), "CA_MW_ServiceGrey", bevel=12),
    box("HousingRear", (2900, 70, 760), (0, 565, 450), "CA_MW_CairnwellGreen", bevel=8),
]
for x in (-1420, 1420): parts.append(box(f"HousingCorner{x}", (60, 1200, 900), (x, 0, 450), "CA_MW_FoundryCharcoal", bevel=6))
for x in (-960, 0, 960):
    parts.append(box(f"ServiceDoor{x}", (820, 55, 620), (x, -572, 390), "CA_MW_CairnwellGreen", bevel=10))
    for z in (170, 250, 330, 410, 490): parts.append(box(f"DoorVent{x}_{z}", (650, 22, 18), (x, -603, z), "CA_MW_WorkedSteel", bevel=2))
    parts.append(box(f"DoorHandle{x}", (24, 32, 180), (x+320, -624, 390), "CA_MW_SafetyYellow", bevel=3))
join_asset("SM_CA_MW_PR010_UpperServiceHousingSection_v102", parts, [2900, 1240, 900], "Four repeated upper service housings; panels/vents/handles", "Sheet 03 hero direction; recommended inside fixed station envelope")

# Grated access platform with open rails, never an opaque guard wall.
parts = [box("WalkwayDeck", (2900, 900, 100), (0, 0, 50), "CA_MW_WorkedSteel", bevel=5)]
for x in range(-1350, 1351, 150): parts.append(box(f"Grate{x}", (18, 820, 18), (x, 0, 110), "CA_MW_FoundryCharcoal"))
for x in (-1420, -710, 0, 710, 1420):
    parts.append(box(f"RailPost{x}", (55, 55, 1100), (x, -422, 650), "CA_MW_SafetyYellow", bevel=5))
for z in (680, 1180): parts.append(box(f"RailLong{z}", (2900, 55, 55), (0, -422, z), "CA_MW_SafetyYellow", bevel=5))
join_asset("SM_CA_MW_PR010_ServiceWalkwayRailSection_v102", parts, [2900, 900, 1208], "Open grated service platform and two-rail access edge", "Sheet 03 hero service-access direction; recommended")

# Rooftop drive pod and local disconnect details.
parts = [
    box("DriveBase", (1200, 800, 80), (0, 0, 40), "CA_MW_FoundryCharcoal", bevel=10),
    box("DriveBody", (1040, 680, 300), (0, 0, 220), "CA_MW_ServiceGrey", bevel=28),
    box("DriveTop", (900, 560, 90), (0, 0, 355), "CA_MW_FoundryCharcoal", bevel=20),
    box("Disconnect", (180, 80, 240), (420, -360, 190), "CA_MW_SafetyYellow", bevel=8),
]
for x in (-320, -160, 0, 160, 320): parts.append(box(f"DriveVent{x}", (80, 25, 180), (x, -352, 220), "CA_MW_WorkedSteel", bevel=2))
join_asset("SM_CA_MW_PR010_RoofDrivePod_v102", parts, [1200, 800, 400], "Repeated rooftop drive/utility pod", "Sheet 03 hero rooftop service direction; recommended")

# Cable tray and three colour-separated service routes.
parts = [box("RouteTray", (2900, 500, 80), (0, 0, 40), "CA_MW_WorkedSteel", bevel=6)]
for y, material in ((-150, "CA_MW_SafetyYellow"), (0, "CA_MW_CairnwellGreen"), (150, "CA_MW_ServiceGrey")):
    parts.append(cylinder(f"RoutePipe{y}", 90, 2800, (0, y, 180), material, axis="X", vertices=20))
for x in (-1350, -675, 0, 675, 1350): parts.append(box(f"RouteClamp{x}", (45, 500, 220), (x, 0, 140), "CA_MW_FoundryCharcoal", bevel=4))
join_asset("SM_CA_MW_PR010_RoofUtilityRoute_v102", parts, [2900, 500, 250], "Visible electrical/air/control service routing", "Sheet 03 utility interface and hero direction; recommended")

# Exact fixed pylon envelope from Sheet 03/module register.
parts = [
    box("PylonBase", (350, 350, 120), (0, 0, 60), "CA_MW_FoundryCharcoal", bevel=18),
    box("PylonBody", (310, 300, 1900), (0, 0, 1070), "CA_MW_CairnwellGreen", bevel=28),
    box("PylonHead", (350, 350, 300), (0, 0, 2050), "CA_MW_FoundryCharcoal", bevel=20),
    box("PylonScreen", (250, 24, 300), (0, -163, 1650), "CA_MW_ScreenOnline", bevel=8),
    box("PylonIDPlate", (250, 24, 260), (0, -163, 1180), "CA_MW_ServiceGrey", bevel=6),
    cylinder("PylonBeacon", 120, 180, (0, 0, 2110), "CA_MW_SensorGlass", axis="Z", vertices=24),
]
join_asset("SM_CA_MW_PR010_IDPylonDetailed_v102", parts, [350, 350, 2200], "Detailed four-lane reservation and identity pylon", "Sheet 03 Item 08 fixed 350 x 350 x 2200 mm envelope")

exports = []
for name, data in assets.items():
    obj = data["object"]; path = FBX / f"{name}.fbx"
    bpy.ops.object.select_all(action="DESELECT"); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True, add_leaf_bones=False)
    exports.append({"asset": name, "file": str(path.relative_to(OUT)), "bytes": path.stat().st_size,
        "measured_dimensions_mm": [round(v*1000, 3) for v in obj.dimensions], "expected_dimensions_mm": data["expected_dimensions_mm"],
        "notes": data["notes"], "authority": data["authority"], "material_slots": [slot.material.name for slot in obj.material_slots]})
blend = OUT / "CA_MW_PR010_ReleaseArt_v102.blend"; bpy.ops.wm.save_as_mainfile(filepath=str(blend))
manifest = {"$schema": "cairnwell/source/pr010-release-art-v102/v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
    "station": "PR010", "source_blend": blend.name, "blender_version": bpy.app.version_string,
    "authority": "Pro Sheet 03 plus retained v101 technical contracts", "assets": exports, "promotion_authorized": False}
(OUT / "PR010_RELEASE_ART_MANIFEST_v102.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({"status": "PASS__PR010_V102_SERVICE_DECK_SOURCE_BUILT__AUDIT_UNREAL_GATES_REQUIRED__NOT_PROMOTED", "assets": len(exports)}, indent=2))
