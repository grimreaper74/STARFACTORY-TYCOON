"""Import the scan beam and place a sweeping laser at inspection points.

Owner, 2026-08-21: inspection should have "a laser that moves like a
car wash". One ALBOneFactoryScanBeamActor per EOL inspection arch,
vision gate and quality light tunnel, aligned to the machine so the
beam sweeps along the line through the station. Re-runnable: clears
its own Scan_ actors first.
"""
import json
import os

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
SRC = ("C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/"
       "SourceAssets/Candidate/ScanKit_v001/SM_LB_Inspect_ScanBeam_v001/"
       "SM_LB_Inspect_ScanBeam_v001.fbx")
MESH_DIR = "/Game/LineBoss/ScanKit_v001/Meshes"
MESH_PATH = MESH_DIR + "/SM_LB_Inspect_ScanBeam_v001"
SK_MATS = "/Game/LineBoss/SignalKit_v001/Materials/"
OUT = "C:/Temp/lb_place_scanners.json"

HOSTS = ("EOLInspectionArch", "VisionGate", "QualityLightTunnel")

ROLES = {
    "warmwhite": "MI_LB_SK_StatusGlow_v001",
    "charcoal": "MI_LB_SK_Graphite_v001",
    "steel": "MI_LB_SK_Steel_v001",
    "red": "MI_LB_SK_Red_v001",
}

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

if not unreal.EditorAssetLibrary.does_asset_exist(MESH_PATH):
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_as_skeletal", False)
    options.static_mesh_import_data.set_editor_property(
        "combine_meshes", True)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", SRC)
    task.set_editor_property("destination_path", MESH_DIR)
    task.set_editor_property("destination_name",
                             "SM_LB_Inspect_ScanBeam_v001")
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
if not mesh:
    raise RuntimeError("scan beam mesh failed to import")

materials = list(mesh.get_editor_property("static_materials"))
for entry in materials:
    slot = str(entry.get_editor_property("material_slot_name")).lower()
    for fragment, instance_name in ROLES.items():
        if fragment in slot:
            mic = unreal.EditorAssetLibrary.load_asset(
                SK_MATS + instance_name)
            if mic:
                entry.set_editor_property("material_interface", mic)
            break
mesh.set_editor_property("static_materials", materials)
unreal.EditorAssetLibrary.save_asset(MESH_PATH)

scan_class = unreal.load_class(None,
    "/Script/LineBossCarFactory.LBOneFactoryScanBeamActor")

report = {"cleared": 0, "placed": [], "hosts": {}}
for actor in list(ACTOR_SUB.get_all_level_actors()):
    if actor.get_actor_label().startswith("Scan_"):
        ACTOR_SUB.destroy_actor(actor)
        report["cleared"] += 1

index = 0
for actor in list(ACTOR_SUB.get_all_level_actors()):
    mesh_name = ""
    for component in actor.get_components_by_class(
            unreal.StaticMeshComponent):
        found = component.get_editor_property("static_mesh")
        if found:
            mesh_name = found.get_name()
            break
    host = next((h for h in HOSTS if h in mesh_name), None)
    if not host:
        continue
    where = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    scanner = ACTOR_SUB.spawn_actor_from_class(
        scan_class, where, rot)
    if not scanner:
        continue
    index += 1
    scanner.set_actor_label("Scan_{:03d}".format(index))
    beam = scanner.get_editor_property("beam_mesh")
    beam.set_static_mesh(mesh)
    report["hosts"][host] = report["hosts"].get(host, 0) + 1
    report["placed"].append([scanner.get_actor_label(), host,
                             round(where.x), round(where.y)])

if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")
with open(OUT, "w") as handle:
    json.dump(report, handle, indent=1)
unreal.log("LINE_BOSS_SCANNERS placed={} hosts={}".format(
    index, report["hosts"]))
