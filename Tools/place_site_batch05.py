"""Site batch 05: the ground plane - a single sealed-concrete ground slab
under the whole site and skyline so the works stops floating in void.
Idempotent via LB.Site05. Run with -ExecutePythonScript.
"""
import io
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_site05.json"
TAG = "LB.Site05"

lib = unreal.EditorAssetLibrary
report = {"ground_material": None, "placed": 0, "cleared": 0}

plane = unreal.load_asset("/Engine/BasicShapes/Plane")
if not isinstance(plane, unreal.StaticMesh):
    raise RuntimeError("engine plane unavailable")

# A dark sealed-concrete ground reads as the industrial estate the plan
# calls for; searched rather than hardcoded so a rename cannot break it.
ground_material = None
for asset in lib.list_assets("/Game/LineBoss", recursive=True):
    name = asset.rsplit("/", 1)[-1].split(".")[0]
    if "sealedconcrete" in name.lower():
        loaded = unreal.load_asset(asset.split(".")[0])
        if isinstance(loaded, unreal.MaterialInterface):
            ground_material = loaded
            report["ground_material"] = name
            break

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")
w = unreal.EditorLevelLibrary.get_editor_world()
if w is None or TARGET.rsplit("/", 1)[-1] != w.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")
for a in ACTOR_SUB.get_all_level_actors():
    if a and unreal.Name(TAG) in a.tags:
        ACTOR_SUB.destroy_actor(a)
        report["cleared"] += 1

actor = ACTOR_SUB.spawn_actor_from_object(
    plane, unreal.Vector(0.0, 2000.0, -4.0), unreal.Rotator(0.0, 0.0, 0.0))
if actor is None:
    raise RuntimeError("ground plane spawn failed")
# Engine plane is 100 cm; the estate ground is 1300 x 900 m.
actor.set_actor_scale3d(unreal.Vector(1300.0, 900.0, 1.0))
component = actor.static_mesh_component
if ground_material:
    component.set_material(0, ground_material)
actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
              unreal.Name("LB.NotProcessWIP")]
actor.set_actor_label("Site_GroundPlane")
report["placed"] = 1

LEVEL_SUB.save_current_level()
with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_SITE05 {}".format(json.dumps(report)))
