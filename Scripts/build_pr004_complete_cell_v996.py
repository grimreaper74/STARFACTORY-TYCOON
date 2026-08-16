"""Assemble the approved A-E PR004 cell and prove the two coil orientations."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
AB = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/Assembly_v20260810/Cairnwell_PR004_CradleWinderFit_v990.blend"
C = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/PlasticFilmCompactor_v20260810/Cleaned/Cairnwell_PlasticFilmCompactor_Controlled_v994.blend"
D_FIT = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/BareCoilOutputSaddle_v20260810/Fit/Cairnwell_BareCoilSaddleFit_v995.blend"
ROBOT = ROOT / "SourceAssets/Candidate/PressTrains/Shared/MeshyUnloadRobot_v20260809_v001/Cleaned_v001/Cairnwell_S07_UnloadRobot_Cleaned_v001.blend"
E = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/RobotWristDepackTool_v20260810/Cleaned/Cairnwell_RobotWristDepackTool_Controlled_v994.blend"
OUT = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/Assembly_v20260810/Cairnwell_PR004_CompleteCell_v996.blend"
AUDIT = ROOT / "Saved/Audits/PressShopIntegration/pr004_complete_cell_v996.json"

bpy.ops.wm.read_factory_settings(use_empty=True)


def append_meshes(path, prefix, keep=lambda name: True):
    with bpy.data.libraries.load(str(path), link=False) as (source, target):
        target.objects = list(source.objects)
    linked = []
    for obj in target.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
            linked.append(obj)
    bpy.context.view_layer.update()
    meshes = []
    for obj in linked:
        if obj.type != "MESH" or not keep(obj.name):
            continue
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
        obj.name = prefix + obj.name
        meshes.append(obj)
    for obj in linked:
        if obj not in meshes:
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.context.view_layer.update()
    return meshes


def transform(objects, matrix):
    bpy.context.view_layer.update()
    for obj in objects:
        obj.matrix_world = matrix @ obj.matrix_world
    bpy.context.view_layer.update()


def bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    return low, high


ab = append_meshes(AB, "AB_")
c = append_meshes(C, "C_COMPACTOR_")
d = append_meshes(D_FIT, "D_OUTPUT_")
robot = append_meshes(ROBOT, "ROBOT_", lambda name: name != "REVIEW_FLOOR_NOT_EXPORT" and not name.startswith("S07_TOOL_"))
tool = append_meshes(E, "E_TOOL_")

# Compact U-shaped player-buildable cell around the powered cradle.
transform(c, Matrix.Translation((2.15, 2.55, 0.0)))
transform(d, Matrix.Translation((-2.35, 0.0, 0.0)))

# Reuse the approved six-axis robot body but replace its unload cup array with
# the new E depack tool. Source arm points -X; +90 Z points it toward -Y and
# the cradle from the rear service side.
robot_transform = Matrix.Translation((0.0, 2.15, 0.805135)) @ Matrix.Rotation(math.radians(90.0), 4, "Z")
transform(robot, robot_transform)

# Existing wrist/tool datum was source (-0.69, 0, 0.235). After the robot
# transform it is world (0, 1.46, 1.040135). E is floor-seated with the ISO
# flange at Z=0.641043, so lift its flange to that datum.
tool_flange = Vector((0.0, 1.46, 1.040135))
transform(tool, Matrix.Translation((tool_flange.x, tool_flange.y, tool_flange.z - 0.641043)))

OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))

groups = {"ab_cradle_winder": ab, "c_compactor": c, "d_saddle_and_bare_coil": d, "robot_body": robot, "e_wrist_tool": tool}
rows = {}
for name, objects in groups.items():
    low, high = bounds(objects)
    rows[name] = {
        "mesh_count": len(objects),
        "low_m": [round(value, 6) for value in low],
        "high_m": [round(value, 6) for value in high],
        "dimensions_m": [round(value, 6) for value in high - low],
    }

all_objects = [obj for objects in groups.values() for obj in objects]
low, high = bounds(all_objects)
payload = {
    "status": "PASS__COMPLETE_A_TO_E_BLENDER_ASSEMBLY__VISUAL_REVIEW_REQUIRED__NOT_UNREAL_PROMOTED",
    "output": str(OUT),
    "components": rows,
    "cell_envelope_m": [round(value, 6) for value in high - low],
    "wrapped_coil_axis": "X on powered cradle",
    "bare_coil_axis": "Y on output saddle",
    "robot_source": "approved shared Meshy six-axis body; old cup tooling excluded",
    "new_tool_scale": "controlled 0.75 m operational derivative",
    "normal_unloading_method": "autonomous coil-handler forklift; overhead crane not required",
    "meshy_credits_used": 0,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_PR004_COMPLETE_CELL_V996", len(all_objects), payload["cell_envelope_m"])
