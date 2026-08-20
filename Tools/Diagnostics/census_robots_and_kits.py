"""Find every robot actor regardless of label, and inventory the authored
shop kits available in /Game/LineBoss.

Assembly shows robots that are 'not our own' (owner): the canonical unit
is SM_LB_BodyShopRobotNative_* (weld and paint use it). Locate every
actor whose mesh says robot, listing label, mesh and position. Also list
the authored static meshes available per kit family so the process-line
rebuilds place from what exists.
"""
import json
import re
from collections import defaultdict

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_robots_kits.json"

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

robots = []
for actor in ACTOR_SUB.get_all_level_actors():
    for component in actor.get_components_by_class(
            unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is None:
            continue
        name = mesh.get_name()
        if re.search(r"robot", name, re.IGNORECASE) \
                and "BodyShopRobotNative" not in name:
            where = actor.get_actor_location()
            robots.append({
                "label": actor.get_actor_label(),
                "mesh": name,
                "x": round(where.x), "y": round(where.y),
            })

registry = unreal.AssetRegistryHelpers.get_asset_registry()
filt = unreal.ARFilter(
    class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")],
    package_paths=["/Game/LineBoss"], recursive_paths=True)
kits = defaultdict(list)
for data in registry.get_assets(filt):
    name = str(data.asset_name)
    match = re.match(r"SM_LB_(Weld|Paint|Assembly|BodyShop\w*?|Site)_?", name)
    if match:
        kits[match.group(1)].append(name)
for family in kits:
    kits[family] = sorted(set(kits[family]))

with open(OUT, "w", encoding="utf-8") as handle:
    json.dump({"foreign_robots": robots, "kits": kits}, handle, indent=1)
unreal.log("LINE_BOSS_ROBOTKIT foreign={} families={}".format(
    len(robots), list(kits)))
