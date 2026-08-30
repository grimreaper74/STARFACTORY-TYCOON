"""inspect_decal_textures_v001.py - READ-ONLY. Which textures do the
two floor-paint material instances bind? A real decal-domain material
has to sample the same images, so list every texture parameter (and the
parent's own texture samplers) for both."""

import unreal

PATHS = [
    "/Game/Materials/MI_DangerLine_01",
    "/Game/Materials/MI_Decal_FloorTraces1",
]

lib = unreal.MaterialEditingLibrary

for path in PATHS:
    mi = unreal.load_asset(path)
    unreal.log("DECALTEX ==== %s" % path)
    parent = mi.get_editor_property("parent")
    names = lib.get_texture_parameter_names(parent)
    for n in names:
        try:
            tex = lib.get_material_instance_texture_parameter_value(mi, n)
        except Exception:
            tex = None
        unreal.log("DECALTEX   param %s = %s"
                   % (n, tex.get_path_name() if tex else "<parent default>"))
    for n in lib.get_scalar_parameter_names(parent):
        unreal.log("DECALTEX   scalar %s = %s"
                   % (n, lib.get_material_instance_scalar_parameter_value(
                       mi, n)))
    for n in lib.get_vector_parameter_names(parent):
        unreal.log("DECALTEX   vector %s = %s"
                   % (n, lib.get_material_instance_vector_parameter_value(
                       mi, n)))
    # Parent's hard-wired samplers (params may be empty entirely).
    for expr in unreal.MaterialEditingLibrary.get_used_textures(parent):
        unreal.log("DECALTEX   used %s" % expr.get_path_name())
unreal.log("DECALTEX DONE")
