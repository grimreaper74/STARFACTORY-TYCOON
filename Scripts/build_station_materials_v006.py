"""build_station_materials_v006.py - measured per-instance albedo
normalization (supersedes the v005 master-default bump, which the
capture proved insufficient).

Evidence: polish_shot_3 pixel samples read machines at RGB 39-81
against a 220 floor. Root cause measured, not guessed: the eleven
Meshy base_color maps differ 4.7x in mean linear luminance
(PowerPlant 0.231 vs StorageRack 0.049), so no single master boost
can work. Each MI now overrides BaseColorBoost = 0.22 / measured
(clamped [1, 5]), landing every model on the same graphite-steel
read below the 0.30 floor. Measurements from
SourceAssets/.../StationModels_MeshyIntake_v001/TexturesByModel.
"""

import unreal

MAT_DIR = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials"

BOOSTS = {
    "CircuitFab": 1.01,  # albedo 0.218 linear
    "DroneAssembly": 3.55,  # albedo 0.062 linear
    "DroneCargoLift": 3.67,  # albedo 0.060 linear
    "DroneSpray": 4.00,  # albedo 0.055 linear
    "DroneWinch": 3.73,  # albedo 0.059 linear
    "PowerCellPlant": 1.47,  # albedo 0.150 linear
    "PowerPlant": 1.00,  # albedo 0.231 linear
    "PropulsionStation": 1.23,  # albedo 0.179 linear
    "RollingMill": 1.50,  # albedo 0.147 linear
    "StorageRack": 4.49,  # albedo 0.049 linear
    "SubAssemblyRobot": 1.54,  # albedo 0.143 linear
}

mel = unreal.MaterialEditingLibrary
lib = unreal.EditorAssetLibrary

missing = []
for key, boost in BOOSTS.items():
    path = "%s/MI_LB_%s" % (MAT_DIR, key)
    mi = unreal.load_asset(path)
    if mi is None:
        missing.append(key)
        continue
    mel.set_material_instance_scalar_parameter_value(
        mi, "BaseColorBoost", boost)
    mel.update_material_instance(mi)
    lib.save_asset(path)
    unreal.log("BOOST %s = %.2f" % (key, boost))
if missing:
    raise RuntimeError("FAIL CLOSED: missing MIs: %s" % ", ".join(missing))
unreal.log("NORMALIZED %d instances to 0.22 linear" % len(BOOSTS))
