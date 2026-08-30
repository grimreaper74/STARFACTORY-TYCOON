"""Import the site hub scene as a UI texture.

Runs inside the editor. The hub is ONE painted picture the player
clicks (owner 2026-08-29: "I thought it would just be a picture that
you could click on"), so this is a UI texture, not a world material:
no mip streaming games, no compression that eats the fine road
markings, and clamped so it never wraps at the edges.
"""
import unreal

SRC = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Spacecraft\SiteHubScene_v006\site_hub_scene_v006.png")
DEST = "/Game/LineBoss/UI/SiteHub"
NAME = "T_LB_SiteHub_v006"

if not unreal.Paths.file_exists(SRC):
    unreal.log_error("SITEHUB: source missing %s" % SRC)
else:
    task = unreal.AssetImportTask()
    task.filename = SRC
    task.destination_path = DEST
    task.destination_name = NAME
    task.automated = True
    task.replace_existing = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    tex = unreal.EditorAssetLibrary.load_asset("%s/%s.%s" % (DEST, NAME, NAME))
    if tex is None:
        unreal.log_error("SITEHUB: import produced no texture")
    else:
        # UI group: no aggressive compression on a picture whose road
        # markings and hazard striping are one pixel wide in places.
        tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property("compression_settings",
                                unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        tex.set_editor_property("srgb", True)
        unreal.EditorAssetLibrary.save_loaded_asset(tex)
        unreal.log("SITEHUB OK %s  %dx%d" % (NAME, tex.blueprint_get_size_x(),
                                             tex.blueprint_get_size_y()))
