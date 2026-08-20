"""Dump footprints for every authored kit mesh plus the native robot pose.

The process-line layouts need real sizes, not guesses: every
SM_LB_(Weld|Paint|Assembly|BodyShop*)_* static mesh's bounding box, and
the relative transforms of one existing native robot's seven joints so
placement scripts can spawn correctly-posed robots.
"""
import json
import re
from collections import defaultdict

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_kit_bounds.json"

registry = unreal.AssetRegistryHelpers.get_asset_registry()
filt = unreal.ARFilter(
    class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")],
    package_paths=["/Game/LineBoss"], recursive_paths=True)
bounds = {}
packages = {}
for data in registry.get_assets(filt):
    name = str(data.asset_name)
    if not re.match(r"SM_LB_(Weld|Paint|Assembly|BodyShop)", name):
        continue
    mesh = unreal.load_asset(str(data.package_name))
    if mesh is None:
        continue
    box = mesh.get_bounding_box()
    bounds[name] = {
        "size": [round(box.max.x - box.min.x, 1),
                 round(box.max.y - box.min.y, 1),
                 round(box.max.z - box.min.z, 1)],
        "package": str(data.package_name),
    }

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

# One paint robot's joints, grouped by shared numeric suffix in the label.
joints = defaultdict(dict)
for actor in ACTOR_SUB.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith("Paint_"):
        continue
    for component in actor.get_components_by_class(
            unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is None or "BodyShopRobotNative" not in mesh.get_name():
            continue
        part = mesh.get_name().replace(
            "SM_LB_BodyShopRobotNative_", "").replace("_v001", "")
        group = re.sub(r".*?(\d+)$", r"\1", label)
        where = actor.get_actor_location()
        rot = actor.get_actor_rotation()
        joints[group][part] = {
            "loc": [round(where.x, 1), round(where.y, 1),
                    round(where.z, 1)],
            "rot": [round(rot.pitch, 1), round(rot.yaw, 1),
                    round(rot.roll, 1)],
        }

pose = {}
for group, parts in joints.items():
    if len(parts) == 7 and "Base" in parts:
        base = parts["Base"]["loc"]
        pose = {part: {
            "offset": [round(info["loc"][0] - base[0], 1),
                       round(info["loc"][1] - base[1], 1),
                       round(info["loc"][2] - base[2], 1)],
            "rot": info["rot"],
        } for part, info in parts.items()}
        break

with open(OUT, "w") as handle:
    json.dump({"bounds": bounds, "robot_pose": pose}, handle, indent=1)
unreal.log("LINE_BOSS_KIT_BOUNDS meshes={} pose_parts={}".format(
    len(bounds), len(pose)))
