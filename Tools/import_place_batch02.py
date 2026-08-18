"""Batch 02: import six authored machines and place them, including the press fix.

The two SM_LB_* press pieces stand in for the SM_CA_Factory_*_MeshyMaster_v632
meshes whose 40 components the transplant had to skip. Their positions are read
LIVE from the reference (never composed by hand), and the transplant's offset is
derived empirically from an anchor actor present in both maps, because the
transplant computed its offset from content bounds and its report is gone.

Idempotent: clears LB.Batch02 before placing. Run with -ExecutePythonScript.
"""
import io
import json
import os

import unreal

SRC = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
       r"/SourceAssets/Candidate")
REFERENCE = "/Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001"
TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Batch02"
OUT = os.environ.get("LB_BATCH_OUT", "C:/Temp/lb_batch02.json")

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
REPORT = {"replacements": {}, "imported": {}, "placed": {}, "cleared": 0}


def require_world(path):
    world = unreal.EditorLevelLibrary.get_editor_world()
    if world is None or path.rsplit("/", 1)[-1] != world.get_name():
        raise RuntimeError("wrong world open; use -ExecutePythonScript")


# ---- phase A: read the Meshy component transforms from the reference --------
if not LEVEL_SUB.load_level(REFERENCE):
    raise RuntimeError("could not load {}".format(REFERENCE))
require_world(REFERENCE)

elect, hmi = [], []
anchors = {}
for actor in ACTOR_SUB.get_all_level_actors():
    if actor is None:
        continue
    comps = list(actor.get_components_by_class(unreal.StaticMeshComponent))
    kept = [c for c in comps if c.static_mesh is not None]
    for comp in kept:
        path = comp.static_mesh.get_path_name().lower()
        transform = comp.get_world_transform()
        loc = transform.translation
        yaw = transform.rotation.rotator().yaw
        record = (round(loc.x, 1), round(loc.y, 1), round(yaw, 1))
        if "elect_net_meshymaster" in path:
            elect.append(record)
        elif "opera_hmi_meshymaster" in path:
            hmi.append(record)
    # Anchor candidates: single-mesh actors with clean provenance, keyed by label.
    if len(kept) == 1:
        path = kept[0].static_mesh.get_path_name().lower()
        if "meshy" not in path and "externalgenerated" not in path:
            label = actor.get_actor_label()
            loc = kept[0].get_world_transform().translation
            anchors.setdefault(label, []).append((loc.x, loc.y))

if not elect or not hmi:
    raise RuntimeError("found no Meshy components to replace: {} / {}".format(
        len(elect), len(hmi)))
REPORT["replacements"] = {"elect_net": len(elect), "opera_hmi": len(hmi)}
anchor_candidates = [(label, locs[0]) for label, locs in anchors.items()
                     if len(locs) == 1]
if not anchor_candidates:
    raise RuntimeError("no unique single-mesh anchor actor in the reference")

# ---- phase B: import the six FBX ---------------------------------------------
MODELS = [
    ("WeldShop/FramingGate_v001", "SM_LB_Weld_FramingGate_v001"),
    ("WeldShop/SkidConveyor_v001", "SM_LB_Weld_SkidConveyorModule_3000_v001"),
    ("WeldShop/IndexTurntable_v001", "SM_LB_Weld_IndexTurntable_v001"),
    ("WeldShop/RoofMagazine_v001", "SM_LB_Weld_RoofMagazine_v001"),
    ("PressShop/ElectricalCabinetNet_v001", "SM_LB_ElectricalCabinetNet_v001"),
    ("PressShop/OperatorHMIStand_v001", "SM_LB_OperatorHMIStand_v001"),
]
tools = unreal.AssetToolsHelpers.get_asset_tools()
tasks = []
for folder, name in MODELS:
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_as_skeletal", False)
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", os.path.join(SRC, folder, name + ".fbx"))
    task.set_editor_property("destination_path",
                             "/Game/LineBoss/Candidates/" + folder)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)
    tasks.append(task)
tools.import_asset_tasks(tasks)

