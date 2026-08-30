"""Read-only inventory of the current 2126 PR003/PR004 front-end corridor."""
import json
from collections import Counter
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
OUT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "frontend_corridor_audit_v001.json"

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 map")
rows = []
groups = Counter()
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    loc = actor.get_actor_location()
    if not (-5200.0 <= loc.x <= -1000.0 and -5200.0 <= loc.y <= 1300.0):
        continue
    label = actor.get_actor_label()
    asset = ""
    if isinstance(actor, unreal.StaticMeshActor):
        mesh = actor.static_mesh_component.static_mesh
        asset = mesh.get_path_name() if mesh else ""
    prefix = "OTHER"
    for candidate in ("LB_INT_FRONT_PR003", "LB_INT_PR003", "LB_PR003", "LB_INT_FRONT_PR004", "LB_INT_PR004", "LB_PR004"):
        if label.startswith(candidate):
            prefix = candidate
            break
    groups[(prefix, actor.get_class().get_name())] += 1
    rows.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "prefix_group": prefix,
        "asset": asset,
        "location_cm": [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)],
    })
rows.sort(key=lambda row: (row["prefix_group"], row["class"], row["label"]))
summary = [{"prefix_group": key[0], "class": key[1], "count": value} for key, value in sorted(groups.items())]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"status": "PASS", "map": MAP, "count": len(rows), "summary": summary, "actors": rows}, indent=2) + "\n", encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_FRONTEND_CORRIDOR_AUDIT_PASS count={len(rows)} output={OUT}")
unreal.SystemLibrary.quit_editor()
