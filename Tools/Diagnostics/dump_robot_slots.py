"""Dump slots + bounds for the robot family and shared base."""
import unreal

registry = unreal.AssetRegistryHelpers.get_asset_registry()
WANT = ("SM_LB_BodyShopRobotNative_", "SM_LB_WeldRobot_SharedBase")
for data in registry.get_assets_by_class(
        unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh"), True):
    name = str(data.asset_name)
    if not any(name.startswith(w) for w in WANT):
        continue
    mesh = unreal.EditorAssetLibrary.load_asset(str(data.package_name))
    if not mesh:
        continue
    box = mesh.get_bounding_box()
    size = box.max - box.min
    slots = []
    for entry in mesh.get_editor_property("static_materials"):
        slot = str(entry.get_editor_property("material_slot_name"))
        mat = entry.get_editor_property("material_interface")
        slots.append(slot + ":" + (mat.get_name() if mat else "NONE"))
    unreal.log("ROBOTDUMP {} size={:.0f}x{:.0f}x{:.0f} slots={}".format(
        name, size.x, size.y, size.z, ";".join(slots)))
