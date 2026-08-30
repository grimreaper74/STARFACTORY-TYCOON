"""edit_spacecraft_environment_v001.py - the owner's verdict on the
slice map was "that's not a game": a dark bare plane. This pass gives
LB_SpacecraftFactory_v001 an environment shell:

1. Floor gets a clean light-industrial material (was near-black).
2. Perimeter walls on three sides - the +X side stays OPEN because the
   departure sprint exits that way.
3. A delivery dock apron at the -X wall (where resource orders will
   visibly arrive; the CargoLift transport drone's home).

Idempotent: every spawned actor is labelled LB_SC_Env_* and existing
ones are removed before respawning. Saves the map.

Run headless (editor closed):
  UnrealEditor-Cmd.exe <proj> -Unattended ... -ExecutePythonScript="<this>"
"""

import unreal

MAP_PATH = ("/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001"
            "/Maps/LB_SpacecraftFactory_v001")
MAT_DIR = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials"
CUBE = "/Engine/BasicShapes/Cube"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not les.load_level(MAP_PATH):
    raise RuntimeError("FAIL CLOSED: could not load " + MAP_PATH)

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
if not lib.does_directory_exist(MAT_DIR):
    lib.make_directory(MAT_DIR)


def constant_material(name, color, roughness, metallic=0.0):
    path = "%s/%s" % (MAT_DIR, name)
    mat = unreal.load_asset(path)
    if mat is not None:
        return mat
    mat = tools.create_asset(name, MAT_DIR, unreal.Material,
                             unreal.MaterialFactoryNew())
    col = mel.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -400, -200)
    col.set_editor_property("constant", unreal.LinearColor(*color))
    mel.connect_material_property(col, "",
                                  unreal.MaterialProperty.MP_BASE_COLOR)
    rough = mel.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -400, 60)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(rough, "",
                                  unreal.MaterialProperty.MP_ROUGHNESS)
    if metallic > 0.0:
        met = mel.create_material_expression(
            mat, unreal.MaterialExpressionConstant, -400, 180)
        met.set_editor_property("r", metallic)
        mel.connect_material_property(met, "",
                                      unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(mat)
    lib.save_asset(path)
    return mat


floor_mat = constant_material("M_LB_FactoryFloor_v001",
                              (0.52, 0.53, 0.55), 0.55)
wall_mat = constant_material("M_LB_FactoryWall_v001",
                             (0.74, 0.74, 0.72), 0.6)
apron_mat = constant_material("M_LB_DockApron_v001",
                              (0.32, 0.34, 0.38), 0.4, 0.4)

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = actor_sub.get_all_level_actors()

# Remove previous environment actors (idempotent re-run).
for actor in list(actors):
    if actor.get_actor_label().startswith("LB_SC_Env_"):
        actor_sub.destroy_actor(actor)
actors = actor_sub.get_all_level_actors()

# Find the floor: the largest thin StaticMeshActor.
floor = None
floor_size = None
for actor in actors:
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    origin, extent = actor.get_actor_bounds(False)
    if (extent.x > 3000 and extent.y > 3000
            and extent.z < 200
            and (floor_size is None or extent.x > floor_size.x)):
        floor = actor
        floor_size = extent
if floor is None:
    raise RuntimeError("FAIL CLOSED: no floor-sized StaticMeshActor found")
comp = floor.get_component_by_class(unreal.StaticMeshComponent)
comp.set_material(0, floor_mat)
unreal.log("FLOOR %s (half %.0f x %.0f cm) rematerialed"
           % (floor.get_actor_label(), floor_size.x, floor_size.y))

origin, extent = floor.get_actor_bounds(False)
cube = unreal.load_asset(CUBE)
if cube is None:
    raise RuntimeError("FAIL CLOSED: engine cube missing")


def spawn_box(label, loc, scale, material):
    actor = actor_sub.spawn_actor_from_object(
        cube, unreal.Vector(*loc))
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    c = actor.get_component_by_class(unreal.StaticMeshComponent)
    c.set_material(0, material)
    c.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    return actor


WALL_H = 900.0   # cm
WALL_T = 60.0
fx, fy = extent.x, extent.y
cx, cy = origin.x, origin.y
# Three walls; +X (departure end) stays open. Engine cube is 100 cm.
spawn_box("LB_SC_Env_Wall_MinX",
          (cx - fx - WALL_T / 2, cy, WALL_H / 2),
          (WALL_T / 100.0, (2 * fy + 2 * WALL_T) / 100.0, WALL_H / 100.0),
          wall_mat)
spawn_box("LB_SC_Env_Wall_MinY",
          (cx, cy - fy - WALL_T / 2, WALL_H / 2),
          ((2 * fx) / 100.0, WALL_T / 100.0, WALL_H / 100.0), wall_mat)
spawn_box("LB_SC_Env_Wall_MaxY",
          (cx, cy + fy + WALL_T / 2, WALL_H / 2),
          ((2 * fx) / 100.0, WALL_T / 100.0, WALL_H / 100.0), wall_mat)

# Delivery dock apron against the -X wall: raised plate, two pylons and
# an orange edge - the CargoLift transport drone's home.
apron_x = cx - fx + 1100.0
spawn_box("LB_SC_Env_DockApron", (apron_x, cy, 12.0),
          (20.0, 14.0, 0.24), apron_mat)
spawn_box("LB_SC_Env_DockEdge", (apron_x + 1010.0, cy, 16.0),
          (0.4, 14.0, 0.34),
          constant_material("M_LB_DockEdge_v001", (0.9, 0.35, 0.05), 0.5))
for sy in (-1, 1):
    spawn_box("LB_SC_Env_DockPylon_%d" % sy,
              (apron_x - 900.0, cy + sy * 620.0, 260.0),
              (1.2, 1.2, 5.2), wall_mat)

if not les.save_current_level():
    raise RuntimeError("FAIL CLOSED: could not save " + MAP_PATH)
unreal.log("ENVIRONMENT v001 DONE: floor + 3 walls + dock apron")
