"""Replace only the deprecated vehicle/inbound mesh references embedded in OneFactory.

This is a map-authoring migration, not an import or topology operation. It preserves
each component, actor, transform, route and material override; it only swaps the
specified legacy static meshes for clean-room native-kit or Engine primitive meshes.
"""

import unreal

MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
NATIVE = "/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001"
CUBE = "/Engine/BasicShapes/Cube.Cube"
CYLINDER = "/Engine/BasicShapes/Cylinder.Cylinder"

PANEL_REPLACEMENTS = {
    "HOOD_PANEL": f"{NATIVE}/Panels/SM_LB_C2040_Hood.SM_LB_C2040_Hood",
    "ROOF_PANEL": f"{NATIVE}/Panels/SM_LB_C2040_Roof.SM_LB_C2040_Roof",
    "DOOR_FRONT_LEFT": f"{NATIVE}/Panels/SM_LB_C2040_FrontDoor_L.SM_LB_C2040_FrontDoor_L",
    "DOOR_FRONT_RIGHT": f"{NATIVE}/Panels/SM_LB_C2040_FrontDoor_L.SM_LB_C2040_FrontDoor_L",
    "DOOR_REAR_LEFT": f"{NATIVE}/Panels/SM_LB_C2040_RearDoor_L.SM_LB_C2040_RearDoor_L",
    "DOOR_REAR_RIGHT": f"{NATIVE}/Panels/SM_LB_C2040_RearDoor_L.SM_LB_C2040_RearDoor_L",
    "FENDER_FRONT_LEFT": f"{NATIVE}/Panels/SM_LB_C2040_FrontFender_L.SM_LB_C2040_FrontFender_L",
    "FENDER_FRONT_RIGHT": f"{NATIVE}/Panels/SM_LB_C2040_FrontFender_L.SM_LB_C2040_FrontFender_L",
    "QUARTER_PANEL_LEFT": f"{NATIVE}/Panels/SM_LB_C2040_QuarterPanel_L.SM_LB_C2040_QuarterPanel_L",
    "QUARTER_PANEL_RIGHT": f"{NATIVE}/Panels/SM_LB_C2040_QuarterPanel_L.SM_LB_C2040_QuarterPanel_L",
    "TAILGATE_PANEL": f"{NATIVE}/Panels/SM_LB_C2040_Tailgate.SM_LB_C2040_Tailgate",
}

assets = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

replacements = {CUBE: assets.load_asset(CUBE), CYLINDER: assets.load_asset(CYLINDER)}
for path in PANEL_REPLACEMENTS.values():
    replacements[path] = assets.load_asset(path)
if not all(replacements.values()):
    raise RuntimeError("A required clean-room replacement mesh is unavailable")

changed = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if not mesh:
            continue
        old_path = mesh.get_path_name()
        target_path = None
        if "/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001/" in old_path:
            target_path = f"{NATIVE}/Layers/SM_LB_C2040_RoofClosures.SM_LB_C2040_RoofClosures"
            replacements.setdefault(target_path, assets.load_asset(target_path))
        elif "/Factory/OneFactory/v001/Vehicles/Cairnwell2040PanelModules_v001/" in old_path:
            for panel_id, panel_path in PANEL_REPLACEMENTS.items():
                if panel_id in old_path:
                    target_path = panel_path
                    break
        elif "/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/" in old_path:
            target_path = CYLINDER if "Coil" in old_path else CUBE
        if target_path:
            target = replacements.get(target_path) or assets.load_asset(target_path)
            if not target:
                raise RuntimeError(f"Missing replacement {target_path}")
            component.set_static_mesh(target)
            changed.append(f"{actor.get_name()}::{component.get_name()} = {target_path}")

if not changed:
    raise RuntimeError("No deprecated map mesh references were found; refusing an empty save")
if not levels.save_current_level():
    raise RuntimeError("Failed to save OneFactory after mesh migration")
unreal.log(f"ONEFACTORY deprecated vehicle map-mesh migration changed {len(changed)} component(s)")
for row in changed:
    unreal.log(row)
