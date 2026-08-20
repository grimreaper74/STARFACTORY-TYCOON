"""Import Codex's vegetation set and plant the site perimeter.

Per SITE_PLAN_2026-08-19: trees line the verge between the fence and the
ring road on all four edges (gaps at both gates and the dispatch lanes),
hedges flank the main-gate approach, grass tufts scatter the verges.
Deterministic variant/yaw/scale from the placement index - no RNG, so
reruns are identical. Idempotent via LB.SiteVeg. Slot materials are
created here (role-named tints per palette D); the FBXs import bare.
"""
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate/Site/Vegetation_v001")
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
MESH_DIR = "/Game/LineBoss/Site/Vegetation_v001"
MAT_DIR = "/Game/LineBoss/Site/Vegetation_v001/Materials"
TAG = "LB.SiteVeg"
OUT = "C:/Temp/lb_siteveg.json"

NAMES = ["SM_LB_Site_Tree_v001_A", "SM_LB_Site_Tree_v001_B",
         "SM_LB_Site_Tree_v001_C", "SM_LB_Site_Hedge_2000_v001",
         "SM_LB_Site_GrassPatch_v001"]

REPORT = {"imported": {}, "materials": {}, "placed": {}, "cleared": 0}
tools = unreal.AssetToolsHelpers.get_asset_tools()

# ---- materials: one flat master, three role tints (palette D greens) ----
master = unreal.load_asset(MAT_DIR + "/M_LB_Site_Vegetation_v001")
if master is None:
    master = tools.create_asset("M_LB_Site_Vegetation_v001", MAT_DIR,
                                unreal.Material, unreal.MaterialFactoryNew())
    tint = unreal.MaterialEditingLibrary.create_material_expression(
        master, unreal.MaterialExpressionVectorParameter, -420, 0)
    tint.set_editor_property("parameter_name", "Tint")
    tint.set_editor_property("default_value",
                             unreal.LinearColor(0.2, 0.3, 0.2, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        tint, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        master, unreal.MaterialExpressionConstant, -420, 240)
    rough.set_editor_property("r", 0.85)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(master)
    unreal.EditorAssetLibrary.save_loaded_asset(master, False)

TINTS = {
    "Foliage": unreal.LinearColor(0.075, 0.160, 0.110, 1.0),
    "Trunk": unreal.LinearColor(0.100, 0.075, 0.055, 1.0),
    "Grass": unreal.LinearColor(0.090, 0.140, 0.070, 1.0),
}
INSTANCES = {}
for role, colour in TINTS.items():
    name = "MI_LB_Site_{}_v001".format(role)
    inst = unreal.load_asset("{}/{}".format(MAT_DIR, name))
    if inst is None:
        inst = tools.create_asset(name, MAT_DIR,
                                  unreal.MaterialInstanceConstant,
                                  unreal.MaterialInstanceConstantFactoryNew())
        unreal.MaterialEditingLibrary.set_material_instance_parent(
            inst, master)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        inst, "Tint", colour)
    unreal.EditorAssetLibrary.save_loaded_asset(inst, False)
    INSTANCES[role] = inst
    REPORT["materials"][name] = [round(colour.r, 3), round(colour.g, 3),
                                 round(colour.b, 3)]

# ---- import the five meshes and bind slots by role fragment ----
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
                             os.path.join(SRC, name + ".fbx"))
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
        role = next((r for r in INSTANCES if r.lower() in slot.lower()),
                    None)
        if role is None:
            role = "Foliage" if "Tree" in name or "Hedge" in name \
                else "Grass"
        entry.set_editor_property("material_interface", INSTANCES[role])
        bound.append("{}->{}".format(slot, role))
    mesh.set_editor_property("static_materials", materials)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    box = mesh.get_bounding_box()
    REPORT["imported"][name] = {
        "size": [round(box.max.x - box.min.x, 1),
                 round(box.max.y - box.min.y, 1),
                 round(box.max.z - box.min.z, 1)],
        "slots": bound,
    }
    MESHES[name] = mesh

# ---- plant ----
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

COUNT = {"tree": 0, "hedge": 0, "grass": 0}

def spawn(mesh_name, x, y, yaw, scale, kind):
    actor = ACTOR_SUB.spawn_actor_from_object(
        MESHES[mesh_name], unreal.Vector(x, y, 0.0),
        unreal.Rotator(0.0, 0.0, yaw))
    if actor is None:
        return
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    COUNT[kind] += 1
    actor.set_actor_label("Site_Veg_{}_{:03d}".format(
        kind.capitalize(), COUNT[kind]))
    for tag in (TAG, "LB.Environment.VisualOnly", "LB.NotProcessWIP"):
        actor.tags.append(tag)

TREES = ["SM_LB_Site_Tree_v001_A", "SM_LB_Site_Tree_v001_B",
         "SM_LB_Site_Tree_v001_C"]

def plant_run(kind, positions):
    for index, (x, y) in enumerate(positions):
        yaw = float((index * 47) % 360)
        scale = 0.95 + 0.15 * ((index * 13) % 10) / 10.0
        if kind == "tree":
            spawn(TREES[index % 3], x, y, yaw, scale, "tree")
        elif kind == "grass":
            spawn("SM_LB_Site_GrassPatch_v001", x, y, yaw,
                  0.8 + 0.5 * ((index * 7) % 10) / 10.0, "grass")

def steps(start, stop, step):
    value = start
    while value <= stop:
        yield float(value)
        value += step

# Verge runs; gaps at the NE main gate, the west service gate and the
# south-east dispatch lanes.
tree_rows = []
tree_rows += [(x, 19700.0) for x in steps(-35500, 35500, 1400)]
tree_rows += [(x, -18700.0) for x in steps(-35500, 18000, 1400)]
tree_rows += [(-36200.0, y) for y in steps(-17500, 18500, 1400)
              if not -1500.0 <= y <= 2500.0]
tree_rows += [(36200.0, y) for y in steps(-17500, 10500, 1400)]
plant_run("tree", tree_rows)

grass_rows = []
grass_rows += [(x + 700.0, 19750.0) for x, _ in
               [(x, 0) for x in steps(-35500, 34100, 1400)]]
grass_rows += [(x + 700.0, -18750.0) for x in steps(-35500, 16600, 1400)]
grass_rows += [(-36150.0, y + 700.0) for y in steps(-17500, 17100, 1400)
               if not -2200.0 <= y <= 3200.0]
plant_run("grass", grass_rows)

# Hedge rows flank the main-gate approach road (gatehouse ~ (34200, 13000)).
hedge_index = 0
for y in (12200.0, 13800.0):
    for x in steps(30200, 34000, 200):
        spawn("SM_LB_Site_Hedge_2000_v001", x, y, 0.0, 1.0, "hedge")
        hedge_index += 1

REPORT["placed"] = dict(COUNT)
if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")

with open(OUT, "w") as handle:
    json.dump(REPORT, handle, indent=1)
unreal.log("LINE_BOSS_SITEVEG {}".format(json.dumps(REPORT["placed"])))
