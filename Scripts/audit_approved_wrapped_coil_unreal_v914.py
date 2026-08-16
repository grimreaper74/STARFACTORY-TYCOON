"""Read-only bounds/material audit for the repaired wrapped coil after Unreal import."""
import unreal

path = "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/SM_CA_MW_WrappedCoil_Repaired_v003"
mesh = unreal.EditorAssetLibrary.load_asset(path)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Approved wrapped coil missing")
box = mesh.get_bounding_box()
materials = []
for slot in mesh.get_editor_property("static_materials"):
    interface = slot.get_editor_property("material_interface")
    materials.append(interface.get_path_name() if interface else None)
unreal.log(
    "LB_WRAPPED_COIL_UNREAL_AUDIT_V914="
    f"min=({box.min.x:.3f},{box.min.y:.3f},{box.min.z:.3f}) "
    f"max=({box.max.x:.3f},{box.max.y:.3f},{box.max.z:.3f}) "
    f"materials={materials}"
)
