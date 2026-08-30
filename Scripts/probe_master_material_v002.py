"""Dump both master materials' expression graphs - class, parameter
name, texture default, sampler type. Read-only. The masters fail to
compile ('Default Material will be used in game'); this names why."""
import unreal
mel = unreal.MaterialEditingLibrary
lib = unreal.EditorAssetLibrary
MASTERS = [
    ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Meshes/"
     "BuildingTextures/M_LB_Building_Master"),
    ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/"
     "M_LB_MeshyPBR_v002"),
]
for path in MASTERS:
    mat = lib.load_asset(path)
    if mat is None:
        print("PROBE MISSING %s" % path)
        continue
    print("PROBE == %s" % path)
    for expr in mel.get_material_expressions(mat):
        cls = expr.get_class().get_name()
        detail = ""
        try:
            detail += " param=%s" % expr.get_editor_property("parameter_name")
        except Exception:
            pass
        try:
            tex = expr.get_editor_property("texture")
            detail += " texture=%s" % (tex.get_path_name() if tex else "NONE")
        except Exception:
            pass
        try:
            detail += " sampler=%s" % expr.get_editor_property("sampler_type")
        except Exception:
            pass
        print("PROBE   %s%s" % (cls, detail))
