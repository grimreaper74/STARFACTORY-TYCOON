"""Read-only grouping of inherited actors competing with the new 2126 line."""
import json
from collections import defaultdict
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
OUT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "inherited_competition_audit_v001.json"

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 map")

groups = defaultdict(lambda: {"count": 0, "classes": defaultdict(int), "min": [1e30,1e30,1e30], "max": [-1e30,-1e30,-1e30], "samples": []})
rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    loc = actor.get_actor_location()
    parts = label.split("_")
    group = "_".join(parts[:3]) if len(parts) >= 3 else label.split(" |")[0]
    if label.startswith("2126 ") or label.startswith("CAM | 2126"):
        group = "2126_NEW"
    asset = ""
    if isinstance(actor, unreal.StaticMeshActor):
        mesh = actor.static_mesh_component.static_mesh
        asset = mesh.get_path_name() if mesh else ""
    row = {"label":label,"class":actor.get_class().get_name(),"asset":asset,"location_cm":[round(loc.x,2),round(loc.y,2),round(loc.z,2)]}
    rows.append(row)
    item = groups[group]
    item["count"] += 1
    item["classes"][row["class"]] += 1
    for i,value in enumerate((loc.x,loc.y,loc.z)):
        item["min"][i] = min(item["min"][i],value); item["max"][i] = max(item["max"][i],value)
    if len(item["samples"]) < 8:
        item["samples"].append(row)

summary = []
for name,item in groups.items():
    summary.append({"group":name,"count":item["count"],"classes":dict(item["classes"]),"bounds_cm":{"min":[round(v,2) for v in item["min"]],"max":[round(v,2) for v in item["max"]]},"samples":item["samples"]})
summary.sort(key=lambda r:(-r["count"],r["group"]))
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({"status":"PASS","map":MAP,"actor_count":len(rows),"groups":summary},indent=2)+"\n",encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_INHERITED_COMPETITION_AUDIT_PASS actors={len(rows)} output={OUT}")
unreal.SystemLibrary.quit_editor()
