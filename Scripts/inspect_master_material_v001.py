"""inspect_master_material_v001.py - READ-ONLY dump of the Meshy PBR
master's graph: which texture-sample channel feeds Metallic and
Roughness (diagnosing the glossy black/orange 'mirror' look on the
power plant, owner 2026-08-26 night: it is fine in Blender)."""
import unreal

MASTER = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
          "/Materials/M_LB_MeshyPBR_v003")
mat = unreal.load_asset(MASTER)
if mat is None:
    unreal.log("MASTERCHK MISSING")
else:
    props = [
        ("BaseColor", unreal.MaterialProperty.MP_BASE_COLOR),
        ("Metallic", unreal.MaterialProperty.MP_METALLIC),
        ("Roughness", unreal.MaterialProperty.MP_ROUGHNESS),
        ("Normal", unreal.MaterialProperty.MP_NORMAL),
        ("Emissive", unreal.MaterialProperty.MP_EMISSIVE_COLOR),
    ]
    for label, prop in props:
        try:
            connected = unreal.MaterialEditingLibrary \
                .get_material_property_input_node(mat, prop)
        except Exception as exc:
            connected = "ERR %s" % exc
        name = "NONE"
        extra = ""
        if isinstance(connected, unreal.MaterialExpression):
            name = connected.get_class().get_name()
            if isinstance(connected, unreal.MaterialExpressionTextureSample):
                tex = connected.get_editor_property("texture")
                extra = " tex=%s" % (tex.get_name() if tex else "None")
            if isinstance(connected,
                          unreal.MaterialExpressionTextureSampleParameter2D):
                extra += " param=%s" % connected.get_editor_property(
                    "parameter_name")
        unreal.log("MASTERCHK %-10s <- %s%s" % (label, name, extra))
    exprs = unreal.MaterialEditingLibrary.get_used_texture_samples(mat) \
        if hasattr(unreal.MaterialEditingLibrary,
                   "get_used_texture_samples") else []
    unreal.log("MASTERCHK expression count=%d" % len(exprs))
unreal.log("MASTERCHK DONE")
