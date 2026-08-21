"""Import dev car v003 and stage it in the plant.

Imports the palette-passed concept as a first-class vehicle asset and
parks two beside the transporter staging so the owner sees it in the
world on next open. Slot names bind to the SignalKit material
instances by the established fragment mapping. Re-runnable: clears
its own DevCar_ actors first.
"""
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
BASE = ("C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/"
        "SourceAssets/Candidate/DevCar_v003/{0}/{0}.fbx")
NAMES = ("SM_LB_DevCar_Concept_v003", "SM_LB_DevCar_ConceptLOD1_v003",
         "SM_LB_DevCar_ConceptLOD2_v003")
PART_BASE = ("C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/"
             "SourceAssets/Candidate/DevCarParts_v001/{0}/{0}.fbx")
PARTS = ("SM_LB_DevCar_Part_Wheel_v001",)
SRC = BASE.format(NAMES[0])
MESH_DIR = "/Game/LineBoss/Candidates/Vehicles/DevCar_v003"
MESH_PATH = MESH_DIR + "/SM_LB_DevCar_Concept_v003"
SK_MATS = "/Game/LineBoss/SignalKit_v001/Materials/"
OUT = "C:/Temp/lb_place_devcar.json"

ROLES = {
    "cairnwellgreen": "MI_LB_SK_Emerald_v001",
    "foundrycharcoal": "MI_LB_SK_Graphite_v001",
    "machinedsteel": "MI_LB_SK_Steel_v001",
    "warmwhite": "MI_LB_SK_StatusGlow_v001",
    "signalred": "MI_LB_SK_Red_v001",
    "tireblack": "MI_LB_SK_Tire_v001",
    "glass": "MI_LB_SK_Glass_v001",
}

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

def import_one(name):
    src_path = BASE.format(name)
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_as_skeletal", False)
    options.static_mesh_import_data.set_editor_property(
        "combine_meshes", True)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src_path)
    task.set_editor_property("destination_path", MESH_DIR)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", False)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    m = unreal.EditorAssetLibrary.load_asset(MESH_DIR + "/" + name)
    if not m:
        unreal.log("DEVCAR_IMPORT_FAIL " + name)
        return None
    mats = list(m.get_editor_property("static_materials"))
    n = 0
    for entry in mats:
        slot = str(entry.get_editor_property("material_slot_name")).lower()
        for fragment, instance in ROLES.items():
            if fragment in slot:
                mic = unreal.EditorAssetLibrary.load_asset(
                    SK_MATS + instance)
                if mic:
                    entry.set_editor_property("material_interface", mic)
                    n += 1
                break
    m.set_editor_property("static_materials", mats)
    unreal.EditorAssetLibrary.save_asset(MESH_DIR + "/" + name)
    unreal.log("DEVCAR_IMPORTED {} tris={} bound={}".format(
        name, m.get_num_triangles(0), n))
    return m

for extra in NAMES[1:]:
    import_one(extra)

for part in PARTS:
    global BASE
    saved = BASE
    BASE = PART_BASE
    import_one(part)
    BASE = saved

options = unreal.FbxImportUI()
options.set_editor_property("import_mesh", True)
options.set_editor_property("import_materials", False)
options.set_editor_property("import_textures", False)
options.set_editor_property("import_as_skeletal", False)
options.static_mesh_import_data.set_editor_property("combine_meshes", True)
task = unreal.AssetImportTask()
task.set_editor_property("filename", SRC)
task.set_editor_property("destination_path", MESH_DIR)
task.set_editor_property("destination_name", "SM_LB_DevCar_Concept_v003")
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", False)
task.set_editor_property("options", options)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
if not mesh:
    raise RuntimeError("dev car mesh failed to import")
materials = list(mesh.get_editor_property("static_materials"))
bound = 0
for entry in materials:
    slot = str(entry.get_editor_property("material_slot_name")).lower()
    for fragment, instance in ROLES.items():
        if fragment in slot:
            mic = unreal.EditorAssetLibrary.load_asset(SK_MATS + instance)
            if mic:
                entry.set_editor_property("material_interface", mic)
                bound += 1
            break
mesh.set_editor_property("static_materials", materials)
unreal.EditorAssetLibrary.save_asset(MESH_PATH)
box = mesh.get_bounding_box()
size = box.max - box.min
unreal.log("DEVCAR_MESH size={:.0f}x{:.0f}x{:.0f} slots_bound={}".format(
    size.x, size.y, size.z, bound))

report = {"cleared": 0, "placed": []}
for actor in list(ACTOR_SUB.get_all_level_actors()):
    if actor.get_actor_label().startswith("DevCar_"):
        ACTOR_SUB.destroy_actor(actor)
        report["cleared"] += 1

SPOTS = ((15600.0, 15500.0, 25.0), (16300.0, 15480.0, 205.0))
for index, (x, y, yaw) in enumerate(SPOTS):
    actor = ACTOR_SUB.spawn_actor_from_object(
        mesh, unreal.Vector(x, y, 0.0), unreal.Rotator(0.0, 0.0, yaw))
    if actor:
        actor.set_actor_label("DevCar_{:02d}".format(index + 1))
        report["placed"].append([actor.get_actor_label(), x, y])

if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")
with open(OUT, "w") as handle:
    json.dump(report, handle, indent=1)
unreal.log("DEVCAR_PLACED n={}".format(len(report["placed"])))
