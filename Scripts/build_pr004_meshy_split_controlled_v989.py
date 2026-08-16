import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
if len(args) != 4:
    raise RuntimeError("usage: -- <mode:a|b|c|d|e> <source.blend> <output.blend> <audit.json>")
mode, source, output_blend, output_audit = args
if mode not in {"a", "b", "c", "d", "e"}:
    raise RuntimeError("mode must be a, b, c, d or e")

bpy.ops.wm.open_mainfile(filepath=source)
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
removed = []
if mode in {"a", "b", "c", "e"}:
    stray = bpy.data.objects.get("model_part0")
    if stray:
        removed.append(stray.name)
        bpy.data.objects.remove(stray, do_unlink=True)
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]

targets = {
    "a": Vector((1.902081, 1.052291, 0.716011)),
    "b": Vector((1.711946, 1.651218, 1.904054)),
    "c": Vector((1.534235, 1.901226, 1.437694)),
    "d": Vector((1.899533, 1.204557, 0.759190)),
    # Meshy interpreted the wrist tool as a 1.9 m assembly. Keep its source
    # proportions but produce a credible 0.75 m robot-wrist derivative.
    "e": Vector((0.750000, 0.487515, 0.641043)),
}

def bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    return low, high

low, high = bounds(meshes)
scale = Vector(tuple(targets[mode][i] / (high[i] - low[i]) for i in range(3)))
for obj in meshes:
    obj.location = Vector(tuple(obj.location[i] * scale[i] for i in range(3)))
    obj.scale = Vector(tuple(obj.scale[i] * scale[i] for i in range(3)))

bpy.context.view_layer.update()
low, high = bounds(meshes)
offset = Vector((-(low.x + high.x) * 0.5, -(low.y + high.y) * 0.5, -low.z))
for obj in meshes:
    obj.location += offset
bpy.context.view_layer.update()

def material(name, base, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*base, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

mats = {
    "green": material("CAIRNWELL_EmeraldGreen", (0.018, 0.16, 0.085), 0.55, 0.38),
    "graphite": material("CAIRNWELL_Graphite", (0.025, 0.032, 0.038), 0.68, 0.46),
    "rubber": material("CAIRNWELL_RollerRubber", (0.008, 0.010, 0.012), 0.0, 0.78),
    "yellow": material("CAIRNWELL_SafetyYellow", (0.82, 0.46, 0.025), 0.42, 0.40),
    "steel": material("CAIRNWELL_MachinedSteel", (0.23, 0.27, 0.30), 0.82, 0.30),
    "blue": material("CAIRNWELL_VisionBlue", (0.015, 0.18, 0.42), 0.32, 0.34),
}

if mode == "a":
    assignment = {
        "green": {"model_part2", "model_part3", "model_part10", "model_part11", "model_part20"},
        "rubber": {"model_part6", "model_part7"},
        "yellow": {"model_part1", "model_part4", "model_part5", "model_part8", "model_part9", "model_part12", "model_part13"},
        "steel": {"model_part14", "model_part15"},
    }
elif mode == "b":
    assignment = {
        "green": {"model_part21", "model_part22", "model_part23"},
        "rubber": {"model_part1", "model_part8"},
        "yellow": {"model_part3", "model_part9", "model_part10", "model_part11", "model_part12", "model_part13", "model_part14", "model_part15"},
        "steel": {"model_part2", "model_part4", "model_part5", "model_part6"},
    }
elif mode == "c":
    assignment = {
        "green": {"model_part2", "model_part10", "model_part18"},
        "steel": {"model_part15"},
        "yellow": {"model_part3", "model_part4", "model_part5", "model_part6", "model_part11", "model_part12", "model_part13", "model_part14"},
    }
elif mode == "d":
    assignment = {
        "green": {"model_part9"},
        "rubber": {"model_part8"},
        "yellow": {"model_part0", "model_part1", "model_part2", "model_part3"},
    }
else:
    assignment = {
        "green": {"model_part7"},
        "steel": {"model_part2"},
        "blue": {"model_part3"},
        "yellow": {"model_part1", "model_part5"},
    }

for obj in meshes:
    key = "graphite"
    for candidate, names in assignment.items():
        if obj.name in names:
            key = candidate
            break
    obj.data.materials.clear()
    obj.data.materials.append(mats[key])

low, high = bounds(meshes)
moving = {
    "a": ["model_part6", "model_part7"],
    "b": ["model_part1", "model_part8", "model_part24"],
    "c": ["model_part1", "model_part9", "model_part15"],
    "d": ["model_part4", "model_part5", "model_part6", "model_part7", "model_part8"],
    "e": ["model_part1", "model_part4", "model_part5", "model_part6", "model_part8"],
}[mode]
for name in moving:
    obj = bpy.data.objects.get(name)
    if obj:
        obj["line_boss_motion_candidate"] = True

output = Path(output_blend)
output.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(output))

payload = {
    "status": "BLENDER_CONTROLLED_MATERIAL_CANDIDATE__VISUAL_REVIEW_REQUIRED__NOT_UNREAL_PROMOTED",
    "mode": mode,
    "source": source,
    "output": str(output),
    "removed_strays": removed,
    "mesh_count": len(meshes),
    "target_envelope_m": [round(value, 6) for value in targets[mode]],
    "result_envelope_m": [round(value, 6) for value in (high - low)],
    "axis_scale_applied": [round(value, 9) for value in scale],
    "moving_part_candidates": moving,
    "materials": list(mats),
    "meshy_credits_used": 0,
}
audit = Path(output_audit)
audit.parent.mkdir(parents=True, exist_ok=True)
audit.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_PR004_MESHY_SPLIT_CONTROLLED_V989", mode, len(meshes))
