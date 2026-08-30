"""Read-only lighting inventory for the isolated Press Shop candidate."""
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_lighting_v001.json"

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate map")

found = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    component = None
    if isinstance(actor, (unreal.DirectionalLight, unreal.SkyLight, unreal.PointLight, unreal.SpotLight, unreal.RectLight)):
        component = actor.get_component_by_class(unreal.LightComponent)
    if component is not None:
        row = {
            "label": actor.get_actor_label(),
            "class": actor.get_class().get_name(),
            "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
            "intensity": component.get_editor_property("intensity"),
            "light_color": str(component.get_editor_property("light_color")),
            "visible": component.get_editor_property("visible"),
            "mobility": str(component.mobility),
        }
        for key in ("indirect_lighting_intensity", "source_angle", "intensity_units"):
            try:
                row[key] = str(component.get_editor_property(key))
            except Exception:
                pass
        found.append(row)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "lights": found}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_LIGHT_AUDIT_PASS " + str(len(found)))
unreal.SystemLibrary.quit_editor()
