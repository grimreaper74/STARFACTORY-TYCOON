"""Report what materials/textures the imported buildings actually carry.

The first sighted screenshot showed the white futuristic buildings
rendering DARK. Before fixing anything: what did the FBX import actually
produce? Guessing at material problems is how the decal-domain
mis-diagnosis happened; this looks instead.
"""
import unreal

ROOT = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Meshes"
NAMES = ["SM_LB_ST_PowerPlant_v002", "SM_LB_ST_SubAssemblyHall_v003",
         "SM_LB_ST_AssemblyStation_v001", "SM_LB_ST_Smelter"]

library = unreal.EditorAssetLibrary
for name in NAMES:
    path = "%s/%s" % (ROOT, name)
    mesh = library.load_asset(path)
    if mesh is None:
        print("MISSING %s" % path)
        continue
    print("== %s" % name)
    for index, static_material in enumerate(
            mesh.get_editor_property("static_materials")):
        material = static_material.get_editor_property("material_interface")
        print("  slot %d: %s" % (index,
              material.get_path_name() if material else "None"))
        if material is None:
            continue
        base = material.get_base_material() if hasattr(
            material, "get_base_material") else None
        # List texture parameters / referenced textures.
        try:
            textures = material.get_used_textures()
        except Exception:
            textures = []
        for tex in textures:
            print("    tex: %s  %sx%s" % (tex.get_name(),
                  tex.blueprint_get_size_x() if hasattr(
                      tex, "blueprint_get_size_x") else "?",
                  tex.blueprint_get_size_y() if hasattr(
                      tex, "blueprint_get_size_y") else "?"))
        # Scalar/vector params on instances tell us metallic defaults.
        if isinstance(material, unreal.MaterialInstance):
            for sp in material.scalar_parameter_values:
                print("    scalar %s = %s" % (
                    sp.parameter_info.name, sp.parameter_value))
            for vp in material.vector_parameter_values:
                print("    vector %s = %s" % (
                    vp.parameter_info.name, vp.parameter_value))
        elif isinstance(material, unreal.Material):
            print("    (plain Material) metallic/roughness inputs "
                  "connected: base_color=%s" % "?")
# Also: what textures landed in the folder at all?
print("== textures in the mesh folder")
for asset in library.list_assets(ROOT, recursive=False):
    if "Texture" in str(library.find_asset_data(asset).asset_class_path):
        print("  %s" % asset)
