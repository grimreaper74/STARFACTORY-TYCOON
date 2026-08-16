"""Build the dimensioned semantic PR-010 four-lane Blender/FBX blockout source."""

import bpy
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PR010/FourLaneBuffer/Blockout_v001"
EXPORTS = OUT / "FBX"
OUT.mkdir(parents=True, exist_ok=True)
EXPORTS.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "MILLIMETERS"
scene.unit_settings.scale_length = 1.0

palette = {
    "CairnwellGreen": (0.025, 0.19, 0.145, 1),
    "FoundryCharcoal": (0.025, 0.035, 0.038, 1),
    "SafetyYellow": (0.95, 0.57, 0.0, 1),
    "ServiceGrey": (0.46, 0.50, 0.50, 1),
    "WorkedSteel": (0.23, 0.27, 0.29, 1),
    "BlankSteel": (0.48, 0.53, 0.55, 1),
    "StatusGreen": (0.02, 0.75, 0.30, 1),
    "StatusAmber": (1.0, 0.42, 0.0, 1),
    "Glass": (0.02, 0.25, 0.24, 0.45),
}
materials = {}
for name, colour in palette.items():
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = colour
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Metallic"].default_value = 0.75 if name in {"WorkedSteel", "BlankSteel", "ServiceGrey"} else 0.15
    bsdf.inputs["Roughness"].default_value = 0.42
    if name == "Glass":
        bsdf.inputs["Alpha"].default_value = 0.45
        mat.surface_render_method = "DITHERED"
    materials[name] = mat

asset_templates = {}
asset_specs = {}
placements = []


def box_template(asset, dims_mm, material):
    if asset in asset_templates:
        return asset_templates[asset]
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = asset
    obj.dimensions = tuple(value / 1000.0 for value in dims_mm)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(materials[material])
    asset_templates[asset] = obj
    asset_specs[asset] = {"shape": "box", "dimensions_mm": list(dims_mm), "material": material}
    return obj


def cylinder_template(asset, length_mm, diameter_mm, axis, material):
    if asset in asset_templates:
        return asset_templates[asset]
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=diameter_mm / 2000.0, depth=length_mm / 1000.0)
    obj = bpy.context.object
    obj.name = asset
    if axis == "X": obj.rotation_euler[1] = math.radians(90)
    if axis == "Y": obj.rotation_euler[0] = math.radians(90)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(materials[material])
    asset_templates[asset] = obj
    asset_specs[asset] = {
        "shape": "cylinder", "length_mm": length_mm, "diameter_mm": diameter_mm,
        "axis": axis, "material": material,
    }
    return obj


def place(asset, name, location_mm, tags, material=None, dims_mm=None, kind="box", **shape):
    if kind == "box":
        template = box_template(asset, dims_mm, material)
    else:
        template = cylinder_template(asset, shape["length_mm"], shape["diameter_mm"], shape["axis"], material)
    obj = template if not any(row["asset"] == asset for row in placements) else template.copy()
    if obj is not template:
        obj.data = template.data
        scene.collection.objects.link(obj)
    obj.name = name
    obj.location = tuple(value / 1000.0 for value in location_mm)
    obj["semantic_asset"] = asset
    obj["station"] = "PR010"
    placements.append({
        "asset": asset,
        "object": name,
        "location_mm": list(location_mm),
        "rotation_deg": [0.0, 0.0, 0.0],
        "tags": tags,
    })


# Station deck and dimensioned equipment envelope markers.
place("SM_CA_MW_PR010_Deck", "PR010_Deck", (0, 0, 40), ["fixed", "deck"], "FoundryCharcoal", (14000, 8400, 80))
place("SM_CA_MW_PR010_ServiceCorridor", "PR010_ServiceCorridor", (0, -4900, 45), ["service_corridor", "navigation_neutral"], "SafetyYellow", (14000, 1400, 20))
place("SM_CA_MW_PR010_HandoffApron", "PR010_HandoffApron", (0, 4700, 45), ["agv_handoff", "external_apron"], "ServiceGrey", (13500, 2400, 20))

