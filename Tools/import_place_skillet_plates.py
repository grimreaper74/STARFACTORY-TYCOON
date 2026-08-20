"""Import the reworked skillet deck plate and fill the assembly chains.

SM_LB_Conveyor_SkilletDeckPlate_v001 was commissioned under a name that
never made it into the game; Codex's detail-uplift rework is its first
import. Plates land between the skillet carriers (320 cm pitch) on all
four assembly lines, so the chains read as continuous decking.
Idempotent via LB.SkilletPlate. Run with -ExecutePythonScript.
"""
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate/DetailUplift_v001"
       r"/SM_LB_Conveyor_SkilletDeckPlate_v001"
       r"/SM_LB_Conveyor_SkilletDeckPlate_v001.fbx")
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
MESH_DIR = "/Game/LineBoss/Candidates/AssemblyShop/SkilletDeckPlate_v001"
TAG = "LB.SkilletPlate"
OUT = "C:/Temp/lb_skillet_plates.json"

tools = unreal.AssetToolsHelpers.get_asset_tools()
options = unreal.FbxImportUI()
options.set_editor_property("import_mesh", True)
options.set_editor_property("import_materials", False)
options.set_editor_property("import_textures", False)
options.set_editor_property("import_as_skeletal", False)
options.static_mesh_import_data.set_editor_property("combine_meshes", True)
task = unreal.AssetImportTask()
task.set_editor_property("filename", SRC)
task.set_editor_property("destination_path", MESH_DIR)
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", True)
task.set_editor_property("options", options)
tools.import_asset_tasks([task])
paths = list(task.get_editor_property("imported_object_paths") or [])
if not paths:
    raise RuntimeError("skillet deck plate import produced nothing")
mesh = unreal.load_asset(paths[0].split(".")[0])

# Steel deck finish from the SignalKit role instances.
steel = unreal.load_asset(
    "/Game/LineBoss/SignalKit_v001/Materials/MI_LB_SK_Steel_v001")
graphite = unreal.load_asset(
    "/Game/LineBoss/SignalKit_v001/Materials/MI_LB_SK_Graphite_v001")
materials = list(mesh.get_editor_property("static_materials"))
for entry in materials:
    slot = str(entry.get_editor_property("material_slot_name")).lower()
    entry.set_editor_property(
        "material_interface",
        graphite if "graphite" in slot or "frame" in slot else steel)
mesh.set_editor_property("static_materials", materials)
unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or TARGET.rsplit("/", 1)[-1] != world.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")

REPORT = {"cleared": 0, "placed": 0}
for actor in list(ACTOR_SUB.get_all_level_actors()):
    if TAG in [str(t) for t in actor.tags]:
        ACTOR_SUB.destroy_actor(actor)
        REPORT["cleared"] += 1

X_WEST, X_EAST = 4400.0, 21600.0
for line_y in (3609.0, 7391.0, 9609.0, 13391.0):
    x = X_WEST + 160.0
    while x <= X_EAST:
        actor = ACTOR_SUB.spawn_actor_from_object(
            mesh, unreal.Vector(x, line_y, 0.0),
            unreal.Rotator(0.0, 0.0, 0.0))
        if actor is not None:
            REPORT["placed"] += 1
            actor.set_actor_label(
                "SkilletPlate_{:04d}".format(REPORT["placed"]))
            for tag in (TAG, "LB.Environment.VisualOnly",
                        "LB.NotProcessWIP"):
                actor.tags.append(tag)
        x += 320.0

if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")

with open(OUT, "w") as handle:
    json.dump(REPORT, handle, indent=1)
unreal.log("LINE_BOSS_SKILLET_PLATES placed={} cleared={}".format(
    REPORT["placed"], REPORT["cleared"]))
