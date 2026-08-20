"""Import journey batch 1 and swap it over the old coil-yard pieces.

Imports the three rework FBXs, binds brand materials by the kit's slot
names, then finds every placed actor whose mesh name contains CoilAGV,
BlankStackAGV or CoilScale and points its component at the new mesh -
transforms and labels untouched. Run with -ExecutePythonScript.
"""
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate/PressShop/IntakeRework_v001")
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
MESH_DIR = "/Game/LineBoss/Candidates/PressShop/IntakeRework_v001"
OUT = "C:/Temp/lb_intake_swap.json"

MODELS = {
    "SM_LB_Press_CoilAGV_v002": "CoilAGV",
    "SM_LB_Press_BlankStackAGV_v002": "BlankStackAGV",
    "SM_LB_Press_CoilScale_v002": "CoilScale",
}

MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

# Brand finishes: reuse the SignalKit role instances, add red and tire.
def role_instance(name, parent_name, colour):
    path = "/Game/LineBoss/SignalKit_v001/Materials/" + name
    inst = unreal.load_asset(path)
    if inst is not None:
        return inst
    parent = unreal.load_asset(
        "/Game/LineBoss/SignalKit_v001/Materials/" + parent_name)
    inst = tools.create_asset(name,
                              "/Game/LineBoss/SignalKit_v001/Materials",
                              unreal.MaterialInstanceConstant,
                              unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(inst, parent)
    MEL.set_material_instance_vector_parameter_value(inst, "Tint", colour)
    unreal.EditorAssetLibrary.save_loaded_asset(inst, False)
    return inst

ROLES = {
    "cairnwellgreen": unreal.load_asset(
        "/Game/LineBoss/SignalKit_v001/Materials/MI_LB_SK_Emerald_v001"),
    "foundrycharcoal": unreal.load_asset(
        "/Game/LineBoss/SignalKit_v001/Materials/MI_LB_SK_Graphite_v001"),
    "machinedsteel": unreal.load_asset(
        "/Game/LineBoss/SignalKit_v001/Materials/MI_LB_SK_Steel_v001"),
    "warmwhite": unreal.load_asset(
        "/Game/LineBoss/SignalKit_v001/Materials/MI_LB_SK_Cream_v001"),
    "safetyyellow": unreal.load_asset(
        "/Game/LineBoss/SignalKit_v001/Materials/MI_LB_SK_Yellow_v001"),
    "signalred": role_instance("MI_LB_SK_Red_v001",
                               "MI_LB_SK_Graphite_v001",
                               unreal.LinearColor(0.45, 0.06, 0.05, 1.0)),
    "tireblack": role_instance("MI_LB_SK_Tire_v001",
                               "MI_LB_SK_Graphite_v001",
                               unreal.LinearColor(0.012, 0.013, 0.015,
                                                  1.0)),
    "cabglass": unreal.load_asset(
        "/Game/LineBoss/SignalKit_v001/Materials/MI_LB_SK_StatusGlow_v001"),
}

REPORT = {"imported": [], "swapped": 0}
tasks = []
for name in MODELS:
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_as_skeletal", False)
    options.static_mesh_import_data.set_editor_property(
        "combine_meshes", True)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename",
                             os.path.join(SRC, name + ".fbx"))
    task.set_editor_property("destination_path", MESH_DIR)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", False)
    task.set_editor_property("options", options)
    tasks.append(task)
tools.import_asset_tasks(tasks)

NEW = {}
for name, task in zip(MODELS, tasks):
    paths = list(task.get_editor_property("imported_object_paths") or [])
    if not paths:
        raise RuntimeError("import produced nothing for " + name)
    mesh = unreal.load_asset(paths[0].split(".")[0])
    materials = list(mesh.get_editor_property("static_materials"))
    for entry in materials:
        slot = str(entry.get_editor_property(
            "material_slot_name")).lower()
        bound = None
        for fragment, instance in ROLES.items():
            if fragment in slot and instance is not None:
                bound = instance
                break
        if bound is None:
            bound = ROLES["foundrycharcoal"]
        entry.set_editor_property("material_interface", bound)
    mesh.set_editor_property("static_materials", materials)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    NEW[MODELS[name]] = mesh
    REPORT["imported"].append(name)

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

for actor in ACTOR_SUB.get_all_level_actors():
    for component in actor.get_components_by_class(
            unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is None:
            continue
        name = mesh.get_name()
        if name.startswith("SM_LB_Press_"):
            continue
        for fragment, new_mesh in NEW.items():
            if fragment.lower() in name.lower():
                component.set_static_mesh(new_mesh)
                REPORT["swapped"] += 1
                break

if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")

with open(OUT, "w") as handle:
    json.dump(REPORT, handle, indent=1)
unreal.log("LINE_BOSS_INTAKE_SWAP swapped={}".format(REPORT["swapped"]))
