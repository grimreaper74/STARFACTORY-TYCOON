"""Restore the original WIP chain meshes; the dev car stays isolated.

Owner, 2026-08-22: put the project back how it was; keep the new
meshes in their own folder. Re-imports the 11 original panel modules
and the RoofClosures layer from their documented sources, rebinds the
VehiclePanelSurface slot to the original player-paint material, and
removes the two placed DevCar actors. The dev car and parts remain
untouched under /Game/LineBoss/Candidates/Vehicles/DevCar_v003.
"""
import unreal

PANEL_DIR = ("/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
             "Cairnwell2040PanelModules_v001/Meshes")
LAYER_DIR = ("/Game/LineBoss/Native/Vehicles/Cairnwell2040/"
             "VehicleWIPNativeKit_v001/Layers")
SRC_ROOT = ("C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/"
            "SourceAssets/Candidate/Vehicles/Cairnwell2040/")
PAINT = ("/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
         "Cairnwell2040Runtime_v001/Materials/"
         "M_LB_C2040_BodyPaintTintPBR_v001")

PANELS = ("HOOD_PANEL", "ROOF_PANEL", "DOOR_FRONT_LEFT",
          "DOOR_FRONT_RIGHT", "DOOR_REAR_LEFT", "DOOR_REAR_RIGHT",
          "FENDER_FRONT_LEFT", "FENDER_FRONT_RIGHT",
          "QUARTER_PANEL_LEFT", "QUARTER_PANEL_RIGHT", "TAILGATE_PANEL")

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(
        "/Game/LineBoss/Factory/OneFactory/v001/Maps/"
        "LB_MoorcrossWorks_OneFactory_v001"):
    raise RuntimeError("could not load target map")

paint = unreal.EditorAssetLibrary.load_asset(PAINT)


def restore(filename, dest_dir, dest_name):
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_as_skeletal", False)
    options.static_mesh_import_data.set_editor_property(
        "combine_meshes", True)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", filename)
    task.set_editor_property("destination_path", dest_dir)
    task.set_editor_property("destination_name", dest_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", False)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.EditorAssetLibrary.load_asset(dest_dir + "/" + dest_name)
    if not mesh:
        unreal.log("RESTORE_FAIL " + dest_name)
        return
    mats = list(mesh.get_editor_property("static_materials"))
    for entry in mats:
        if paint:
            entry.set_editor_property("material_interface", paint)
    mesh.set_editor_property("static_materials", mats)
    unreal.EditorAssetLibrary.save_asset(dest_dir + "/" + dest_name)
    unreal.log("RESTORED {} tris={}".format(dest_name,
                                            mesh.get_num_triangles(0)))


for name in PANELS:
    restore(SRC_ROOT + "Cairnwell2040PanelModules_v001/Exports/{0}/LOD0/"
            "SM_LB_C2040_{0}_v001_LOD0.fbx".format(name),
            PANEL_DIR, "SM_LB_C2040_{}_v001".format(name))
restore(SRC_ROOT + "VehicleWIPNativeKit_v001/Exports/Layers/LOD0/"
        "SM_LB_C2040_RoofClosures_LOD0.fbx",
        LAYER_DIR, "SM_LB_C2040_RoofClosures")

removed = 0
for actor in list(ACTOR_SUB.get_all_level_actors()):
    if actor.get_actor_label().startswith("DevCar_"):
        ACTOR_SUB.destroy_actor(actor)
        removed += 1
if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")
unreal.log("RESTORE_DONE removed_actors={}".format(removed))
