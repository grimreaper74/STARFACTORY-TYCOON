"""build_station_materials_v009.py - drone boost trim. With the master
finally compiling (v008), the measured v006 boosts render for the
first time - and the capture shows the four drones OVER-brightened
(sun-lit panels at sRGB ~232, brighter than the 220 floor; machinery
should sit below the floor). Stations look right; only the drones
trim, from target 0.22 to ~0.13 linear."""

import unreal

MAT_DIR = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials"
TRIMS = {
    "DroneAssembly": 2.10,
    "DroneCargoLift": 2.20,
    "DroneSpray": 2.40,
    "DroneWinch": 2.25,
}
mel = unreal.MaterialEditingLibrary
lib = unreal.EditorAssetLibrary
for key, val in TRIMS.items():
    path = "%s/MI_LB_%s" % (MAT_DIR, key)
    mi = unreal.load_asset(path)
    if mi is None:
        raise RuntimeError("FAIL CLOSED: %s missing" % path)
    mel.set_material_instance_scalar_parameter_value(
        mi, "BaseColorBoost", val)
    mel.update_material_instance(mi)
    lib.save_asset(path)
    unreal.log("TRIM %s = %.2f" % (key, val))
unreal.log("V009 DONE: drones below the floor again")
