"""Read-only lighting and post-process audit for the 2126 screenshot candidate."""

import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_lighting_v019.json"


def safe(value):
    try:
        return str(value)
    except Exception:
        return "<unavailable>"


if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    actor_class = actor.get_class().get_name()
    if any(key in actor_class for key in ("Light", "PostProcess", "Sky")) or any(key in label.lower() for key in ("light", "sky", "stylized", "post")):
        row = {"label": label, "class": actor_class, "location_cm": [round(v, 1) for v in (actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z)]}
        for property_name in ("intensity", "light_color", "temperature", "use_temperature", "cast_shadows", "unbound", "blend_weight", "settings"):
            try:
                row[property_name] = safe(actor.get_editor_property(property_name))
            except Exception:
                pass
        components = []
        for component in actor.get_components_by_class(unreal.ActorComponent):
            name = component.get_class().get_name()
            if any(key in name for key in ("Light", "Sky", "PostProcess")):
                component_row = {"class": name}
                for property_name in ("intensity", "light_color", "temperature", "use_temperature", "cast_shadows"):
                    try:
                        component_row[property_name] = safe(component.get_editor_property(property_name))
                    except Exception:
                        pass
                components.append(component_row)
        if components:
            row["components"] = components
        rows.append(row)
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS__READ_ONLY_LIGHTING_AUDIT", "actors": rows}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_LIGHTING_AUDIT_V019_PASS")
