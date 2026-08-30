import json
import os
import unreal

MAP_PATH = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
OUT_PATH = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressShop2126\inbound_overhead_audit_v001.json"

unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
actors = unreal.EditorLevelLibrary.get_all_level_actors()
keywords = (
    "crane", "bridge", "rail", "girder", "endtruck", "end truck",
    "hoist", "roofbeam", "roof beam", "truss", "overhead", "runway",
)
rows = []
for actor in actors:
    label = actor.get_actor_label()
    loc = actor.get_actor_location()
    if not (-11000.0 <= loc.x <= -6500.0 and -5200.0 <= loc.y <= 1200.0):
        continue
    cls = actor.get_class().get_name()
    asset = ""
    try:
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp and comp.static_mesh:
            asset = comp.static_mesh.get_path_name()
    except Exception:
        pass
    haystack = f"{label} {cls} {asset}".lower()
    if any(k in haystack for k in keywords) or loc.z >= 800.0:
        origin, extent = actor.get_actor_bounds(False, False)
        rows.append({
            "label": label,
            "class": cls,
            "asset": asset,
            "location_cm": [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)],
            "bounds_origin_cm": [round(origin.x, 2), round(origin.y, 2), round(origin.z, 2)],
            "bounds_extent_cm": [round(extent.x, 2), round(extent.y, 2), round(extent.z, 2)],
            "hidden": bool(actor.is_hidden_ed()),
        })

rows.sort(key=lambda r: (r["location_cm"][2], r["label"]))
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as handle:
    json.dump({"map": MAP_PATH, "count": len(rows), "actors": rows}, handle, indent=2)
unreal.log(f"PRESSSHOP_2126_INBOUND_OVERHEAD_AUDIT_PASS count={len(rows)} output={OUT_PATH}")
