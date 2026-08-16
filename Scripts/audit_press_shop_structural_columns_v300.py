"""Read-only exact-v300 hall-column and structural-grid inventory."""

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_structural_column_inventory_v300.json"
EXPECTED_SHA = "93BF6B46BAD2292019E31C08EF31AF9C9C21CE98BAB9A045CF7670AF5A7AA52C"
TOKEN = re.compile(r"(?:column|pillar|structural[_ -]?post|roof[_ -]?post)", re.IGNORECASE)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


before = sha256(MAP_FILE)
if before != EXPECTED_SHA:
    raise RuntimeError(f"v300 hash drift {before}")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

rows = []
for actor in api.get_all_level_actors():
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh_path = component.static_mesh.get_path_name() if component and component.static_mesh else ""
    label = actor.get_actor_label()
    if not TOKEN.search(label + " " + mesh_path):
        continue
    location = actor.get_actor_location()
    origin, extent = actor.get_actor_bounds(False, False)
    rows.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "mesh": mesh_path or None,
        "location_cm": [location.x, location.y, location.z],
        "bounds_min_cm": [origin.x-extent.x, origin.y-extent.y, origin.z-extent.z],
        "bounds_max_cm": [origin.x+extent.x, origin.y+extent.y, origin.z+extent.z],
        "size_cm": [extent.x*2.0, extent.y*2.0, extent.z*2.0],
        "collision_profile": str(component.get_collision_profile_name()) if component else None,
        "collision_enabled": str(component.get_collision_enabled()) if component else None,
        "affects_navigation": bool(component.get_editor_property("can_ever_affect_navigation")) if component else None,
        "visible": bool(component.get_editor_property("visible")) if component else None,
        "tags": [str(tag) for tag in actor.tags],
    })

xs = sorted(set(round(row["location_cm"][0], 3) for row in rows))
ys = sorted(set(round(row["location_cm"][1], 3) for row in rows))
def gaps(values):
    return [round(values[index+1]-values[index], 3) for index in range(len(values)-1)]

train_zone = [row for row in rows if 0.0 <= row["location_cm"][0] <= 10000.0 and -6500.0 <= row["location_cm"][1] <= 2500.0]
blocking = [row for row in rows if row["collision_profile"] not in (None, "NoCollision") and "NO_COLLISION" not in (row["collision_enabled"] or "")]
after = sha256(MAP_FILE)
failures = []
if before != after:
    failures.append("read-only structural audit changed v300")
if not rows:
    failures.append("no structural column candidates found")
payload = {
    "$schema": "cairnwell/audit/press-shop-structural-column-inventory-v300/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__READ_ONLY_EXACT_V300_STRUCTURAL_GRID_INVENTORY__NO_REMOVAL_AUTHORIZED" if not failures else "FAIL__AUDIT_INVALID",
    "map": MAP,
    "map_sha256_before": before,
    "map_sha256_after": after,
    "candidate_count": len(rows),
    "train_zone_candidate_count": len(train_zone),
    "blocking_candidate_count": len(blocking),
    "collision_profile_counts": dict(Counter(row["collision_profile"] for row in rows)),
    "mesh_counts": dict(Counter(row["mesh"] for row in rows)),
    "unique_x_cm": xs,
    "unique_y_cm": ys,
    "x_gaps_cm": gaps(xs),
    "y_gaps_cm": gaps(ys),
    "train_zone_bounds_cm": {"x": [0.0, 10000.0], "y": [-6500.0, 2500.0]},
    "train_zone_candidates": train_zone,
    "all_candidates": rows,
    "authority_note": "This inventory proves actor state only. It does not establish real structural load capacity and authorizes no removal or relocation.",
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({key: payload[key] for key in ("status", "candidate_count", "train_zone_candidate_count", "blocking_candidate_count", "collision_profile_counts", "failures")}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
