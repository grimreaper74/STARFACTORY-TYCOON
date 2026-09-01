"""Set used_with_nanite on every material the packaged run refused.

The second packaged journey's log carried 58 unique "missing usage
flag Nanite! Default Material will be used in game" warnings - the
Scout's six part materials, the whole gantry crane, the paint booth,
the kit dolly, the lift cradle, the interior wall bays, the track end
caps. The editor sets usage flags on demand and saves them lazily, so
none of this is visible outside a cooked build. Deduped by base
material (Interchange shares bases across meshes in one import).
"""
import unreal

lib = unreal.MaterialEditingLibrary
ROOT = "/Game/LineBoss/Candidates/Spacecraft/"
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
    "StationMeshes_v001/Materials/M_LB_ShipPaint_v001",
    "TrackSet_v002/LB_Track_track_end_cap/Materials/brushed_aluminium",
    "TrackSet_v002/LB_Track_track_end_cap/Materials/graphite_metal",
    "TrackSet_v002/LB_Track_track_end_cap/Materials/livery_accent",
    "TrackSet_v002/LB_Track_track_end_cap/Materials/machined_pale",
]

seen = set()
fixed = 0
missing = 0
for rel in PATHS:
    path = ROOT + rel
    m = unreal.load_asset(path)
    if m is None:
        unreal.log_warning("NANITEFIX MISSING: " + path)
        missing += 1
        continue
    base = m.get_base_material() if isinstance(
        m, unreal.MaterialInterface) else m
    if base is None:
        unreal.log_warning("NANITEFIX NO BASE: " + path)
        missing += 1
        continue
    bpath = base.get_path_name()
    if bpath in seen:
        continue
    seen.add(bpath)
    if bpath.startswith("/InterchangeAssets/") or bpath.startswith("/Engine/"):
        unreal.log_warning(
            "NANITEFIX SKIP ENGINE-OWNED BASE (needs reparent): " + bpath)
        continue
    base.set_editor_property("used_with_nanite", True)
    lib.recompile_material(base)
    assert unreal.EditorAssetLibrary.save_loaded_asset(base), bpath
    fixed += 1
    unreal.log("NANITEFIX set: " + bpath)
unreal.log("NANITEFIX DONE fixed=%d missing=%d unique_bases=%d"
    % (fixed, missing, len(seen)))
