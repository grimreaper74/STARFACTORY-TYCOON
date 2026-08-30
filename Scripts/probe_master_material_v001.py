"""probe_master_material_v001.py - read-only diagnosis: why does
BaseColorBoost not move a single rendered pixel? Dumps the master's
expression graph, the MP_BASE_COLOR binding, one MI's parent and
overrides, and one mesh's slot materials."""

import unreal

MAT = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
       "/Materials/M_LB_MeshyPBR_v002")
MI = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
      "/Materials/MI_LB_RollingMill")
SM = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
      "/Meshes/SM_LB_ST_RollingMill_LOD0")

mel = unreal.MaterialEditingLibrary
m = unreal.load_asset(MAT)
unreal.log("=== EXPRESSIONS ===")
for e in mel.get_material_expressions(m):
    d = type(e).__name__
    try:
        d += " param=" + str(e.get_editor_property("parameter_name"))
    except Exception:
        pass
    try:
        d += " default=" + str(e.get_editor_property("default_value"))
    except Exception:
        pass
    unreal.log("EXPR " + d)
unreal.log("=== BASECOLOR INPUT ===")
try:
    node = mel.get_material_property_input_node(
        m, unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.log("BASECOLOR fed by: " + (type(node).__name__
        if node else "NOTHING"))
    if node:
        for inp in ("a", "b"):
            try:
                src = mel.get_material_expression_input_node(node, inp)
                unreal.log("  input %s <- %s" % (inp,
                    type(src).__name__ if src else "none"))
            except Exception as ex:
                unreal.log("  input %s: %s" % (inp, ex))
except Exception as ex:
    unreal.log("probe error: %s" % ex)
unreal.log("=== MI ===")
mi = unreal.load_asset(MI)
unreal.log("parent=" + str(mi.get_editor_property("parent")))
unreal.log("boost=" + str(
    mel.get_material_instance_scalar_parameter_value(mi, "BaseColorBoost")))
for sp in mi.get_editor_property("scalar_parameter_values"):
    unreal.log("override scalar: %s = %s" % (
        sp.get_editor_property("parameter_info").get_editor_property("name"),
        sp.get_editor_property("parameter_value")))
unreal.log("=== MESH SLOTS ===")
sm = unreal.load_asset(SM)
for s in sm.get_editor_property("static_materials"):
    unreal.log("slot %s -> %s" % (
        s.get_editor_property("material_slot_name"),
        s.get_editor_property("material_interface")))
unreal.log("PROBE DONE")
