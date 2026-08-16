"""Refine v936 S01 materials by broad functional zones on compound split pieces."""
import bpy
from pathlib import Path
from mathutils import Vector

OUT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\S01_Destack\HandPaintedSplit_v937\Cairnwell_S01_Destack_HandPaintedSplit_v937.blend")
OUT.parent.mkdir(parents=True, exist_ok=True)

def ensure(name, color, metallic, roughness):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

mats = {m.name: m for m in bpy.data.materials if m.name.startswith("CA_S01_")}
green = mats["CA_S01_EmeraldGreen"]
dark_green = ensure("CA_S01_DarkGreen", (0.009, 0.070, 0.039), .68, .46)
graphite = ensure("CA_S01_Graphite", (0.025, 0.032, 0.036), .78, .42)
yellow = ensure("CA_S01_SafetyYellow", (0.92, 0.53, 0.015), .52, .40)
steel = ensure("CA_S01_BrushedSteel", (0.34, 0.38, 0.40), .90, .31)
cabinet = ensure("CA_S01_CabinetGrey", (0.55, 0.58, 0.57), .62, .48)
black = ensure("CA_S01_RubberBlack", (0.008, 0.010, 0.011), .15, .58)

# Reduce the wet/glossy appearance from the first proof.
for m, rough in [(green, .43), (dark_green, .46), (graphite, .42), (yellow, .40), (steel, .31), (cabinet, .48), (black, .58)]:
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = rough

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
palette = [green, dark_green, graphite, yellow, steel, cabinet, black]

for obj in meshes:
    obj.data.materials.clear()
    for mat in palette:
        obj.data.materials.append(mat)
    inv_transpose = obj.matrix_world.to_3x3().inverted().transposed()
    for poly in obj.data.polygons:
        p = obj.matrix_world @ poly.center
        n = (inv_transpose @ poly.normal).normalized()
        idx = 0  # emerald structure
        # Ground frames, motors and lower mechanisms.
        if p.z < 0.72:
            idx = 2
        # End electrical/control cabinets.
        if abs(p.x) > 2.72 and p.z < 2.45:
            idx = 5
        # Brushed contact surfaces on the two blank stacks/feed decks.
        if 0.72 <= p.z <= 1.38 and abs(p.x) < 2.55 and n.z > 0.42:
            idx = 4
        # Central moving suction carriage below the fixed top gantry.
        if abs(p.x) < 1.50 and 1.55 < p.z < 2.55:
            idx = 3
        # Upper fixed rails remain a darker structural green.
        if p.z >= 2.58:
            idx = 1
        # Rubber pads/cups beneath the yellow carriage.
        if abs(p.x) < 1.65 and 1.38 < p.z < 1.72 and n.z < -0.20:
            idx = 6
        poly.material_index = idx

bpy.context.scene["LineBossValidation"] = "v937 broad functional material zones; no Meshy texture"
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
print("LINE_BOSS_S01_MATERIAL_ZONES_V937", OUT, len(meshes))
