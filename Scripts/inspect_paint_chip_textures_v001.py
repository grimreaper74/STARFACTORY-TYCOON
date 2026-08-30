"""What are the Metal Paint Chips textures actually set to?

The new surface master fails to compile, which is the same class of
fault as this morning's: a sampler type that does not match the
texture's compression. Read the settings rather than guess them.
"""
import unreal
SRC = "/Game/Surface_Forge/Textures/Metal_Paint_Chips"
library = unreal.EditorAssetLibrary
for name in ("T_Base_Color_Metal_Paint_Chips", "T_Normal_Metal_Paint_Chips",
             "T_ORD_Metal_Paint_Chips"):
    tex = library.load_asset("%s/%s" % (SRC, name))
    if tex is None:
        print("TEXPROBE MISSING %s" % name)
        continue
    print("TEXPROBE %s compression=%s srgb=%s size=%sx%s"
          % (name,
             tex.get_editor_property("compression_settings"),
             tex.get_editor_property("srgb"),
             tex.blueprint_get_size_x(), tex.blueprint_get_size_y()))
