"""Import journey batch 2, swap intake pieces, stage the transporters.

Destack magazine, cleaning dock and cleaning robot swap over their old
actors by mesh-name fragment. The tractor and trailer import fresh and
two coupled transporters stage in the dispatch lanes (trailer kingpin
at +4.55 local, tractor fifth wheel at -1.55, so the tractor sits +6.1
ahead of the trailer at yaw 0). Idempotent via LB.Transporter for the
staged pairs. Run with -ExecutePythonScript.
"""
import json
import os

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_batch02_swap.json"
TAG = "LB.Transporter"

IMPORTS = {
    "SM_LB_Press_DestackMagazine_v002": (
        r"PressShop/IntakeRework_v001",
        "/Game/LineBoss/Candidates/PressShop/IntakeRework_v001",
        "DestackMagazine"),
    "SM_LB_Press_CleaningDock_v002": (
        r"PressShop/IntakeRework_v001",
        "/Game/LineBoss/Candidates/PressShop/IntakeRework_v001",
        "CleaningDock"),
    "SM_LB_Press_CleaningRobot_v002": (
        r"PressShop/IntakeRework_v001",
        "/Game/LineBoss/Candidates/PressShop/IntakeRework_v001",
        "CleaningRobot"),
    "SM_LB_Site_Transporter_v001_Tractor": (
        r"Site/TransporterRework_v001",
        "/Game/LineBoss/Site/Transporter_v001", None),
    "SM_LB_Site_Transporter_v001_Trailer": (
        r"Site/TransporterRework_v001",
        "/Game/LineBoss/Site/Transporter_v001", None),
}

SRC_ROOT = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
            r"/SourceAssets/Candidate")

MEL = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
MAT_ROOT = "/Game/LineBoss/SignalKit_v001/Materials/"

def role_instance(name, colour):
    inst = unreal.load_asset(MAT_ROOT + name)
    if inst is not None:
        return inst
    parent = unreal.load_asset(MAT_ROOT + "MI_LB_SK_Graphite_v001")
    inst = tools.create_asset(name, MAT_ROOT.rstrip("/"),
                              unreal.MaterialInstanceConstant,
                              unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(inst, parent)
    MEL.set_material_instance_vector_parameter_value(inst, "Tint", colour)
    unreal.EditorAssetLibrary.save_loaded_asset(inst, False)
    return inst

ROLES = {
    "cairnwellgreen": unreal.load_asset(MAT_ROOT + "MI_LB_SK_Emerald_v001"),
    "foundrycharcoal": unreal.load_asset(
        MAT_ROOT + "MI_LB_SK_Graphite_v001"),
    "machinedsteel": unreal.load_asset(MAT_ROOT + "MI_LB_SK_Steel_v001"),
    "warmwhite": unreal.load_asset(MAT_ROOT + "MI_LB_SK_Cream_v001"),
    "safetyyellow": unreal.load_asset(MAT_ROOT + "MI_LB_SK_Yellow_v001"),
    "signalred": role_instance("MI_LB_SK_Red_v001",
                               unreal.LinearColor(0.45, 0.06, 0.05, 1.0)),
    "tireblack": role_instance("MI_LB_SK_Tire_v001",
                               unreal.LinearColor(0.012, 0.013, 0.015,
                                                  1.0)),
    "cabglass": role_instance("MI_LB_SK_Glass_v001",
                              unreal.LinearColor(0.03, 0.08, 0.08, 1.0)),
}

REPORT = {"imported": [], "swapped": 0, "staged": 0}
NEW = {}
for name, (folder, dest, fragment) in IMPORTS.items():
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_as_skeletal", False)
    options.static_mesh_import_data.set_editor_property(
        "combine_meshes", True)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename",
                             os.path.join(SRC_ROOT, folder, name + ".fbx"))
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", False)
    task.set_editor_property("options", options)
    tools.import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths") or [])
    if not paths:
        raise RuntimeError("import produced nothing for " + name)
    mesh = unreal.load_asset(paths[0].split(".")[0])
    materials = list(mesh.get_editor_property("static_materials"))
    for entry in materials:
        slot = str(entry.get_editor_property(
            "material_slot_name")).lower()
        bound = None
        for key, instance in ROLES.items():
            if key in slot and instance is not None:
                bound = instance
                break
        entry.set_editor_property(
            "material_interface", bound or ROLES["foundrycharcoal"])
    mesh.set_editor_property("static_materials", materials)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    NEW[name] = (mesh, fragment)
    REPORT["imported"].append(name)

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

# Swap the intake pieces over their old actors.
for actor in ACTOR_SUB.get_all_level_actors():
    for component in actor.get_components_by_class(
            unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is None:
            continue
        current = mesh.get_name()
        if current.startswith("SM_LB_Press_") \
                or current.startswith("SM_LB_Site_Transporter"):
            continue
        for name, (new_mesh, fragment) in NEW.items():
            if fragment and fragment.lower() in current.lower():
                component.set_static_mesh(new_mesh)
                REPORT["swapped"] += 1
                break

# Stage two coupled transporters in the dispatch lanes.
for actor in list(ACTOR_SUB.get_all_level_actors()):
    if TAG in [str(t) for t in actor.tags]:
        ACTOR_SUB.destroy_actor(actor)

def stage(key, x, y, yaw):
    mesh = NEW[key][0]
    actor = ACTOR_SUB.spawn_actor_from_object(
        mesh, unreal.Vector(x, y, 0.0), unreal.Rotator(0.0, 0.0, yaw))
    if actor is None:
        return
    REPORT["staged"] += 1
    actor.set_actor_label("Site_Transporter_{:02d}".format(
        REPORT["staged"]))
    for tag in (TAG, "LB.Environment.VisualOnly", "LB.NotProcessWIP"):
        actor.tags.append(tag)

for base_x, base_y in ((14000.0, 16200.0), (17200.0, 16900.0)):
    stage("SM_LB_Site_Transporter_v001_Trailer", base_x, base_y, 0.0)
    stage("SM_LB_Site_Transporter_v001_Tractor", base_x + 610.0, base_y,
          0.0)

if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")

with open(OUT, "w") as handle:
    json.dump(REPORT, handle, indent=1)
unreal.log("LINE_BOSS_BATCH02 swapped={} staged={}".format(
    REPORT["swapped"], REPORT["staged"]))
