"""Inventory station-scoped donor actors absent from protected whole-shop v273."""
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
TARGET = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273"
DONORS = {
    "PR006": "/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v208",
    "PR007": "/Game/LineBoss/Maps/LB_PressShop_PR007ReleaseArtCandidate_v209",
    "PR008": "/Game/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210",
}
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr006_pr008_missing_donor_station_actors_v273.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def row(actor):
    result = {
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "tags": [str(tag) for tag in actor.tags],
        "location": [float(v) for v in (actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z)],
    }
    if isinstance(actor, unreal.StaticMeshActor):
        component = actor.static_mesh_component
        result["mesh"] = component.static_mesh.get_path_name() if component.static_mesh else None
        result["attached_to"] = component.get_attach_parent().get_name() if component.get_attach_parent() else None
    return result


if not levels.load_level(TARGET):
    raise RuntimeError(TARGET)
target_labels = {actor.get_actor_label() for actor in actors_api.get_all_level_actors()}
families = {}
for family, donor in DONORS.items():
    if not levels.load_level(donor):
        raise RuntimeError(donor)
    station_tag = f"LB.Station.{family}"
    candidates = [actor for actor in actors_api.get_all_level_actors() if station_tag in [str(tag) for tag in actor.tags]]
    missing = [row(actor) for actor in candidates if actor.get_actor_label() not in target_labels]
    families[family] = {
        "donor_station_actor_count": len(candidates),
        "missing_count": len(missing),
        "missing_by_class": {name: sum(1 for item in missing if item["class"] == name) for name in sorted({item["class"] for item in missing})},
        "missing": sorted(missing, key=lambda item: item["label"]),
    }

payload = {
    "$schema": "cairnwell/audit/press-shop-pr006-pr008-missing-donor-station-actors-v273/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "target": TARGET,
    "donors": DONORS,
    "families": families,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
