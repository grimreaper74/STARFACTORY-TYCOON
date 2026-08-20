"""Body-weld close-range density pass.

The zoom captures show press holding up at mockup height while body weld
reads sparse: empty aisles between the three lines (y=-13067/-9099/-5192)
and bare line edges. The target mockup fills those with stillages, panel
racks and dollies. Places deterministic aisle clusters and line-edge
racks from the weld/shared kit meshes already in /Game/LineBoss.
Idempotent via LB.WeldDensity. Run with -ExecutePythonScript.
"""
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.WeldDensity"
OUT = "C:/Temp/lb_weld_density.json"

# Preferred name fragments, best first; the script reports what it found.
WANTED = ["Stillage", "PanelRack", "Rack", "PanelStack", "Dolly", "Trolley",
          "Cart", "Bin"]

REPORT = {"meshes": [], "placed": 0, "cleared": 0}

registry = unreal.AssetRegistryHelpers.get_asset_registry()
filt = unreal.ARFilter(
    class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")],
    package_paths=["/Game/LineBoss"], recursive_paths=True)
candidates = []
for data in registry.get_assets(filt):
    name = str(data.asset_name)
    for rank, fragment in enumerate(WANTED):
        if fragment.lower() in name.lower():
            candidates.append((rank, name, str(data.package_name)))
            break
candidates.sort()
MESHES = []
seen = set()
for rank, name, package in candidates:
    if name in seen:
        continue
    seen.add(name)
    mesh = unreal.load_asset(package)
    if mesh is None:
        continue
    box = mesh.get_bounding_box()
    size = box.max - box.min
    # Aisle dressing must be trolley-scale: skip tiny clutter and anything
    # conveyor-length.
    if size.x < 60 or size.x > 700 or size.y > 700 or size.z > 400:
        continue
    MESHES.append(mesh)
    REPORT["meshes"].append(name)
    if len(MESHES) >= 6:
        break
if len(MESHES) < 2:
    raise RuntimeError("too few dressing meshes found: {}".format(
        REPORT["meshes"]))

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

def spawn(mesh, x, y, yaw):
    actor = ACTOR_SUB.spawn_actor_from_object(
        mesh, unreal.Vector(x, y, 0.0), unreal.Rotator(0.0, 0.0, yaw))
    if actor is None:
        return
    REPORT["placed"] += 1
    actor.set_actor_label("Weld_Dress_{:03d}".format(REPORT["placed"]))
    for tag in (TAG, "LB.Environment.VisualOnly", "LB.NotProcessWIP"):
        actor.tags.append(tag)

# Aisle clusters between the three weld lines. Gantry legs stand ON the
# lines now, so the aisle centres are free; clusters of 2-3 racks every
# ~2.2 m bay pitch with deterministic variety and yaw.
index = 0
for aisle_y in (-11150.0, -7050.0):
    x = -19600.0
    while x <= -3000.0:
        cluster = 2 + (index % 2)
        for member in range(cluster):
            mesh = MESHES[(index + member) % len(MESHES)]
            offset_x = member * 240.0
            offset_y = -180.0 if member % 2 else 180.0
            yaw = float(((index * 31) + member * 90) % 360)
            spawn(mesh, x + offset_x, aisle_y + offset_y, yaw)
        index += 1
        x += 2200.0

# Line-edge racks: singles along the outer edges of the outer lines.
for edge_y, side in ((-13900.0, 1), (-4400.0, -1)):
    x = -18800.0
    while x <= -3800.0:
        mesh = MESHES[(index * 7) % len(MESHES)]
        spawn(mesh, x, edge_y, float((index * 53) % 180))
        index += 1
        x += 2600.0

if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")

with open(OUT, "w") as handle:
    json.dump(REPORT, handle, indent=1)
unreal.log("LINE_BOSS_WELD_DENSITY placed={} meshes={}".format(
    REPORT["placed"], REPORT["meshes"]))
