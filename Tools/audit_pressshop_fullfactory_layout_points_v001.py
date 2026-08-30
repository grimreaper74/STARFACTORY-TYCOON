"""Read-only layout-point audit for the restored full Press Shop."""
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001"
OUT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "fullfactory_layout_points_v001.json"
TERMS = ("zone_press", "pr008", "pr009", "pr010", "pr040", "pr042", "pr044", "dispatch", "stillage", "pallet", "coilagv", "coil_store", "finishedfloor", "managementoverview")

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load restored factory")
rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if not any(term in label.lower() for term in TERMS):
        continue
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    try:
        origin, extent = actor.get_actor_bounds(False, False)
        bounds = {"origin_cm": [round(origin.x, 1), round(origin.y, 1), round(origin.z, 1)], "extent_cm": [round(extent.x, 1), round(extent.y, 1), round(extent.z, 1)]}
    except Exception:
        bounds = None
    rows.append({"label": label, "class": actor.get_class().get_name(), "location_cm": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)], "rotation": [round(rot.pitch, 1), round(rot.yaw, 1), round(rot.roll, 1)], "bounds": bounds})
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "status": "PASS", "actors": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_FULLFACTORY_LAYOUT_POINTS_PASS {}".format(OUT))
unreal.SystemLibrary.quit_editor()
