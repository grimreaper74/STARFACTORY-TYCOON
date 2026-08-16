"""Create a clean hand-painted material test from the new untextured Meshy 7 AGV."""
import bpy
from pathlib import Path
from mathutils import Vector

OUT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressShop\CoilAGV\HandPaintedMeshy7_v934\Cairnwell_Coil_AGV_HandPainted_v934.blend")
OUT.parent.mkdir(parents=True, exist_ok=True)

def make_material(name, color, metallic, roughness):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

green = make_material("CA_AGV_CairnwellGreen", (0.018, 0.20, 0.105), 0.48, 0.28)
yellow = make_material("CA_AGV_SafetyYellow", (0.95, 0.52, 0.015), 0.34, 0.32)
black = make_material("CA_AGV_RubberBlack", (0.009, 0.012, 0.014), 0.02, 0.72)
steel = make_material("CA_AGV_BrushedSteel", (0.34, 0.38, 0.40), 0.82, 0.24)
charcoal = make_material("CA_AGV_CharcoalHardware", (0.035, 0.045, 0.048), 0.58, 0.34)
cyan = make_material("CA_AGV_SensorGlow", (0.02, 0.22, 0.18), 0.18, 0.25)
cyan.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.01, 0.50, 0.30, 1.0)
cyan.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.0

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if len(meshes) != 1:
    raise RuntimeError(f"Expected one generated AGV mesh, got {len(meshes)}")
obj = meshes[0]
obj.name = "SM_CA_MW_CoilAGV_HandPainted_v934"
obj.data.name = obj.name
obj.data.materials.clear()
for mat in (green, yellow, black, steel, charcoal, cyan):
    obj.data.materials.append(mat)

verts = [v.co for v in obj.data.vertices]
mins = Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts)))
maxs = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
center = (mins + maxs) * 0.5
half = (maxs - mins) * 0.5

for poly in obj.data.polygons:
    c = poly.center
    nx = abs((c.x - center.x) / max(half.x, 1e-6))
    ny = abs((c.y - center.y) / max(half.y, 1e-6))
    nz = (c.z - mins.z) / max(maxs.z - mins.z, 1e-6)
    top_facing = poly.normal.z > 0.38
    # Clean, readable factory palette based on physical surface zones.
    if nz < 0.13:
        poly.material_index = 2  # continuous black bumper/skirt
    elif nx > 0.72 and ny > 0.70 and nz < 0.72:
        poly.material_index = 1  # four safety corner guards
    elif nz > 0.53 and top_facing and nx < 0.72 and ny < 0.72:
        poly.material_index = 3  # V-cradle and upper wear deck
    elif nz > 0.72 and (nx > 0.58 or ny > 0.58):
        poly.material_index = 4  # sensor towers and upper hardware
    elif nz < 0.29 and (nx > 0.55 or ny > 0.55):
        poly.material_index = 4  # wheel/service hardware band
    else:
        poly.material_index = 0  # Cairnwell green body

obj["line_boss_asset"] = "COIL_AGV_HAND_PAINTED_V934"
obj["source_geometry"] = "Meshy_AI_Cairnwell_Coil_AGV_0810073415_generate.blend"
obj["player_buildable"] = True
obj["moving_deck_split_required"] = True
bpy.context.scene["meshy_credits_used_by_codex"] = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
print("LINE_BOSS_HAND_PAINTED_AGV_V934", OUT)
