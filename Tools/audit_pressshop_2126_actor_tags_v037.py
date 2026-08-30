"""Read-only inventory of candidate actor tags and source meshes."""

import json
from collections import Counter, defaultdict
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_actor_tags_v037.json"

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")

rows = []
counts = Counter()
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    for tag in tags:
        counts[tag] += 1
    location = actor.get_actor_location()
    mesh = None
    if isinstance(actor, unreal.StaticMeshActor):
        value = actor.static_mesh_component.get_editor_property("static_mesh")
        mesh = value.get_path_name() if isinstance(value, unreal.StaticMesh) else None
    rows.append({
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "tags": tags,
        "location_cm": [round(location.x, 1), round(location.y, 1), round(location.z, 1)],
        "mesh": mesh,
    })

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__READ_ONLY_CANDIDATE_ACTOR_TAG_AUDIT",
    "tag_counts": dict(sorted(counts.items())),
    "actor_rows": rows,
    "map_saved": False,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_ACTOR_TAG_AUDIT_V037_PASS")
