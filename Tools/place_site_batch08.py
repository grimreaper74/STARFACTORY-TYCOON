"""Site batch 08: solar canopies over the dispatch lanes and centreline
markings along the ring and spine roads. Idempotent via LB.Site08.
Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate")
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Site08"
OUT = "C:/Temp/lb_site08.json"

report = {"imported": {}, "placed": {}, "cleared": 0, "marking_material": None}
lib = unreal.EditorAssetLibrary

options = unreal.FbxImportUI()
options.set_editor_property("import_mesh", True)
options.set_editor_property("import_materials", False)
options.set_editor_property("import_textures", False)
options.set_editor_property("import_as_skeletal", False)
options.static_mesh_import_data.set_editor_property("combine_meshes", True)
task = unreal.AssetImportTask()
task.set_editor_property("filename", os.path.join(
    SRC, "Site/SolarCanopy_v001", "SM_LB_Site_SolarCanopy_v001.fbx"))
task.set_editor_property("destination_path",
                         "/Game/LineBoss/Candidates/Site/SolarCanopy_v001")
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", True)
task.set_editor_property("options", options)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
paths = list(task.get_editor_property("imported_object_paths") or [])
if not paths:
    raise RuntimeError("canopy import produced nothing")
CANOPY = unreal.load_asset(paths[0].split(".")[0])
size = CANOPY.get_bounding_box().max - CANOPY.get_bounding_box().min
report["imported"]["SM_LB_Site_SolarCanopy_v001"] = [
    round(size.x, 1), round(size.y, 1), round(size.z, 1)]

# A light plate material for the markings; cubes import default-grey and
# the semantic pass has no fragment for road paint.
marking_material = None
for asset in lib.list_assets("/Game/LineBoss", recursive=True):
    name = asset.rsplit("/", 1)[-1].split(".")[0]
    if "labelplate" in name.lower() or "lightgrey" in name.lower():
        loaded = unreal.load_asset(asset.split(".")[0])
        if isinstance(loaded, unreal.MaterialInterface):
            marking_material = loaded
            report["marking_material"] = name
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

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
count = 0


def tag_actor(actor, label):
    global count
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label(label)
    count += 1


# Ten canopies along the dispatch compound.
for n in range(10):
    actor = ACTOR_SUB.spawn_actor_from_object(
        CANOPY, unreal.Vector(7500.0 + n * 2000.0, 16600.0, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0))
    if actor:
        tag_actor(actor, "Site_SolarCanopy_{:d}".format(n))
        report["placed"]["canopy"] = report["placed"].get("canopy", 0) + 1


def dash_line(label, cx, cy, length, along_x, pitch=600.0):
    global count
    dashes = int(length / pitch)
    for n in range(dashes):
        offset = -length / 2.0 + pitch * (n + 0.5)
        x = cx + (offset if along_x else 0.0)
        y = cy + (0.0 if along_x else offset)
        actor = ACTOR_SUB.spawn_actor_from_object(
            CUBE, unreal.Vector(x, y, 6.0), unreal.Rotator(0.0, 0.0, 0.0))
        if actor is None:
            continue
        actor.set_actor_scale3d(unreal.Vector(
            3.0 if along_x else 0.15, 0.15 if along_x else 3.0, 0.02))
        component = actor.get_component_by_class(
            unreal.StaticMeshComponent.static_class())
        if component and marking_material:
            component.set_material(0, marking_material)
        tag_actor(actor, "Site_RoadMark_{}_{:d}".format(label, n))
        report["placed"]["marks"] = report["placed"].get("marks", 0) + 1


dash_line("N", 0.0, 17250.0, 70000.0, True)
dash_line("S", 0.0, -16750.0, 70000.0, True)
dash_line("W", -34250.0, 500.0, 34400.0, False)
dash_line("E", 34250.0, 500.0, 34400.0, False)
dash_line("Spine", 0.0, -500.0, 63000.0, True)

LEVEL_SUB.save_current_level()
report["total"] = count
with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_SITE08 {}".format(json.dumps(
    {k: report[k] for k in ("placed", "marking_material")})))
