import json
from pathlib import Path
import unreal

# A roofless candidate should not ask for a static-light bake.  This converts
# only level-owned light components in v004 to Movable; it neither builds
# lighting nor edits a shared light asset or protected level.
EXPECTED_MAP_SUFFIX = "LB_PressShop_SteamOpenBay_v004"
REPORT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressShopIntegration\steam_openbay_v004_movable_lights.json")
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or not world.get_path_name().endswith(EXPECTED_MAP_SUFFIX):
    raise RuntimeError("Refusing light mobility correction outside " + EXPECTED_MAP_SUFFIX)

updated = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    for component in actor.get_components_by_class(unreal.LightComponentBase):
        mobility = component.get_editor_property("mobility")
        if mobility != unreal.ComponentMobility.MOVABLE:
            updated.append({"actor": actor.get_actor_label(), "component": component.get_name(), "from": str(mobility)})
            component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)

if not updated:
    raise RuntimeError("No non-movable level light components found; refusing a no-op claim")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate light-mobility correction")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS__V004_ALL_LEVEL_LIGHTS_MOVABLE", "updated": updated}, indent=2) + "\n", encoding="utf-8")
unreal.log("PRESS_SHOP_V004_MOVABLE_LIGHTS_PASS count={}".format(len(updated)))
