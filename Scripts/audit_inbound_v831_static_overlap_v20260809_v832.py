from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Maps/LB_PressShop_CleanConnectedS07_v20260809_v791"
OUT = ROOT / "Saved/Audits/PressShopIntegration/inbound_v831_static_overlap_v20260809_v832.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"

VOLUMES = {
    "crane_static_frame": {"min": [-9602.5, -3444.5, 0.0], "max": [-8637.5, -1999.5, 780.5]},
    "lorry": {"min": [-9127.5, -3325.0, 0.0], "max": [-8872.5, -1675.0, 400.0]},
    "pr001": {"min": [-9514.5, -2658.75, 0.0], "max": [-9285.5, -2341.25, 270.0]},
}


def protected_hash():
    return hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()


def overlap(a_min, a_max, b_min, b_max):
    return all(a_min[i] <= b_max[i] and a_max[i] >= b_min[i] for i in range(3))


if OUT.exists():
    raise RuntimeError("fresh-output invariant failed")
if protected_hash() != EXPECTED:
    raise RuntimeError("protected-map invariant failed before audit")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("v791 load failed")

records = []
for actor in actors.get_all_level_actors():
    origin, extent = actor.get_actor_bounds(False)
    b_min = [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z]
    b_max = [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z]
    hits = [name for name, volume in VOLUMES.items() if overlap(b_min, b_max, volume["min"], volume["max"])]
    if not hits:
        continue
    collision_components = []
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        try:
            setting = str(component.get_collision_enabled())
        except Exception:
            setting = "UNKNOWN"
        if "NO_COLLISION" not in setting.upper():
            collision_components.append({"name": component.get_name(), "collision_enabled": setting})
    label = actor.get_actor_label()
    tags = [str(tag) for tag in actor.tags]
    searchable = (label + " " + " ".join(tags)).lower()
    allowed_surface = any(token in searchable for token in ["floor", "paint", "walkway", "marking", "decal"])
    records.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "tags": sorted(tags),
        "location_cm": [round(actor.get_actor_location().x, 3), round(actor.get_actor_location().y, 3), round(actor.get_actor_location().z, 3)],
        "bounds_min_cm": [round(value, 3) for value in b_min],
        "bounds_max_cm": [round(value, 3) for value in b_max],
        "overlaps": hits,
        "allowed_floor_or_marking_surface": allowed_surface,
        "collision_component_count": len(collision_components),
        "collision_components": collision_components,
    })

records.sort(key=lambda item: item["label"])
blocking = [item for item in records if item["collision_component_count"] > 0 and not item["allowed_floor_or_marking_surface"]]
after = protected_hash()
payload = {
    "$schema": "line-boss/audit/inbound-v831-static-overlap/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_AABB_CANDIDATE_OVERLAP_REVIEW_REQUIRED",
    "map": MAP,
    "placement_authority": "Saved/Audits/PressShopIntegration/inbound_handoff_blender_placement_contract_v20260809_v831.json",
    "proposed_volumes_cm": VOLUMES,
    "overlapping_actor_count": len(records),
    "candidate_blocker_count": len(blocking),
    "candidate_blocker_labels": [item["label"] for item in blocking],
    "actors": records,
    "limitations": [
        "axis-aligned bounds are a conservative broad phase and do not prove primitive-level clearance",
        "new candidate assets were not imported or placed",
        "floor and non-collision marking contact is expected",
    ],
    "protected_sha256_before": EXPECTED,
    "protected_sha256_after": after,
    "protected_unchanged": after == EXPECTED,
    "meshy_credits_used": 0,
    "map_modified": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_V831_STATIC_OVERLAP_V832_COMPLETE")
