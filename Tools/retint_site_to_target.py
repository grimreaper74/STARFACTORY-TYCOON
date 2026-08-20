"""Retint the site's big surfaces toward the approved target frame.

The owner's mockup (SourceAssets/Reference, 2026-08-20) sets the look:
warm cream shop floors and walls, green surroundings. Three bindings
paint those surfaces:
  - MI_CA_MW_IndustrialGraphiteWall_v238   (every Site_Wall_* run)
  - MI_LB_SealedFactoryConcrete_Neutral_v001 (LB_OF_ENV_HISM_FloorSlabs)
  - Site_GroundPlane -> M_CA_MW_PR004_HoldSealedConcrete_v117 (plain
    material - it gets a tinted child instance, or the flat vegetation
    master if the concrete master exposes no colour parameter).
Every set is read back and reported: a silently-ignored parameter name
looks identical to a wrong tint (lesson from the site ground pass).
"""
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_retint.json"
MAT_DIR = "/Game/LineBoss/Site/TargetLook_v001"

CREAM_WALL = unreal.LinearColor(0.360, 0.330, 0.270, 1.0)
CREAM_FLOOR = unreal.LinearColor(0.320, 0.285, 0.220, 1.0)
GRASS = unreal.LinearColor(0.100, 0.130, 0.065, 1.0)

MEL = unreal.MaterialEditingLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
REPORT = {"set": {}, "ground": "", "warnings": []}


def find_asset(name):
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    found = registry.get_assets_by_package_name
    data = registry.get_all_assets()
    return None


def load_by_name(name):
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    filt = unreal.ARFilter(class_names=[], package_paths=["/Game"],
                           recursive_paths=True)
    for asset in registry.get_assets(filt):
        if str(asset.asset_name) == name:
            return unreal.load_asset(str(asset.package_name))
    return None


def tint_instance(name, colour):
    instance = load_by_name(name)
    if instance is None:
        REPORT["warnings"].append("missing instance {}".format(name))
        return
    names = [str(n) for n in MEL.get_vector_parameter_names(instance)]
    touched = {}
    for parameter in names:
        if any(f in parameter.lower() for f in
               ("tint", "color", "colour", "albedo", "base")):
            MEL.set_material_instance_vector_parameter_value(
                instance, parameter, colour)
            back = MEL.get_material_instance_vector_parameter_value(
                instance, parameter)
            touched[parameter] = [round(back.r, 3), round(back.g, 3),
                                  round(back.b, 3)]
    if not touched:
        REPORT["warnings"].append(
            "{} exposes no colour parameter ({})".format(name, names))
        return
    unreal.EditorAssetLibrary.save_loaded_asset(instance, False)
    REPORT["set"][name] = touched


tint_instance("MI_CA_MW_IndustrialGraphiteWall_v238", CREAM_WALL)
tint_instance("MI_LB_SealedFactoryConcrete_Neutral_v001", CREAM_FLOOR)

# Ground plane: give it a green child instance of its own master when the
# master exposes a colour parameter; otherwise fall back to the flat
# vegetation master, which certainly does.
LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

ground = None
for actor in ACTOR_SUB.get_all_level_actors():
    if actor.get_actor_label() == "Site_GroundPlane":
        ground = actor
        break
if ground is None:
    raise RuntimeError("Site_GroundPlane not found")

existing = unreal.load_asset(MAT_DIR + "/MI_LB_Site_GroundGrass_v001")
if existing is None:
    parent = load_by_name("M_CA_MW_PR004_HoldSealedConcrete_v117")
    instance = TOOLS.create_asset("MI_LB_Site_GroundGrass_v001", MAT_DIR,
                                  unreal.MaterialInstanceConstant,
                                  unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(instance, parent)
    names = [str(n) for n in MEL.get_vector_parameter_names(instance)]
    hits = [n for n in names if any(f in n.lower() for f in
            ("tint", "color", "colour", "albedo", "base"))]
    if not hits:
        veg_master = unreal.load_asset(
            "/Game/LineBoss/Site/Vegetation_v001/Materials/"
            "M_LB_Site_Vegetation_v001")
        MEL.set_material_instance_parent(instance, veg_master)
        hits = ["Tint"]
        REPORT["ground"] = "flat vegetation master (concrete has no tint)"
    else:
        REPORT["ground"] = "child of the concrete master"
    for parameter in hits:
        MEL.set_material_instance_vector_parameter_value(
            instance, parameter, GRASS)
    unreal.EditorAssetLibrary.save_loaded_asset(instance, False)
    existing = instance

component = ground.get_components_by_class(unreal.StaticMeshComponent)[0]
component.set_material(0, existing)
if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")

with open(OUT, "w") as handle:
    json.dump(REPORT, handle, indent=1)
unreal.log("LINE_BOSS_RETINT {}".format(json.dumps(REPORT["set"])))
