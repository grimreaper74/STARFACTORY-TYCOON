"""Read-only PR-003 slot-cluster audit against authoritative Sheet 2."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004WrapResponseCandidate_v118"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr003_layout_inspection_v118.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)


def vec(value):
    return [round(float(value.x), 3), round(float(value.y), 3), round(float(value.z), 3)]


pattern = re.compile(r"CS-(0[1-9]|1[0-2])")
clusters = {f"CS-{index:02d}": [] for index in range(1, 13)}
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    matches = pattern.findall(label)
    if not matches:
        matches = [match for tag in actor.tags for match in pattern.findall(str(tag))]
    if not matches:
        continue
    slot = f"CS-{matches[0]}"
    clusters[slot].append({
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": vec(actor.get_actor_location()),
        "attach_parent": (actor.get_attach_parent_actor().get_actor_label()
                          if actor.get_attach_parent_actor() else None),
        "tags": [str(value) for value in actor.tags],
    })

centres = {}
for slot, rows in clusters.items():
    packaged = next((row for row in rows if "PackagedMasterCoil" in row["label"]), None)
    saddle = next((row for row in rows if row["label"].endswith("_CoilSaddle")), None)
    centres[slot] = {
        "packaged_coil_cm": packaged["location_cm"] if packaged else None,
        "saddle_cm": saddle["location_cm"] if saddle else None,
        "cluster_actor_count": len(rows),
    }

xs = sorted({row["packaged_coil_cm"][0] for row in centres.values() if row["packaged_coil_cm"]})
ys = sorted({row["packaged_coil_cm"][1] for row in centres.values() if row["packaged_coil_cm"]})
payload = {
    "$schema": "cairnwell/audit/press-shop-pr003-layout-inspection-v118/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_CURRENT_3X4_LAYOUT_CONTRADICTS_AUTHORITATIVE_SHEET2_6X2__NO_ASSETS_CHANGED",
    "map": MAP,
    "authoritative_reference": "Docs/References/PressShop_Revised_BareCoil_FrontEnd/v001/Sheet_2_PR001_to_PR005_Operational_Plan.png",
    "required_layout": {"columns": 6, "rows": 2, "positions": 12},
    "current_layout": {"unique_x_count": len(xs), "unique_y_count": len(ys), "unique_x_cm": xs, "unique_y_cm": ys},
    "slot_centres": centres,
    "clusters": clusters,
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "current_layout": payload["current_layout"],
                  "cluster_counts": {key: len(value) for key, value in clusters.items()}}, indent=2))