MESHES = {}
for (folder, name), task in zip(MODELS, tasks):
    paths = list(task.get_editor_property("imported_object_paths") or [])
    if not paths:
        raise RuntimeError("import produced nothing for {}".format(name))
    mesh = unreal.load_asset(paths[0].split(".")[0])
    if mesh is None:
        raise RuntimeError("could not load {}".format(paths[0]))
    size = mesh.get_bounding_box().max - mesh.get_bounding_box().min
    REPORT["imported"][name] = [round(size.x, 1), round(size.y, 1),
                                round(size.z, 1)]
    MESHES[name] = mesh

# ---- phase C: open the target, derive the transplant offset, place ------------
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")
require_world(TARGET)

targets_by_label = {}
for actor in ACTOR_SUB.get_all_level_actors():
    if actor and unreal.Name("LB.Press.Transplant") in actor.tags:
        targets_by_label.setdefault(actor.get_actor_label(), []).append(actor)

delta = None
for label, (ax, ay) in anchor_candidates:
    matches = targets_by_label.get("PT_" + label, [])
    if len(matches) == 1:
        here = matches[0].get_actor_location()
        delta = (here.x - ax, here.y - ay)
        REPORT["anchor"] = {"label": label,
                            "delta": [round(delta[0], 1), round(delta[1], 1)]}
        break
if delta is None:
    raise RuntimeError("no anchor label matched uniquely in the target map")

for actor in ACTOR_SUB.get_all_level_actors():
    if actor and unreal.Name(TAG) in actor.tags:
        ACTOR_SUB.destroy_actor(actor)
        REPORT["cleared"] += 1


def place(name, x, y, yaw=0.0, label=None):
    actor = ACTOR_SUB.spawn_actor_from_object(
        MESHES[name], unreal.Vector(x, y, 0.0), unreal.Rotator(0.0, yaw, 0.0))
    if actor is None:
        return
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    if label:
        actor.set_actor_label(label)
    key = name.rsplit("_", 2)[0]
    REPORT["placed"][key] = REPORT["placed"].get(key, 0) + 1


# Press replacements at the recorded Meshy positions, floor pivots at Z=0.
for n, (x, y, yaw) in enumerate(elect):
    place("SM_LB_ElectricalCabinetNet_v001", x + delta[0], y + delta[1], yaw,
          "PT_ElectricalCabinetNet_{:02d}".format(n))
for n, (x, y, yaw) in enumerate(hmi):
    place("SM_LB_OperatorHMIStand_v001", x + delta[0], y + delta[1], yaw,
          "PT_OperatorHMIStand_{:02d}".format(n))

# Framing gates on the weld line BETWEEN stations (station centres already
# carry starter-presentation content; the gate straddles the open line).
place("SM_LB_Weld_FramingGate_v001", -8050.0, -7000.0, 0.0, "Weld_FramingGate_A")
place("SM_LB_Weld_FramingGate_v001", -14050.0, -11200.0, 0.0, "Weld_FramingGate_B")

# Return skid line: fourteen 3 m modules chained under the aisle mezzanine
# (deck at Z 282 clears the 84 cm module; pillars sit at y -8800/-9400).
for n in range(14):
    place("SM_LB_Weld_SkidConveyorModule_3000_v001", -17350.0 + n * 300.0,
          -9100.0, 0.0, "Weld_ReturnSkid_{:02d}".format(n))

# Framing cell support north of run A, clear of batch-01 welders and dressers.
place("SM_LB_Weld_IndexTurntable_v001", -7050.0, -5450.0, 0.0,
      "Weld_IndexTurntable")
place("SM_LB_Weld_RoofMagazine_v001", -6250.0, -5500.0, 90.0, "Weld_RoofMag_E")
place("SM_LB_Weld_RoofMagazine_v001", -7850.0, -5500.0, 90.0, "Weld_RoofMag_W")

LEVEL_SUB.save_current_level()
REPORT["total"] = sum(REPORT["placed"].values())
with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_BATCH02 {}".format(json.dumps(REPORT, sort_keys=True)))
