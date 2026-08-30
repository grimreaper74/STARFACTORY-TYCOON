"""inspect_station_mis_v001.py - READ-ONLY: which texture is bound to
each station material instance's BaseColor / MetallicRoughness /
Normal parameter, and what mesh slots actually use. Diagnoses the
'MR map rendered as colour' symptom (owner 2026-08-26 night: the
power plant reads orange camo in Unreal but is fine in Blender)."""
import unreal

MAT_DIR = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials"
MESH_DIR = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Meshes"
lib = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary

for asset_path in sorted(lib.list_assets(MAT_DIR, recursive=False)):
    name = asset_path.split("/")[-1].split(".")[0]
    if not name.startswith("MI_"):
        continue
    mi = unreal.load_asset(asset_path)
    if not isinstance(mi, unreal.MaterialInstanceConstant):
        continue
    bits = []
    for param in ("BaseColor", "MetallicRoughness", "Normal"):
        tex = mel.get_material_instance_texture_parameter_value(mi, param)
        bits.append("%s=%s" % (param, tex.get_name() if tex else "NONE"))
    boost = mel.get_material_instance_scalar_parameter_value(
        mi, "BaseColorBoost")
    unreal.log("MICHK %-28s %s boost=%.2f" % (name, " ".join(bits), boost))

# What does the power plant mesh actually wear?
for mesh_name in ("SM_LB_ST_PowerPlant_LOD0", "SM_LB_ST_PowerStation_LOD0"):
    mesh = unreal.load_asset("%s/%s" % (MESH_DIR, mesh_name))
    if mesh is None:
        unreal.log("MICHK mesh %s MISSING" % mesh_name)
        continue
    slots = mesh.get_editor_property("static_materials")
    for i, slot in enumerate(slots):
        mat = slot.get_editor_property("material_interface")
        unreal.log("MICHK mesh %s slot%d -> %s" % (
            mesh_name, i, mat.get_name() if mat else "NONE"))
unreal.log("MICHK DONE")