# High-energy infeed shuttle and reusable enclosure spine.
place("SM_CA_MW_PR010_ShuttleBed", "PR010_M01_InfeedShuttle", (0, -3300, 350), ["moving_infeed_shuttle", "M01"], "WorkedSteel", (13000, 1000, 650))
for x in range(-6000, 6001, 1000):
    place("SM_CA_MW_PR010_ShuttleDeckPad", f"PR010_ShuttlePad_{x:+05d}", (x, -3300, 690), ["shuttle_deck"], "BlankSteel", (800, 800, 30))
for x in (-6800, -3400, 0, 3400, 6800):
    place("SM_CA_MW_PR010_SpineColumn", f"PR010_SpineColumn_{x:+05d}", (x, -3825, 1800), ["enclosure_structure"], "FoundryCharcoal", (180, 180, 3500))
place("SM_CA_MW_PR010_UtilitySpine", "PR010_UpperUtilitySpine", (0, -3825, 3375), ["enclosure_structure", "utility_spine"], "CairnwellGreen", (13800, 350, 350))
for bay_index, x in enumerate((-4800, -1600, 1600, 4800), start=1):
    place("SM_CA_MW_PR010_ShuttleRearPanel", f"PR010_ShuttleUpperFascia_{bay_index}", (x, -4100, 2925), ["enclosure_panel", "upper_fascia"], "CairnwellGreen", (2900, 80, 750))
    place("SM_CA_MW_PR010_ShuttleGlazing", f"PR010_ShuttleInspectionGlazing_{bay_index}", (x, -4050, 1900), ["inspection_glazing", "controlled_aperture"], "Glass", (2900, 25, 1200))

# Four fixed lanes, two stack positions per lane, stops, gates and CCTV-readable pylons.
lane_centres = [-4500, -1500, 1500, 4500]
lane_names = ["A", "B", "C", "D"]
for lane_x, lane in zip(lane_centres, lane_names):
    place("SM_CA_MW_PR010_LaneBed", f"PR010_Lane{lane}_Bed", (lane_x, 0, 300), ["lane_bed", f"lane_{lane}"], "FoundryCharcoal", (2400, 6200, 420))
    for y in range(-2700, 2701, 450):
        place("SM_CA_MW_PR010_CarrierRoller", f"PR010_Lane{lane}_Roller_{y:+05d}", (lane_x, y, 560), ["moving_carrier_roller", "M02", f"lane_{lane}"], "WorkedSteel", kind="cylinder", length_mm=2200, diameter_mm=160, axis="X")
    for pos_index, y in enumerate((-1800, 1800), start=1):
        place("SM_CA_MW_PR010_CarrierBase", f"PR010_Lane{lane}_Carrier_{pos_index}", (lane_x, y, 690), ["carrier_position", f"lane_{lane}"], "SafetyYellow", (2400, 1900, 180))
        place("SM_CA_MW_PR010_BlankStack", f"PR010_Lane{lane}_Stack_{pos_index}", (lane_x, y, 1030), ["identified_blank_stack", f"lane_{lane}"], "BlankSteel", (2200, 1700, 500))
        for side in (-1, 1):
            place("SM_CA_MW_PR010_StopPin", f"PR010_Lane{lane}_Stop_{pos_index}_{side:+d}", (lane_x + side * 1050, y + 850, 720), ["moving_stop_pin", "M03", f"lane_{lane}"], "SafetyYellow", (100, 100, 500))
    place("SM_CA_MW_PR010_LanePylon", f"PR010_Lane{lane}_IdentityPylon", (lane_x, 0, 1100), ["lane_identity", f"lane_{lane}"], "CairnwellGreen", (350, 350, 2200))
    place("SM_CA_MW_PR010_StatusLens", f"PR010_Lane{lane}_StatusLens", (lane_x, -180, 2025), ["status_indicator", f"lane_{lane}"], "StatusGreen", (220, 80, 180))
    place("SM_CA_MW_PR010_GateArm", f"PR010_Lane{lane}_ReservationGate", (lane_x, 2950, 1050), ["moving_reservation_gate", "M05", f"lane_{lane}"], "SafetyYellow", (2200, 100, 120))

