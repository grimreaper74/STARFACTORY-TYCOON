"""Read-only inventory of the current 2126 coil corridor."""
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
OUT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "coil_corridor_audit_v001.json"

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 map")
rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    loc = actor.get_actor_location()
    if not (-8100.0 <= loc.x <= -5000.0 and -5200.0 <= loc.y <= 1300.0):
        continue
    label = actor.get_actor_label()
    asset = ""
    if isinstance(actor, unreal.StaticMeshActor):
        mesh = actor.static_mesh_component.static_mesh
        asset = mesh.get_path_name() if mesh else ""
    origin, extent = actor.get_actor_bounds(False, False)
    rows.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "asset": asset,
        "location_cm": [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)],
        "bounds_extent_cm": [round(extent.x, 2), round(extent.y, 2), round(extent.z, 2)],
    })
rows.sort(key=lambda row: (row["location_cm"][0], row["location_cm"][1], row["label"]))
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"status": "PASS", "map": MAP, "count": len(rows), "actors": rows}, indent=2) + "\n", encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_COIL_CORRIDOR_AUDIT_PASS count={len(rows)} output={OUT}")
unreal.SystemLibrary.quit_editor()
