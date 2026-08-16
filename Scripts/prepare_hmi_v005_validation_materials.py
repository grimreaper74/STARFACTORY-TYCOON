"""Create compiled colour MICs and bind them to the native HMI validation map."""

import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_HMI05_UnrealNativeValidation"
MAT_DIR = "/Game/LineBoss/Developer/Validation/HMI05_CaptureMaterials"
PARENT = "/Engine/ArtTools/RenderToTexture/Materials/Debug/M_Emissive_Color.M_Emissive_Color"

palette = {
    "M_HMI05_Stainless": (0.23, 0.27, 0.30),
    "M_HMI05_EdgeSteel": (0.035, 0.045, 0.055),
    "M_HMI05_Charcoal": (0.018, 0.024, 0.030),
    "M_HMI05_Rubber": (0.004, 0.006, 0.008),
    "M_HMI05_Screen": (0.005, 0.10, 0.15),
    "M_HMI05_UI": (0.02, 0.30, 0.58),
    "M_HMI05_White": (0.72, 0.76, 0.78),
    "M_HMI05_Red": (0.62, 0.015, 0.006),
    "M_HMI05_Amber": (0.95, 0.28, 0.006),
    "M_HMI05_Green": (0.008, 0.52, 0.05),
    "M_HMI05_Blue": (0.008, 0.16, 0.70),
    "M_HMI05_SafetyYellow": (0.95, 0.48, 0.006),
    "M_LB_FactoryConcrete": (0.20, 0.22, 0.24),
}

parent = unreal.load_asset(PARENT)
tools = unreal.AssetToolsHelpers.get_asset_tools()
materials = {}
for source_name, colour in palette.items():
    asset_name = f"MI_HMI05_CAPTURE_{source_name}"
    path = f"{MAT_DIR}/{asset_name}"
    mic = unreal.EditorAssetLibrary.load_asset(path)
    if mic is None:
        mic = tools.create_asset(asset_name, MAT_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mic.set_editor_property("parent", parent)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        mic, "Color", unreal.LinearColor(*colour, 1.0)
    )
    unreal.MaterialEditingLibrary.update_material_instance(mic)
    unreal.EditorAssetLibrary.save_loaded_asset(mic, only_if_is_dirty=False)
    materials[source_name] = mic

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
bound = 0
for actor in actors.get_all_level_actors():
    if not actor.get_actor_label().startswith("LB_HMI05_"):
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None:
        continue
    source = component.get_material(0)
    source_name = source.get_name() if source else ""
    replacement = materials.get(source_name)
    if replacement is not None:
        component.set_material(0, replacement)
        bound += 1

levels.save_current_level()
unreal.EditorAssetLibrary.save_directory(MAT_DIR, only_if_is_dirty=False, recursive=True)
unreal.log(f"LINE_BOSS_HMI05_CAPTURE_MATERIALS_PASS bound={bound}")
