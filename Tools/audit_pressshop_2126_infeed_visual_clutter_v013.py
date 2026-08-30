"""Read-only actor/bounds audit around the new infeed camera volume."""

import json
from pathlib import Path
import unreal


MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
REPORT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressShopIntegration\pressshop_2126_infeed_visual_clutter_v013.json")


def visible(actor):
    components = actor.get_components_by_class(unreal.PrimitiveComponent)
    return bool(components) and all(component.is_visible() for component in components)


if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if not visible(actor):
        continue
    origin, extent = actor.get_actor_bounds(False)
    if not (-24000 <= origin.x <= -4000 and -14000 <= origin.y <= 14000 and -1000 <= origin.z <= 12000):
        continue
    mesh_path = None
    materials = []
    if isinstance(actor, unreal.StaticMeshActor):
        component = actor.static_mesh_component
        mesh = component.static_mesh
        mesh_path = mesh.get_path_name() if mesh else None
        materials = [item.get_path_name() if item else None for item in component.get_materials()]
    rows.append({
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location_cm": [round(value, 1) for value in (actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z)],
        "bounds_origin_cm": [round(value, 1) for value in (origin.x, origin.y, origin.z)],
        "bounds_extent_cm": [round(value, 1) for value in (extent.x, extent.y, extent.z)],
        "mesh": mesh_path,
        "materials": materials,
    })
rows.sort(key=lambda row: (-max(row["bounds_extent_cm"]), row["label"]))
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS__READ_ONLY_INFEED_VISUAL_CLUTTER_AUDIT", "map": MAP, "actors": rows}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_INFEED_VISUAL_CLUTTER_V013_PASS: %d actors" % len(rows))
