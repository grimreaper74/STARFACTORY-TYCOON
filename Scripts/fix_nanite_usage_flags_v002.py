"""v002: re-parent every M_Default-based Interchange MIC in the game.

v001 found that ~56 of the 58 packaged-run Nanite warnings trace to
ONE base: the Interchange plugin's engine-owned M_Default, which
cannot be flagged in place (v001 of the ISM fix proved a save there
lands in the engine install). The project already owns a duplicate -
M_LB_InterchangeDefault_ISM_v001, same parameter names, ISM + Nanite
flags set - so every glTF-imported MIC moves onto it. Parameter
overrides survive re-parenting because the duplicate defines the
identical parameter set.
"""
import unreal

lib = unreal.MaterialEditingLibrary
ROOT = "/Game/LineBoss/Candidates/Spacecraft/"
PROJECT_BASE = ("/Game/LineBoss/Candidates/Spacecraft/ShipFactoryInterior_v001/"
    "SM_LB_IN_WallBay/Materials/M_LB_InterchangeDefault_ISM_v001")
PATHS = [
    "Gantry_v002/LB_Gantry_hoist/Materials/brushed_aluminium",
    "Gantry_v002/LB_Gantry_hoist/Materials/dark_rubber",
    "Gantry_v002/LB_Gantry_hoist/Materials/graphite_metal",
    "Gantry_v002/LB_Gantry_portal/Materials/brushed_aluminium",
    "Gantry_v002/LB_Gantry_portal/Materials/dark_rubber",
    "Gantry_v002/LB_Gantry_portal/Materials/graphite_metal",
    "Gantry_v002/LB_Gantry_portal/Materials/livery_accent",
    "Gantry_v002/LB_Gantry_portal/Materials/machined_pale",
    "Gantry_v002/LB_Gantry_rails/Materials/brushed_aluminium",
    "Gantry_v002/LB_Gantry_rails/Materials/graphite_metal",
    "Gantry_v002/LB_Gantry_trolley/Materials/brushed_aluminium",
    "Gantry_v002/LB_Gantry_trolley/Materials/graphite_metal",
    "Gantry_v002/LB_Gantry_trolley/Materials/machined_pale",
    "KitDolly_v003/LB_KitDolly_v003_joined/Materials/amber_accent",
    "KitDolly_v003/LB_KitDolly_v003_joined/Materials/brushed_aluminium",
    "KitDolly_v003/LB_KitDolly_v003_joined/Materials/graphite_steel",
    "KitDolly_v003/LB_KitDolly_v003_joined/Materials/housing_pale",
    "KitDolly_v003/LB_KitDolly_v003_joined/Materials/rubber_pad",
    "LiftCradle_v001/LB_Lift_lift_base/Materials/brushed_aluminium",
    "LiftCradle_v001/LB_Lift_lift_base/Materials/graphite_metal",
    "LiftCradle_v001/LB_Lift_lift_base/Materials/livery_accent",
    "LiftCradle_v001/LB_Lift_lift_base/Materials/machined_pale",
    "LiftCradle_v001/LB_Lift_lift_saddle/Materials/brushed_aluminium",
    "LiftCradle_v001/LB_Lift_lift_saddle/Materials/dark_rubber",
    "LiftCradle_v001/LB_Lift_lift_saddle/Materials/graphite_metal",
    "LiftCradle_v001/LB_Lift_lift_stage_1/Materials/brushed_aluminium",
    "LiftCradle_v001/LB_Lift_lift_stage_1/Materials/dark_rubber",
    "LiftCradle_v001/LB_Lift_lift_stage_1/Materials/graphite_metal",
    "LiftCradle_v001/LB_Lift_lift_stage_2/Materials/brushed_aluminium",
    "LiftCradle_v001/LB_Lift_lift_stage_2/Materials/dark_rubber",
    "LiftCradle_v001/LB_Lift_lift_stage_2/Materials/graphite_metal",
    "LiftCradle_v001/LB_Lift_lift_stage_3/Materials/brushed_aluminium",
    "LiftCradle_v001/LB_Lift_lift_stage_3/Materials/graphite_metal",
    "PaintBooth_v001/LB_Booth_paint_booth/Materials/booth_glazing",
    "PaintBooth_v001/LB_Booth_paint_booth/Materials/brushed_aluminium",
    "PaintBooth_v001/LB_Booth_paint_booth/Materials/dark_rubber",
    "PaintBooth_v001/LB_Booth_paint_booth/Materials/graphite_metal",
    "PaintBooth_v001/LB_Booth_paint_booth/Materials/livery_accent",
    "PaintBooth_v001/LB_Booth_paint_booth/Materials/machined_pale",
    "ShipFactoryInterior_v001/SM_LB_IN_BayLight/Materials/brushed_aluminium",
    "ShipFactoryInterior_v001/SM_LB_IN_BayLight/Materials/graphite_metal",
    "ShipFactoryInterior_v001/SM_LB_IN_BayLight/Materials/lamp_emissive",
    "ShipFactoryInterior_v001/SM_LB_IN_RoofTruss/Materials/graphite_metal",
    "ShipFactoryInterior_v001/SM_LB_IN_WallBay/Materials/brushed_aluminium",
    "ShipFactoryInterior_v001/SM_LB_IN_WallBay/Materials/graphite_metal",
    "ShipFactoryInterior_v001/SM_LB_IN_WallBay/Materials/machined_pale",
    "SpacecraftFactory_v001/Meshes/Scout01_v003/scout01_v003/Materials/brushed_aluminium",
    "SpacecraftFactory_v001/Meshes/Scout01_v003/scout01_v003/Materials/canopy_glass",
    "SpacecraftFactory_v001/Meshes/Scout01_v003/scout01_v003/Materials/engine_hot",
    "SpacecraftFactory_v001/Meshes/Scout01_v003/scout01_v003/Materials/graphite_metal",
    "SpacecraftFactory_v001/Meshes/Scout01_v003/scout01_v003/Materials/livery_accent",
    "SpacecraftFactory_v001/Meshes/Scout01_v003/scout01_v003/Materials/machined_pale",
    "TrackSet_v002/LB_Track_track_end_cap/Materials/brushed_aluminium",
    "TrackSet_v002/LB_Track_track_end_cap/Materials/graphite_metal",
    "TrackSet_v002/LB_Track_track_end_cap/Materials/livery_accent",
    "TrackSet_v002/LB_Track_track_end_cap/Materials/machined_pale",
]

base = unreal.load_asset(PROJECT_BASE)
assert base is not None, "project base missing"
reparented = 0
left = 0
for rel in PATHS:
    path = ROOT + rel
    mi = unreal.load_asset(path)
    if mi is None or not isinstance(mi, unreal.MaterialInstanceConstant):
        unreal.log_warning("NANITEFIX2 not a MIC, untouched: " + path)
        left += 1
        continue
    old = mi.get_base_material()
    if old is None or "/InterchangeAssets/" not in old.get_path_name():
        left += 1
        continue
    lib.set_material_instance_parent(mi, base)
    lib.update_material_instance(mi)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mi), path
    reparented += 1
unreal.log("NANITEFIX2 DONE reparented=%d untouched=%d" % (reparented, left))