# HMI, crossing control, quality-hold spur and recovery cues.
place("SM_CA_MW_PR010_HMIPedestal", "PR010_CoordinationHMI_Pedestal", (6450, -3250, 640), ["coordination_hmi", "service_side"], "ServiceGrey", (600, 460, 1280))
place("SM_CA_MW_PR010_HMIScreen", "PR010_CoordinationHMI_Screen", (6450, -3485, 1120), ["interactive_hmi"], "StatusGreen", (420, 25, 260))
place("SM_CA_MW_PR010_CrossingBar", "PR010_ControlledCrossing", (0, -5000, 1000), ["controlled_crossing", "normally_closed"], "SafetyYellow", (12000, 100, 120))
place("SM_CA_MW_PR010_QualitySpur", "PR010_M06_QualityHoldSpur", (-6200, 3500, 350), ["moving_quality_spur", "M06"], "FoundryCharcoal", (2700, 2100, 500))
place("SM_CA_MW_PR010_QualityStack", "PR010_QualityHoldStack", (-6200, 3500, 820), ["quality_hold_stack"], "BlankSteel", (2200, 1700, 400))
for x in (-6700, -3700, -700, 2300, 5300, 6700):
    place("SM_CA_MW_PR010_EStop", f"PR010_EStop_{x:+05d}", (x, -4350, 1100), ["emergency_stop", "service_side"], "StatusAmber", (180, 120, 260))

# Export one origin-centred deterministic FBX per reusable semantic asset.
export_rows = []
for asset, template in sorted(asset_templates.items()):
    previous_location = template.location.copy()
    previous_name = template.name
    template.location = (0, 0, 0)
    template.name = asset
    bpy.ops.object.select_all(action="DESELECT")
    template.select_set(True)
    bpy.context.view_layer.objects.active = template
    path = EXPORTS / f"{asset}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS", bake_space_transform=False,
        add_leaf_bones=False, path_mode="AUTO", use_mesh_modifiers=True,
    )
    template.location = previous_location
    template.name = previous_name
    export_rows.append({"asset": asset, "file": str(path.relative_to(OUT)), "bytes": path.stat().st_size})

blend_path = OUT / "CA_MW_PR010_FourLaneBuffer_Blockout_v001.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
manifest = {
    "$schema": "cairnwell/source/pr010-dimensioned-blockout-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "station": "PR010",
    "world_datum_cm": [1350, -2000, 0],
    "world_yaw_deg": -90,
    "local_axes": {"x": "across four lanes", "y": "material flow", "z": "up"},
    "fixed_lane_centres_x_mm": lane_centres,
    "lane_pitch_mm": 3000,
    "estimated_equipment_envelope_mm": [14000, 8400, 3600],
    "external_handoff_apron": {"centre_mm": [0, 4700, 0], "size_mm": [13500, 2400]},
    "press_train_datums": "TBC_NOT_INVENTED",
    "source_blend": blend_path.name,
    "assets": export_rows,
    "asset_specs": asset_specs,
    "placements": placements,
    "promotion_authorized": False,
}
(OUT / "PR010_BLOCKOUT_MANIFEST_v001.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({"status": "PASS__PR010_DIMENSIONED_BLOCKOUT_SOURCE_BUILT__UNREAL_GATES_REQUIRED__NOT_PROMOTED", "assets": len(export_rows), "placements": len(placements), "blend": str(blend_path)}, indent=2))
