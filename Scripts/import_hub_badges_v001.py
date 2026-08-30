"""Import the hub state badges as UI textures."""
import unreal

SRC = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
       r"\SourceAssets\Spacecraft\HubBadges_v001")
DEST = "/Game/LineBoss/UI/SiteHub"
NAMES = ["T_LB_Icon_HubLocked_v001", "T_LB_Icon_HubBuild_v001"]

tools = unreal.AssetToolsHelpers.get_asset_tools()
problems = []
for name in NAMES:
    path = "%s\%s.png" % (SRC, name)
    if not unreal.Paths.file_exists(path):
        problems.append("source missing %s" % path)
        continue
    task = unreal.AssetImportTask()
    task.filename = path
    task.destination_path = DEST
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True
    tools.import_asset_tasks([task])
    tex = unreal.EditorAssetLibrary.load_asset(
        "%s/%s.%s" % (DEST, name, name))
    if tex is None:
        problems.append("%s did not import" % name)
        continue
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property(
        "compression_settings",
        unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("srgb", True)
    unreal.EditorAssetLibrary.save_loaded_asset(tex)
    unreal.log("HUBBADGE OK %s %dx%d" % (name, tex.blueprint_get_size_x(),
                                         tex.blueprint_get_size_y()))
if problems:
    for p in problems:
        unreal.log_error("HUBBADGE PROBLEM: %s" % p)
