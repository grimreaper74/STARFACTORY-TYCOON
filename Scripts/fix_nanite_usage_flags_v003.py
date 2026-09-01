"""v003: re-parent EVERY Interchange M_Default MIC, project-wide.

v002 fixed the 53 MICs the second packaged run named - then the third
run cooked PalletLoads_v001/DroneBatch_v001 for the first time (they
were missing from DirectoriesToAlwaysCook) and surfaced a fresh batch
of the same defect. Enumerating by asset registry ends the per-batch
whack-a-mole: every MaterialInstanceConstant under the spacecraft
content roots whose base material lives in /InterchangeAssets/ moves
onto the project-owned duplicate (identical parameter set, ISM+Nanite
flags baked). Re-run this lane after any new glTF import.
"""
import unreal

lib = unreal.MaterialEditingLibrary
PROJECT_BASE = ("/Game/LineBoss/Candidates/Spacecraft/ShipFactoryInterior_v001/"
    "SM_LB_IN_WallBay/Materials/M_LB_InterchangeDefault_ISM_v001")
ROOTS = ["/Game/LineBoss/Candidates/Spacecraft", "/Game/Spacecraft"]

base = unreal.load_asset(PROJECT_BASE)
assert base is not None, "project base missing"
ar = unreal.AssetRegistryHelpers.get_asset_registry()
reparented = 0
scanned = 0
for root in ROOTS:
    for a in ar.get_assets_by_path(root, recursive=True):
        if str(a.asset_class_path.asset_name) != "MaterialInstanceConstant":
            continue
        scanned += 1
        path = str(a.package_name) + "." + str(a.asset_name)
        mi = unreal.load_asset(path)
        if mi is None:
            unreal.log_warning("NANITEFIX3 load failed: " + path)
            continue
        old = mi.get_base_material()
        if old is None or "/InterchangeAssets/" not in old.get_path_name():
            continue
        lib.set_material_instance_parent(mi, base)
        lib.update_material_instance(mi)
        assert unreal.EditorAssetLibrary.save_loaded_asset(mi), path
        reparented += 1
        unreal.log("NANITEFIX3 reparented: " + path)
unreal.log("NANITEFIX3 DONE scanned=%d reparented=%d" % (scanned, reparented))
