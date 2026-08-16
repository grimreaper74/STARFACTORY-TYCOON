"""Build camera-readable, stage-local Train A die-cart coupling evidence.

The kit aligns with the existing ReleaseDetail_v001 cart/dock coordinate frame:
the moving cart is centred on the stage origin, its press-side edge is X=-2250
mm, and the fixed dock hardware occupies roughly X=-2800..-3300 mm.  It does
not author any Train A-D world datum.
"""

import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PressTrains/Shared/DockCouplingEvidence_v001"
FBX = OUT / "FBX"
OUT.mkdir(parents=True, exist_ok=True)
FBX.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "MILLIMETERS"
scene.unit_settings.scale_length = 1.0

PALETTE = {
    "CA_MW_FoundryCharcoal": ((0.016, 0.021, 0.023, 1), 0.35, 0.58),
    "CA_MW_CairnwellGreen": ((0.018, 0.120, 0.090, 1), 0.22, 0.54),
    "CA_MW_SafetyYellow": ((0.78, 0.43, 0.008, 1), 0.18, 0.53),
    "CA_MW_ServiceGrey": ((0.10, 0.13, 0.14, 1), 0.42, 0.60),
    "CA_MW_WorkedSteel": ((0.12, 0.15, 0.16, 1), 0.85, 0.46),
    "CA_MW_DarkRubber": ((0.008, 0.010, 0.010, 1), 0.02, 0.82),
    "CA_MW_TrainAAccent": ((0.035, 0.190, 0.420, 1), 0.20, 0.52),
    "CA_MW_StateGreen": ((0.018, 0.52, 0.18, 1), 0.05, 0.26),
    "CA_MW_LabelWhite": ((0.62, 0.69, 0.67, 1), 0.12, 0.42),
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


def box(parts, name, dims, loc, material, bevel=0, rotation_z=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=tuple(v / 1000 for v in loc))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = tuple(v / 1000 for v in dims)
    obj.rotation_euler[2] = math.radians(rotation_z)
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
        vertices=vertices,
        radius=diameter / 2000,
        depth=depth / 1000,
        location=tuple(v / 1000 for v in loc),
    )
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


def torus(parts, name, major_diameter, minor_diameter, loc, material, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_diameter / 2000,
        minor_radius=minor_diameter / 2000,
        major_segments=24,
        minor_segments=8,
        location=tuple(v / 1000 for v in loc),
        rotation=tuple(math.radians(v) for v in rotation),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(materials[material])
    parts.append(obj)
    return obj


parts = []

# Two visible hydraulic lock bridges span from the cart-side receiver blocks to
# the fixed dock clamps.  The yellow pins and polished sleeves are deliberately
# large enough to remain legible in the fixed die-change camera.
for y in (-1500, 1500):
    box(parts, f"CartReceiver_{y}", (360, 620, 540), (-2200, y, 690),
        "CA_MW_FoundryCharcoal", 42)
    box(parts, f"LockBridge_{y}", (820, 300, 250), (-2580, y, 760),
        "CA_MW_CairnwellGreen", 32)
    cylinder(parts, f"HydraulicLockPin_{y}", 190, 720, (-2760, y, 790),
             "CA_MW_SafetyYellow", axis="X", vertices=24)
    cylinder(parts, f"LockSleeve_{y}", 275, 310, (-2390, y, 790),
             "CA_MW_WorkedSteel", axis="X", vertices=24)
    box(parts, f"ClampProofFlag_{y}", (85, 390, 240), (-2910, y, 1040),
        "CA_MW_StateGreen", 12)

# Protected multi-service connector: keyed power/data/hydraulic faces, a green
# permissive witness and a visible yellow guard.  It sits below the die tooling
# rather than behind it.
box(parts, "ConnectorCartHalf", (420, 1120, 760), (-2240, 0, 1120),
    "CA_MW_ServiceGrey", 48)
box(parts, "ConnectorDockHalf", (420, 1120, 760), (-2810, 0, 1120),
    "CA_MW_FoundryCharcoal", 48)
box(parts, "ConnectorGuard", (930, 1320, 120), (-2525, 0, 1535),
    "CA_MW_SafetyYellow", 24)
for y, material in ((-330, "CA_MW_TrainAAccent"), (0, "CA_MW_StateGreen"),
                    (330, "CA_MW_WorkedSteel")):
    cylinder(parts, f"MatedConnector_{y}", 210, 690, (-2525, y, 1120),
             material, axis="X", vertices=24)
box(parts, "PermissiveWitness", (110, 520, 250), (-2880, 0, 1450),
    "CA_MW_StateGreen", 14)
box(parts, "ConnectorIdentity", (95, 760, 165), (-2900, 0, 750),
    "CA_MW_LabelWhite", 12)

# A short articulated cable chain proves the route between moving cart and
# fixed dock.  Alternating links make the engagement readable without relying
# on a flat black bar.
chain_points = [
    (-1900, -900, 150), (-2050, -900, 70), (-2220, -900, 20),
    (-2400, -900, 20), (-2580, -900, 80), (-2750, -900, 190),
]
for index, (x, y, z) in enumerate(chain_points):
    box(parts, f"CableChainLink_{index:02d}", (250, 390, 155), (x, y, z),
        "CA_MW_DarkRubber", 18, rotation_z=0 if index % 2 == 0 else 4)
    cylinder(parts, f"CableChainPin_{index:02d}", 95, 430, (x, y, z),
             "CA_MW_WorkedSteel", axis="Y", vertices=16)
box(parts, "CartCableAnchor", (320, 620, 420), (-1810, -900, 260),
    "CA_MW_CairnwellGreen", 35)
box(parts, "DockCableAnchor", (320, 620, 420), (-2840, -900, 300),
    "CA_MW_CairnwellGreen", 35)

# The release cart already owns a tow eye; this bright dock-side capture hook
# and retained pin make the relationship explicit from a three-quarter view.
torus(parts, "DockTowCapture", 520, 125, (-2800, 900, 330),
      "CA_MW_SafetyYellow", rotation=(90, 0, 0))
cylinder(parts, "TowCapturePin", 185, 620, (-2500, 900, 330),
         "CA_MW_WorkedSteel", axis="X", vertices=24)
box(parts, "TowCaptureBracket", (520, 620, 460), (-2820, 900, 330),
    "CA_MW_FoundryCharcoal", 45)

bpy.ops.object.select_all(action="DESELECT")
for part in parts:
    part.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
asset = bpy.context.object
asset.name = "SM_CA_MW_PT_DockCouplingEngaged_v001"
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
scene.cursor.location = (0, 0, 0)
bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")

fbx_path = FBX / f"{asset.name}.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL",
    axis_forward="-Y",
    axis_up="Z",
    use_mesh_modifiers=True,
    mesh_smooth_type="FACE",
    add_leaf_bones=False,
)

