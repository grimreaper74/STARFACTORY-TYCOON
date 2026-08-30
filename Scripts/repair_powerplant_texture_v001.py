"""repair_powerplant_texture_v001.py - the power plant rendered as
glossy black-and-orange mottle in Unreal while being a pale grey
fusion plant in Blender (owner 2026-08-26 night: "its ok in blender").

Root cause, proven by comparing every station: the plant's FBX
embedded texture folder (FBX/SM_LB_ST_PowerPlant_LOD0.fbm) holds a
DIFFERENT, much darker base_color.jpg (12.6 MB, mean RGB 72/68/64)
than the verified source in TexturesByModel/PowerPlant
(2.1 MB, mean RGB 131/131/130). The station import lane took the
embedded copy, so the engine has been sampling the wrong image. Every
other station's embedded copy matches its source exactly - this is a
one-off, not a lane-wide fault.

This lane re-imports the plant's BaseColor and Normal from the
verified TexturesByModel source, restores the colour-space flags, and
leaves the MI bindings untouched (they already point at the right
texture assets). Fails closed if a source file is missing."""

import os
import unreal

SRC = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Candidate\Spacecraft\StationModels_MeshyIntake_v001"
       r"\TexturesByModel\PowerPlant")
TEX_DIR = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
           "/Textures")

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

JOBS = [
    ("base_color.jpg", "T_LB_PowerPlant_BaseColor", True, None),
    ("normal.jpg", "T_LB_PowerPlant_Normal", False,
     unreal.TextureCompressionSettings.TC_NORMALMAP),
]

for fname, asset_name, srgb, compression in JOBS:
    path = os.path.join(SRC, fname)
    if not os.path.isfile(path):
        raise RuntimeError("FAIL CLOSED: missing " + path)
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": path, "destination_path": TEX_DIR,
        "destination_name": asset_name, "automated": True,
        "replace_existing": True, "replace_existing_settings": True,
        "save": True})
    tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    tex = unreal.load_asset("%s/%s" % (TEX_DIR, asset_name))
    if tex is None:
        raise RuntimeError("FAIL CLOSED: %s failed to import" % asset_name)
    tex.set_editor_property("srgb", srgb)
    tex.set_editor_property("never_stream", True)
    if compression is not None:
        tex.set_editor_property("compression_settings", compression)
        tex.set_editor_property("flip_green_channel", True)
    lib.save_asset("%s/%s" % (TEX_DIR, asset_name))
    unreal.log("PLANTFIX re-imported %s (%dx%d srgb=%s) from source"
               % (asset_name, tex.blueprint_get_size_x(),
                  tex.blueprint_get_size_y(), srgb))
unreal.log("PLANTFIX DONE")
