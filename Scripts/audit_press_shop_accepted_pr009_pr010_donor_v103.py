"""Read-only extract contract for accepted PR009/PR010 presentation actors."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010Accepted_v103"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_accepted_pr009_pr010_donor_v103.json"
TOKENS = {"PR009": "LB.Asset.Accepted.PR009.v096", "PR010": "LB.Asset.Accepted.PR010.v103"}
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)


def vec(value):
    return [float(value.x), float(value.y), float(value.z)]


def rot(value):
    return [float(value.pitch), float(value.yaw), float(value.roll)]


def record(actor):
    origin, extent = actor.get_actor_bounds(False)
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh = component.get_editor_property("static_mesh") if component else None
    return {
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location_cm": vec(actor.get_actor_location()),
        "rotation_deg": rot(actor.get_actor_rotation()),
        "scale": vec(actor.get_actor_scale3d()),
        "bounds_min_cm": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
        "bounds_max_cm": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
        "mesh": mesh.get_path_name() if mesh else None,
        "materials": [component.get_material(index).get_path_name() if component.get_material(index) else None
                      for index in range(component.get_num_materials())] if component else [],
        "collision_enabled": str(component.get_collision_enabled()) if component else None,
        "collision_profile": str(component.get_collision_profile_name()) if component else None,
        "affects_navigation": bool(component.get_editor_property("can_ever_affect_navigation")) if component else None,
        "tags": [str(tag) for tag in actor.tags],
    }


stations = {}
for station, token in TOKENS.items():
    matched = [record(actor) for actor in actors_api.get_all_level_actors() if token in {str(tag) for tag in actor.tags}]
    presentation = [row for row in matched if row["class"] in {
        "StaticMeshActor", "SkeletalMeshActor", "TextRenderActor", "DecalActor"
    }]
    union_min = [min(row["bounds_min_cm"][axis] for row in presentation) for axis in range(3)] if presentation else None
    union_max = [max(row["bounds_max_cm"][axis] for row in presentation) for axis in range(3)] if presentation else None
    stations[station] = {
        "accepted_tag": token,
        "matched_count": len(matched),
        "presentation_count": len(presentation),
        "class_counts": {name: sum(row["class"] == name for row in matched)
                         for name in sorted({row["class"] for row in matched})},
        "presentation_union_min_cm": union_min,
        "presentation_union_max_cm": union_max,
        "actors": sorted(matched, key=lambda row: (row["class"], row["label"])),
    }

payload = {
    "$schema": "cairnwell/audit/press-shop-accepted-pr009-pr010-donor-v103/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY__ACCEPTED_DONOR_CONTRACT__NO_ASSETS_CHANGED",
    "map": MAP,
    "stations": stations,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "stations": {
    key: {"matched": value["matched_count"], "presentation": value["presentation_count"],
          "classes": value["class_counts"], "min": value["presentation_union_min_cm"],
          "max": value["presentation_union_max_cm"]}
    for key, value in stations.items()}}, indent=2))
unreal.SystemLibrary.quit_editor()