dimensions_mm = [round(value * 1000, 3) for value in asset.dimensions]
blend_path = OUT / "CA_MW_PressTrain_DockCouplingEvidence_v001.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

manifest = {
    "$schema": "cairnwell/source/press-train-dock-coupling-evidence-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "authority": "Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md; Pro Sheets 04/05; retained Train A v053 local cart/dock frame",
    "source_blend": blend_path.name,
    "coordinate_system": "+X operator/HMI/CCTV side, -X die-change side, +Y material flow, +Z up; millimetres",
    "world_placement": "TBC_NOT_INVENTED",
    "assets": [{
        "asset": asset.name,
        "file": str(fbx_path.relative_to(OUT)).replace("\\", "/"),
        "bytes": fbx_path.stat().st_size,
        "sha256": hashlib.sha256(fbx_path.read_bytes()).hexdigest().upper(),
        "measured_dimensions_mm": dimensions_mm,
        "planning_envelope_mm": [1800, 3700, 1800],
        "role": "engaged_die_cart_dock_coupling_presentation",
        "pivot": "stage local floor centre; place at the same transform as ReleaseDetail_v001 cart and dock",
        "collision_role": "no_collision_presentation_until_release_collision_authoring",
        "material_slots": [slot.material.name for slot in asset.material_slots],
        "features": {
            "hydraulic_lock_bridges": 2,
            "mated_service_connectors": 3,
            "articulated_cable_chain_links": len(chain_points),
            "tow_capture": 1,
            "engagement_permissive_witnesses": 3,
        },
        "notes": "Camera-readable engaged-state evidence only; runtime separation and interlock ownership remain mandatory before promotion.",
    }],
    "promotion_authorized": False,
    "press_shop_complete": False,
}
(OUT / "PRESS_TRAIN_DOCK_COUPLING_EVIDENCE_MANIFEST_v001.json").write_text(
    json.dumps(manifest, indent=2), encoding="utf-8")

print(json.dumps({
    "status": "PASS__DOCK_COUPLING_EVIDENCE_V001_BUILT__SOURCE_AUDIT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "asset": asset.name,
    "dimensions_mm": dimensions_mm,
    "fbx": str(fbx_path),
}, indent=2))
