"""Swap the WIP chain's vehicle content to the dev car.

Content-only (no C++): the 11 stamped panel assets are replaced by
panels cut from the owner's car, and the closed body-stage asset
(RoofClosures, used by primed/painted/finished phases) becomes the
8k car. Slot names bind to SignalKit instances where present.
"""
import unreal

PANEL_DIR = ("/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
             "Cairnwell2040PanelModules_v001/Meshes")
LAYER_DIR = ("/Game/LineBoss/Native/Vehicles/Cairnwell2040/"
             "VehicleWIPNativeKit_v001/Layers")
SRC_PANELS = ("C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/"
              "SourceAssets/Candidate/DevCarPanels_v001/{0}/{0}.fbx")
SRC_BODY = ("C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/"
            "SourceAssets/Candidate/DevCar_v003/"
            "SM_LB_DevCar_ConceptLOD2_v003/"
            "SM_LB_DevCar_ConceptLOD2_v003.fbx")
SK_MATS = "/Game/LineBoss/SignalKit_v001/Materials/"
ROLES = {
    "cairnwellgreen": "MI_LB_SK_Emerald_v001",
    "foundrycharcoal": "MI_LB_SK_Graphite_v001",
    "machinedsteel": "MI_LB_SK_Steel_v001",
    "warmwhite": "MI_LB_SK_StatusGlow_v001",
    "signalred": "MI_LB_SK_Red_v001",
    "tireblack": "MI_LB_SK_Tire_v001",
    "glass": "MI_LB_SK_Glass_v001",
}
PANELS = (
    "SM_LB_C2040_HOOD_PANEL_v001", "SM_LB_C2040_ROOF_PANEL_v001",
    "SM_LB_C2040_DOOR_FRONT_LEFT_v001", "SM_LB_C2040_DOOR_FRONT_RIGHT_v001",
    "SM_LB_C2040_DOOR_REAR_LEFT_v001", "SM_LB_C2040_DOOR_REAR_RIGHT_v001",
    "SM_LB_C2040_FENDER_FRONT_LEFT_v001",
    "SM_LB_C2040_FENDER_FRONT_RIGHT_v001",
    "SM_LB_C2040_QUARTER_PANEL_LEFT_v001",
    "SM_LB_C2040_QUARTER_PANEL_RIGHT_v001",
    "SM_LB_C2040_TAILGATE_PANEL_v001",
)


def import_over(filename, dest_dir, dest_name):
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
        unreal.log("SWAP_FAIL " + dest_name)
        return
    mats = list(mesh.get_editor_property("static_materials"))
    for entry in mats:
        slot = str(entry.get_editor_property("material_slot_name")).lower()
        for fragment, instance in ROLES.items():
            if fragment in slot:
                mic = unreal.EditorAssetLibrary.load_asset(
                    SK_MATS + instance)
                if mic:
                    entry.set_editor_property("material_interface", mic)
                break
    mesh.set_editor_property("static_materials", mats)
    unreal.EditorAssetLibrary.save_asset(dest_dir + "/" + dest_name)
    unreal.log("SWAPPED {} tris={}".format(dest_name,
                                           mesh.get_num_triangles(0)))


for panel in PANELS:
    import_over(SRC_PANELS.format(panel), PANEL_DIR, panel)
import_over(SRC_BODY, LAYER_DIR, "SM_LB_C2040_RoofClosures")
unreal.log("WIP_SWAP_DONE")
