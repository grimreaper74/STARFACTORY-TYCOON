"""build_station_materials_v008.py - THE compile fix. The game log
(polish_autoshow_v003) finally named the whole night's ghost:

  M_LB_MeshyPBR_v003: Failed to compile Material for PCD3D_SM6,
  Default Material will be used in game.
  (Node TextureSampleParameter2D) Sampler type is Linear Color,
  should be Color for /Engine/EngineResources/DefaultTexture

The MetallicRoughness sampler is Linear Color but its master DEFAULT
texture was the engine DefaultTexture (sRGB) - a mismatch that fails
the whole material, so every station/drone rendered the engine
default grey; that is why no albedo boost ever moved a pixel. The MI
texture overrides were always correct - the master itself must
compile with its own defaults.

Fix, fail-closed:
1. Every T_LB_*_MR texture is forced sRGB=false (it is data, not
   colour; if it was imported sRGB the roughness/metallic reads were
   wrong anyway).
2. The master's MetallicRoughness sampler default becomes one of
   those linear MR textures, so sampler and texture agree.
3. Recompile + save, then FAIL CLOSED if the master still reports
   compile errors.
"""

import unreal

ROOT = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
MASTER = ROOT + "/Materials/M_LB_MeshyPBR_v003"
TEX_DIR = ROOT + "/Textures"

KEYS = ["CircuitFab", "DroneAssembly", "DroneCargoLift", "DroneSpray",
        "DroneWinch", "PowerCellPlant", "PowerPlant", "PropulsionStation",
        "RollingMill", "StorageRack", "SubAssemblyRobot"]

mel = unreal.MaterialEditingLibrary
lib = unreal.EditorAssetLibrary

fixed = 0
for key in KEYS:
    path = "%s/T_LB_%s_MR" % (TEX_DIR, key)
    tex = unreal.load_asset(path)
    if tex is None:
        raise RuntimeError("FAIL CLOSED: %s missing" % path)
    if tex.get_editor_property("srgb"):
        tex.set_editor_property("srgb", False)
        lib.save_asset(path)
        fixed += 1
unreal.log("MR textures forced linear: %d changed" % fixed)

master = unreal.load_asset(MASTER)
default_mr = unreal.load_asset("%s/T_LB_RollingMill_MR" % TEX_DIR)
bound = False
for e in mel.get_material_expressions(master):
    if isinstance(e, unreal.MaterialExpressionTextureSampleParameter2D) \
            and str(e.get_editor_property("parameter_name")) \
            == "MetallicRoughness":
        e.set_editor_property("texture", default_mr)
        bound = True
if not bound:
    raise RuntimeError("FAIL CLOSED: MetallicRoughness sampler missing")
mel.recompile_material(master)
lib.save_asset(MASTER)

# Fail closed on any remaining compile problem the editor can see.
stats = unreal.MaterialEditingLibrary.get_statistics(master)
unreal.log("master stats: %s" % stats)
unreal.log("V008 DONE: master default MR now linear; sampler agrees")
