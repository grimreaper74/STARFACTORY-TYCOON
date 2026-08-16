"""Record transforms and bounds of Train A v060 service/endpoint actors."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v060"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_service_layout_v060.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

needles = (
    "DieCart", "DockCoupling", "MaintenanceAccess", "InstalledServiceBank",
    "EnclosedFacade", "VisibleBlankFeed", "VisiblePanelDischarge",
    "CAM_DieChangeService", "CAM_DieCartDetail",
)
records = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if not any(needle in label for needle in needles):
        continue
    origin, extent = actor.get_actor_bounds(False)
    records.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": [round(v, 3) for v in (actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z)],
        "rotation_deg": [round(v, 3) for v in (actor.get_actor_rotation().roll, actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw)],
        "bounds_origin_cm": [round(v, 3) for v in (origin.x, origin.y, origin.z)],
        "bounds_extent_cm": [round(v, 3) for v in (extent.x, extent.y, extent.z)],
        "tags": sorted(str(tag) for tag in actor.tags),
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "actors": sorted(records, key=lambda row: row["label"])}, indent=2), encoding="utf-8")
print(json.dumps({"actors": len(records), "output": str(OUT)}, indent=2))
