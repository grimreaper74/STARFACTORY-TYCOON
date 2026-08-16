"""Build a clean, grounded, hand-painted S01 master from the selected 52-part Meshy split."""
import bpy
from pathlib import Path
from mathutils import Vector

OUT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\S01_Destack\HandPaintedSplit_v936\Cairnwell_S01_Destack_HandPaintedSplit_v936.blend")
OUT.parent.mkdir(parents=True, exist_ok=True)

def material(name, color, metallic=0.0, roughness=0.45):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

GREEN = material("CA_S01_EmeraldGreen", (0.018, 0.205, 0.105), 0.72, 0.27)
DARK_GREEN = material("CA_S01_DarkGreen", (0.009, 0.070, 0.039), 0.68, 0.31)
GRAPHITE = material("CA_S01_Graphite", (0.025, 0.032, 0.036), 0.78, 0.29)
YELLOW = material("CA_S01_SafetyYellow", (0.92, 0.53, 0.015), 0.52, 0.30)
STEEL = material("CA_S01_BrushedSteel", (0.34, 0.38, 0.40), 0.90, 0.24)
CABINET = material("CA_S01_CabinetGrey", (0.55, 0.58, 0.57), 0.62, 0.32)
BLACK = material("CA_S01_RubberBlack", (0.008, 0.010, 0.011), 0.15, 0.48)

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if len(meshes) != 52:
    raise RuntimeError(f"Expected selected 52-part split, found {len(meshes)}")

# Determine generated source envelope before rescaling.
points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
hi = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
size = hi - lo
target = Vector((7.0, 3.2, 3.5))
scale = Vector((target.x/size.x, target.y/size.y, target.z/size.z))

for o in meshes:
    # Store source-space classification values before transforms.
    c = o.matrix_world @ Vector((0, 0, 0))
    d = o.dimensions.copy()
    poly = len(o.data.polygons)

    # Controlled palette. Large residual shells form the emerald structural body.
    chosen = GREEN
    role = "StaticStructure"
    if c.z < -0.10:
        chosen, role = GRAPHITE, "BaseOrTable"
    if abs(c.x) > 0.72 and c.z < 0.04 and d.z > 0.18:
        chosen, role = CABINET, "ElectricalCabinet"
    if c.z > 0.145 and d.x < 0.35:
        chosen, role = YELLOW, "MovingSuctionOrSensor"
    elif c.z > 0.13 and d.x >= 0.35:
        chosen, role = DARK_GREEN, "OverheadGantry"
    if d.z < 0.025 or (d.y < 0.035 and d.x < 0.30):
        chosen = STEEL
    if poly < 4000 and c.z < -0.05:
        chosen = BLACK

    o.data.materials.clear()
    o.data.materials.append(chosen)
    o.name = f"S01_{role}_{o.name.replace('model_part','P')}"
    o.scale = Vector((o.scale.x*scale.x, o.scale.y*scale.y, o.scale.z*scale.z))

# Apply transforms, then center X/Y and set the lowest point to Z=0.
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
hi = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
offset = Vector((-(lo.x+hi.x)*0.5, -(lo.y+hi.y)*0.5, -lo.z))
for o in meshes:
    o.location += offset

# Add explicit, non-rendering assembly metadata for Unreal/player-build placement.
root = bpy.data.objects.new("S01_DESTACK_PLAYER_UNIT_ROOT_7M", None)
bpy.context.scene.collection.objects.link(root)
root["LineBossAsset"] = "S01_Destack_BlankFeed"
root["PlayerPlaceable"] = True
root["MaterialFlowAxis"] = "+X"
root["EnvelopeMetres"] = "7.0 x 3.2 x 3.5"
root["TexturePolicy"] = "Controlled Blender PBR; Meshy texture rejected"
for o in meshes:
    o.parent = root

bpy.context.scene["LineBossValidation"] = "Selected newer 52-part split; grounded and hand-painted"
bpy.context.scene["MaterialFlowAxis"] = "+X"
bpy.context.scene["NominalStationPitchMetres"] = 7.5
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
print("LINE_BOSS_S01_HAND_PAINTED_SPLIT_V936", OUT, len(meshes), target[:])
