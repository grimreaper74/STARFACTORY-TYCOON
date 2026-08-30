"""Read-only inventory of lighting and post-processing in the FullHall candidate."""
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
REPORT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "fullhall_lighting_audit_v001.json"

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load candidate")
rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if not isinstance(actor, (unreal.DirectionalLight, unreal.SkyLight, unreal.RectLight, unreal.PointLight, unreal.SpotLight, unreal.PostProcessVolume)):
        continue
    loc = actor.get_actor_location()
    row = {
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location_cm": [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)],
        "hidden_in_game": bool(actor.get_editor_property("hidden")),
    }
    component = actor.get_component_by_class(unreal.LightComponent)
    if component is not None:
        row["intensity"] = float(component.get_editor_property("intensity"))
        row["visible"] = bool(component.is_visible())
        row["mobility"] = str(component.get_editor_property("mobility"))
    if isinstance(actor, unreal.PostProcessVolume):
        row["unbound"] = bool(actor.get_editor_property("unbound"))
        row["blend_weight"] = float(actor.get_editor_property("blend_weight"))
    rows.append(row)

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS_READ_ONLY", "map": MAP, "count": len(rows), "actors": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_FULLHALL_LIGHTING_AUDIT_PASS count=%d" % len(rows))
unreal.SystemLibrary.quit_editor()
