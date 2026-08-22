"""Read-only actor census used to frame current OneFactory process captures."""

import json
from pathlib import Path
import unreal


MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
KEYWORDS = ("paint", "ecoat", "edcoat", "scan", "inspect", "quality")


if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load OneFactory map")

rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    class_name = actor.get_class().get_name()
    searchable = f"{label} {class_name}".lower()
    if not any(keyword in searchable for keyword in KEYWORDS):
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    rows.append((class_name, label, location, rotation))

rows.sort(key=lambda row: (row[0], row[1]))
output = Path(unreal.Paths.project_saved_dir()) / "Audits/OneFactory/current_process_actor_census.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps([
    {
        "class": class_name,
        "label": label,
        "location_cm": [location.x, location.y, location.z],
        "rotation": [rotation.pitch, rotation.yaw, rotation.roll],
    }
    for class_name, label, location, rotation in rows
], indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_ONEFACTORY_PROCESS_ACTORS count={len(rows)}")
unreal.log(f"LINE_BOSS_ONEFACTORY_PROCESS_CENSUS path={output}")
for class_name, label, location, rotation in rows:
    unreal.log(
        "LINE_BOSS_ONEFACTORY_PROCESS_ACTOR "
        f"class={class_name} label={label} "
        f"location=({location.x:.1f},{location.y:.1f},{location.z:.1f}) "
        f"rotation=({rotation.roll:.1f},{rotation.pitch:.1f},{rotation.yaw:.1f})"
    )
