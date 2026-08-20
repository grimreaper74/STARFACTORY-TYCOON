"""Import Codex's SignalKit and dress the weld lines with it.

Status pillars at line heads/exits, hanging line boards over each line,
shop boards on the south wall, cable-tray runs beside each line, hose
festoons at robot cells, kanban boards behind cells, floor marker plates
along the walk aisles. Weld geometry as in place_weld_lines. Idempotent
via LB.SignalKit. Run with -ExecutePythonScript.
"""
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate/SignalKit_v001")
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
MESH_DIR = "/Game/LineBoss/SignalKit_v001"
MAT_DIR = "/Game/LineBoss/SignalKit_v001/Materials"
TAG = "LB.SignalKit"
OUT = "C:/Temp/lb_signalkit.json"

NAMES = ["SM_LB_Site_StatusPillar_v001", "SM_LB_Sign_LineBoard_v001",
         "SM_LB_Sign_ShopBoard_v001", "SM_LB_Detail_CableTray_2000_v001",
         "SM_LB_Detail_HoseFestoon_v001", "SM_LB_Detail_KanbanBoard_v001",
         "SM_LB_Detail_FloorMarkerSet_v001"]

REPORT = {"imported": {}, "placed": 0, "cleared": 0}
tools = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary

# Flat tint master (as the vegetation one) plus an emissive master for
# the status strip.
def ensure_master(name, emissive):
    master = unreal.load_asset("{}/{}".format(MAT_DIR, name))
    if master is not None:
        return master
    master = tools.create_asset(name, MAT_DIR, unreal.Material,
                                unreal.MaterialFactoryNew())
    tint = MEL.create_material_expression(
        master, unreal.MaterialExpressionVectorParameter, -420, 0)
    tint.set_editor_property("parameter_name", "Tint")
    MEL.connect_material_property(
        tint, "", unreal.MaterialProperty.MP_BASE_COLOR)
    if emissive:
        glow = MEL.create_material_expression(
            master, unreal.MaterialExpressionVectorParameter, -420, 240)
        glow.set_editor_property("parameter_name", "Glow")
        MEL.connect_material_property(
            glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    else:
        rough = MEL.create_material_expression(
            master, unreal.MaterialExpressionConstant, -420, 240)
        rough.set_editor_property("r", 0.7)
        MEL.connect_material_property(
            rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(master)
    unreal.EditorAssetLibrary.save_loaded_asset(master, False)
    return master

FLAT = ensure_master("M_LB_SignalKit_Flat_v001", False)
GLOW = ensure_master("M_LB_SignalKit_Glow_v001", True)

def instance(name, parent, vectors):
    inst = unreal.load_asset("{}/{}".format(MAT_DIR, name))
    if inst is None:
        inst = tools.create_asset(name, MAT_DIR,
                                  unreal.MaterialInstanceConstant,
                                  unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(inst, parent)
    for parameter, value in vectors.items():
        MEL.set_material_instance_vector_parameter_value(
            inst, parameter, value)
    unreal.EditorAssetLibrary.save_loaded_asset(inst, False)
    return inst

ROLES = {
    "graphite": instance("MI_LB_SK_Graphite_v001", FLAT,
        {"Tint": unreal.LinearColor(0.044, 0.053, 0.065, 1.0)}),
    "steel": instance("MI_LB_SK_Steel_v001", FLAT,
        {"Tint": unreal.LinearColor(0.25, 0.28, 0.31, 1.0)}),
    "cream": instance("MI_LB_SK_Cream_v001", FLAT,
        {"Tint": unreal.LinearColor(0.80, 0.77, 0.70, 1.0)}),
    "emerald": instance("MI_LB_SK_Emerald_v001", FLAT,
        {"Tint": unreal.LinearColor(0.028, 0.155, 0.116, 1.0)}),
    "yellow": instance("MI_LB_SK_Yellow_v001", FLAT,
        {"Tint": unreal.LinearColor(0.60, 0.42, 0.02, 1.0)}),
    "glow": instance("MI_LB_SK_StatusGlow_v001", GLOW,
        {"Tint": unreal.LinearColor(0.06, 0.35, 0.24, 1.0),
         "Glow": unreal.LinearColor(0.18, 1.40, 0.95, 1.0)}),
}

def role_for(slot):
    lowered = slot.lower()
    if "emissive" in lowered or "status" in lowered:
        return "glow"
    if "signface" in lowered or "cream" in lowered or "card" in lowered:
        return "cream"
    if "yellow" in lowered or "hazard" in lowered:
        return "yellow"
    if "emerald" in lowered or "band" in lowered or "header" in lowered:
        return "emerald"
    if "steel" in lowered or "rail" in lowered or "frame" in lowered \
            or "tray" in lowered or "rod" in lowered:
        return "steel"
    return "graphite"

tasks = []
for name in NAMES:
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_as_skeletal", False)
    options.static_mesh_import_data.set_editor_property(
        "combine_meshes", True)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename",
                             os.path.join(SRC, name, name + ".fbx"))
    task.set_editor_property("destination_path", MESH_DIR)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)
    tasks.append(task)
tools.import_asset_tasks(tasks)

MESHES = {}
for name, task in zip(NAMES, tasks):
    paths = list(task.get_editor_property("imported_object_paths") or [])
    if not paths:
        raise RuntimeError("import produced nothing for {}".format(name))
    mesh = unreal.load_asset(paths[0].split(".")[0])
    materials = list(mesh.get_editor_property("static_materials"))
    bound = []
    for entry in materials:
        slot = str(entry.get_editor_property("material_slot_name"))
        role = role_for(slot)
        entry.set_editor_property("material_interface", ROLES[role])
        bound.append("{}->{}".format(slot, role))
    mesh.set_editor_property("static_materials", materials)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    REPORT["imported"][name] = bound
    MESHES[name] = mesh

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or TARGET.rsplit("/", 1)[-1] != world.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")

for actor in list(ACTOR_SUB.get_all_level_actors()):
    if TAG in [str(t) for t in actor.tags]:
        ACTOR_SUB.destroy_actor(actor)
        REPORT["cleared"] += 1

def spawn(name, x, y, yaw, z=0.0):
    actor = ACTOR_SUB.spawn_actor_from_object(
        MESHES[name], unreal.Vector(x, y, z),
        unreal.Rotator(0.0, 0.0, yaw))
    if actor is None:
        return
    REPORT["placed"] += 1
    actor.set_actor_label("SignalKit_{:04d}".format(REPORT["placed"]))
    for tag in (TAG, "LB.Environment.VisualOnly", "LB.NotProcessWIP"):
        actor.tags.append(tag)

X_WEST, X_EAST = -19500.0, -3400.0
NORTH, MIDDLE, SOUTH = -5192.0, -9099.0, -13067.0

for line_y in (NORTH, MIDDLE, SOUTH):
    # Status pillars at both heads of every line.
    for x, side in ((X_WEST - 500.0, 1), (X_EAST + 500.0, -1)):
        spawn("SM_LB_Site_StatusPillar_v001", x, line_y + 380.0 * side, 0.0)
    # Hanging line boards every ~13 m.
    x = X_WEST + 1200.0
    while x <= X_EAST:
        spawn("SM_LB_Sign_LineBoard_v001", x, line_y, 0.0, 500.0)
        x += 1280.0
    # Cable tray run alongside the line.
    x = X_WEST
    while x <= X_EAST:
        spawn("SM_LB_Detail_CableTray_2000_v001", x, line_y + 520.0, 0.0,
              380.0)
        x += 200.0
    # Festoons over the robot side, kanban boards and floor markers along
    # the walk aisle.
    x = X_WEST + 900.0
    index = 0
    while x <= X_EAST:
        if index % 2 == 0:
            spawn("SM_LB_Detail_HoseFestoon_v001", x, line_y - 420.0, 0.0,
                  300.0)
        if index % 4 == 1:
            spawn("SM_LB_Detail_KanbanBoard_v001", x, line_y + 760.0,
                  180.0)
        if index % 6 == 2:
            spawn("SM_LB_Detail_FloorMarkerSet_v001", x, line_y + 900.0,
                  0.0, 2.0)
        x += 640.0
        index += 1

# Shop boards on the south wall.
x = X_WEST + 2000.0
while x <= X_EAST:
    spawn("SM_LB_Sign_ShopBoard_v001", x, -14280.0, 0.0, 320.0)
    x += 4000.0

if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")

with open(OUT, "w") as handle:
    json.dump(REPORT, handle, indent=1)
unreal.log("LINE_BOSS_SIGNALKIT placed={} cleared={}".format(
    REPORT["placed"], REPORT["cleared"]))
