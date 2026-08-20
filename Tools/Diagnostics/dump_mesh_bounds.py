"""Print current bounds for the placement-QA offender meshes."""
import unreal

NAMES = [
    "/Game/LineBoss/Candidates/SiteKit_v001/Transporter/SM_LB_Site_Transporter_v001_Trailer",
    "/Game/LineBoss/Candidates/SiteKit_v001/Transporter/SM_LB_Site_Transporter_v001_Tractor",
]
registry = unreal.AssetRegistryHelpers.get_asset_registry()
for prefix, keys in (
    ("", []),
):
    pass
found = {}
for data in registry.get_assets_by_class(
        unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh"), True):
    name = str(data.asset_name)
    if name in ("SM_LB_Assembly_SkilletCarrier_v001",
                "SM_LB_Conveyor_SkilletDeckPlate_v001",
                "SM_LB_BodyShopSupport_EmptyReturnCart_v002",
                "SM_LB_Weld_ClosureDoorFixture_v001",
                "SM_LB_BodyShopRobotNative_J2_v001",
                "SM_LB_Site_Transporter_v001_Trailer",
                "SM_LB_Site_Transporter_v001_Tractor",
                "SM_LB_Assembly_OverheadTrackSegment_v001",
                "SM_LB_Site_Tree_v001_B",
                "SM_LB_Paint_PFTrackSegment_v001",
                "SM_LB_Paint_EDDipTank_v001"):
        found[name] = str(data.package_name)

for name, pkg in sorted(found.items()):
    mesh = unreal.EditorAssetLibrary.load_asset(pkg)
    if not mesh:
        unreal.log("BOUNDS {} LOAD_FAIL".format(name))
        continue
    box = mesh.get_bounding_box()
    size = box.max - box.min
    unreal.log("BOUNDS {} size={:.0f}x{:.0f}x{:.0f} min_z={:.0f}".format(
        name, size.x, size.y, size.z, box.min.z))
