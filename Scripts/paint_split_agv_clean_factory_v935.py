"""Create clean two-piece AGV from matching Meshy segmentation with object-boundary paint."""
import bpy
from pathlib import Path

OUT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressShop\CoilAGV\HandPaintedSplit_v935\Cairnwell_Coil_AGV_HandPaintedSplit_v935.blend")
OUT.parent.mkdir(parents=True, exist_ok=True)
SCALE = 1.901947021484375 / 2.0

def mat(name, color, metallic, roughness):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return m

green = mat("CA_AGV_CairnwellGreen_v935", (0.012, 0.105, 0.050), 0.45, 0.32)
yellow = mat("CA_AGV_SafetyYellow_v935", (0.90, 0.39, 0.008), 0.28, 0.36)
black = mat("CA_AGV_RubberBlack_v935", (0.006, 0.008, 0.009), 0.02, 0.76)
steel = mat("CA_AGV_BrushedSteel_v935", (0.28, 0.32, 0.34), 0.76, 0.30)

parts = {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}
expected = {f"model_part{i}" for i in range(12)}
if set(parts) != expected:
    raise RuntimeError(f"Unexpected segmentation: {sorted(parts)}")
for obj in parts.values():
    obj.scale = (SCALE,) * 3
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.object.select_all(action="DESELECT")

def assign(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)

assign(parts["model_part0"], steel)  # central wear insert
assign(parts["model_part1"], steel)  # independently lifting V-cradle/deck
for i in range(2, 10):
    assign(parts[f"model_part{i}"], yellow)  # physical corner protection groups
assign(parts["model_part10"], black)        # continuous lower bumper/base
assign(parts["model_part11"], green)        # main chassis/body

deck = parts["model_part1"]
deck.name = "SM_CA_MW_CoilAGV_LiftDeck_HandPainted_v935"
chassis_parts = [parts["model_part0"], *[parts[f"model_part{i}"] for i in range(2, 12)]]
for obj in chassis_parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = parts["model_part11"]
bpy.ops.object.join()
chassis = bpy.context.object
chassis.name = "SM_CA_MW_CoilAGV_Chassis_HandPainted_v935"

for obj in (chassis, deck):
    obj["line_boss_asset"] = "COIL_AGV_HAND_PAINTED_SPLIT_V935"
    obj["player_buildable"] = True
    obj["nanite_recommended"] = False
bpy.context.scene["source_geometry"] = "Meshy_AI_Cairnwell_Coil_AGV_0810073415_generate.blend"
bpy.context.scene["split_authority"] = "Meshy_AI__0809174551_part-segmentation.blend"
bpy.context.scene["meshy_credits_used_by_codex"] = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
print("LINE_BOSS_HAND_PAINTED_SPLIT_AGV_V935", OUT)
