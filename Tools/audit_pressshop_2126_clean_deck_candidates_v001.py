"""Read-only audit of inherited static clutter inside the 2126 production deck."""
import json
from collections import Counter
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
REPORT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "clean_deck_candidate_audit_v001.json"
BOUNDS = {"x": (-10500.0, 8000.0), "y": (-5000.0, 6500.0), "z": (-100.0, 2500.0)}

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load candidate")
rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if not isinstance(actor, (unreal.StaticMeshActor, unreal.TextRenderActor)):
        continue
    label = actor.get_actor_label()
    if label.startswith("2126"):
        continue
    loc = actor.get_actor_location()
    if not (BOUNDS["x"][0] <= loc.x <= BOUNDS["x"][1] and BOUNDS["y"][0] <= loc.y <= BOUNDS["y"][1] and BOUNDS["z"][0] <= loc.z <= BOUNDS["z"][1]):
        continue
    asset = ""
    if isinstance(actor, unreal.StaticMeshActor) and actor.static_mesh_component.static_mesh is not None:
        asset = actor.static_mesh_component.static_mesh.get_path_name()
    rows.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "prefix": label.split("_")[0] + ("_" + label.split("_")[1] if "_" in label else ""),
        "location_cm": [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)],
        "asset": asset,
    })
prefixes = Counter(row["prefix"] for row in rows)
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS_READ_ONLY",
    "map": MAP,
    "bounds_cm": BOUNDS,
    "candidate_count": len(rows),
    "by_prefix": dict(sorted(prefixes.items(), key=lambda item: (-item[1], item[0]))),
    "candidates": rows,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_CLEAN_DECK_AUDIT_PASS candidates=%d" % len(rows))
unreal.SystemLibrary.quit_editor()
