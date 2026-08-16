"""Read-only inventory of retained PR005-PR008 local donor changes for cumulative v211."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_local_merge_donors_v211.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

DONORS = [
    ("PR005", "/Game/LineBoss/Maps/LB_PressShop_PR005ReleaseArtCandidate_v205", "LB_PR005_V205_"),
    ("PR006", "/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v208", "LB_PR006_V208_"),
    ("PR007", "/Game/LineBoss/Maps/LB_PressShop_PR007ReleaseArtCandidate_v209", "LB_PR007_V209_"),
    ("PR008", "/Game/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210", "LB_PR008_V210_"),
]

payload = {
    "$schema": "cairnwell/audit/press-shop-local-merge-donors-v211/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "donors": [],
    "failures": [],
}

for station, map_path, prefix in DONORS:
    if not levels.load_level(map_path):
        payload["failures"].append(f"could not load {map_path}")
        continue
    actors = list(actors_api.get_all_level_actors())
    rows = [a for a in actors if a.get_actor_label().startswith(prefix)]
    entry = {
        "station": station,
        "map": map_path,
        "prefix": prefix,
        "actor_count": len(rows),
        "classes": dict(Counter(a.get_class().get_name() for a in rows)),
        "labels": sorted(a.get_actor_label() for a in rows),
    }
    if station == "PR005":
        entry["removed_v053_labels_present"] = sorted(a.get_actor_label() for a in actors if a.get_actor_label() in {
            "LB_PR005_V053_ReturnStillage_Base", "LB_PR005_V053_ReturnStillage_Open",
            "LB_PR005_V053_ServicePallet", "LB_PR005_V053_ServiceCrate_01",
            "LB_PR005_V053_ServiceCrate_02", "LB_PR005_V053_ServiceCrate_03"})
        entry["infill_count"] = sum(a.get_actor_label() == "LB_PR005_V197_RuntimeCageInfill_Static_v005" for a in actors)
    if station == "PR008":
        entry["generic_v082_anchor_count"] = sum(
            "LB_PR008_V082_Anchor" in a.get_actor_label() and
            (a.get_actor_label().endswith("_Plate") or a.get_actor_label().endswith("_Stud"))
            for a in actors)
    payload["donors"].append(entry)

payload["status"] = "PASS__READ_ONLY_DONOR_INVENTORY" if not payload["failures"] else "FAIL"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
