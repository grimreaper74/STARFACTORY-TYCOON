"""Import the authored marriage station and stand it at assembly position 12.

Position 12 is the one the builder already labels "Powertrain marriage"
(OF_ASSEMBLY_POS_12), at X 4000 + 11*2200 = 28200, Y 5500, from CanonicalLocation in
LBOneFactoryAssemblyStarterLayout.cpp.

import_materials is False by project policy - meshes arrive carrying named semantic
slots (MAT_CairnwellGreen and friends) with nothing bound, and
LB.OneFactory.Materials binds the brand palette to them at runtime.
"""
import io
import json
import os

import unreal

FBX = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/SourceAssets/Candidate/"
       r"AssemblyShop/PowertrainMarriage_v001/SM_LB_Assembly_PowertrainMarriage_v001.fbx")
DEST = "/Game/LineBoss/Candidates/AssemblyShop/PowertrainMarriage_v001"
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Assembly.Marriage"
AT = unreal.Vector(28200.0, 5500.0, 0.0)
OUT = os.environ.get("LB_MARRIAGE_OUT", "C:/Temp/lb_marriage.json")
REPORT = {}

options = unreal.FbxImportUI()
options.set_editor_property("import_mesh", True)
options.set_editor_property("import_materials", False)
options.set_editor_property("import_textures", False)
options.set_editor_property("import_as_skeletal", False)
options.static_mesh_import_data.set_editor_property(
    "combine_meshes", True)
options.static_mesh_import_data.set_editor_property(
    "import_uniform_scale", 1.0)

task = unreal.AssetImportTask()
task.set_editor_property("filename", FBX)
task.set_editor_property("destination_path", DEST)
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", True)
task.set_editor_property("options", options)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

imported = list(task.get_editor_property("imported_object_paths") or [])
REPORT["imported"] = imported
if not imported:
    raise RuntimeError("import produced nothing")

mesh_path = imported[0].split(".")[0]
mesh = unreal.load_asset(mesh_path)
if mesh is None:
    raise RuntimeError("could not load {}".format(mesh_path))
box = mesh.get_bounding_box()
size = box.max - box.min
REPORT["size_cm"] = [round(size.x, 1), round(size.y, 1), round(size.z, 1)]
REPORT["slots"] = [str(s.material_slot_name) for s in mesh.static_materials]

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")
w = unreal.EditorLevelLibrary.get_editor_world()
if w is None or TARGET.rsplit("/", 1)[-1] != w.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")

cleared = 0
for a in ACTOR_SUB.get_all_level_actors():
    if a and unreal.Name(TAG) in a.tags:
        ACTOR_SUB.destroy_actor(a)
        cleared += 1
REPORT["cleared"] = cleared

actor = ACTOR_SUB.spawn_actor_from_object(mesh, AT, unreal.Rotator(0.0, 0.0, 0.0))
if actor is None:
    raise RuntimeError("spawn failed")
actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
              unreal.Name("LB.NotProcessWIP")]
actor.set_actor_label("Assembly_PowertrainMarriage_Pos12")
LEVEL_SUB.save_current_level()

with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1))
unreal.log("LINE_BOSS_MARRIAGE {}".format(json.dumps(REPORT)))
