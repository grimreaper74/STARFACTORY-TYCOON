"""Read-only audit of visible actors in the 2126 press service lane."""
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
OUT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "service_lane_clutter_v001.json"

if OUT.exists():
    raise RuntimeError("refusing to overwrite service-lane audit")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated FullHall candidate")
rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    location = actor.get_actor_location()
    if not (-1800.0 <= location.x <= 1800.0 and -1000.0 <= location.y <= 7000.0):
        continue
    if bool(actor.get_editor_property("hidden")):
        continue
    mesh_path = None
    materials = []
    if isinstance(actor, unreal.StaticMeshActor):
        component = actor.static_mesh_component
        if not component.is_visible():
            continue
        mesh = component.get_editor_property("static_mesh")
        mesh_path = mesh.get_path_name() if mesh else None
        materials = [component.get_material(index).get_path_name() if component.get_material(index) else None for index in range(component.get_num_materials())]
    rows.append({
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location_cm": [location.x, location.y, location.z],
        "mesh": mesh_path,
        "materials": materials,
        "tags": [str(tag) for tag in actor.tags],
    })
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"status": "PASS_READ_ONLY", "map": MAP, "count": len(rows), "actors": sorted(rows, key=lambda row: (row["location_cm"][1], row["label"]))}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_SERVICE_LANE_AUDIT count=%d" % len(rows))
unreal.SystemLibrary.quit_editor()
