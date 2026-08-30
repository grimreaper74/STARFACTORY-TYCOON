"""Print every building instance's texture + scalar params - which map
is actually bound where. The hall renders charcoal while the dock
renders white through the same master; the difference must be in the
instance data, so read it instead of theorising."""
import unreal
TEX_ROOT = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/"
            "Meshes/BuildingTextures")
library = unreal.EditorAssetLibrary
mat_lib = unreal.MaterialEditingLibrary
for asset in library.list_assets(TEX_ROOT, recursive=False):
    name = asset.split("/")[-1].split(".")[0]
    if not name.startswith("MI_"):
        continue
    mi = library.load_asset("%s/%s" % (TEX_ROOT, name))
    print("== %s" % name)
    for pname in ("BaseColor", "MetallicRoughness", "Normal"):
        tex = mat_lib.get_material_instance_texture_parameter_value(mi, pname)
        print("   %-18s -> %s" % (pname, tex.get_name() if tex else "NONE"))
    print("   MetallicScale = %s"
          % mat_lib.get_material_instance_scalar_parameter_value(
              mi, "MetallicScale"))
