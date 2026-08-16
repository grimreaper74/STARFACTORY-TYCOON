"""Retarget the passed v087 station collision contract to isolated v089."""

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "Saved/Audits/PR009_InMap_v087/release_collision_build.json"
GUIDES = ROOT / "Saved/Audits/PR009_InMap_v089/transfer_guide_collision_build.json"
OUT = ROOT / "Saved/Audits/PR009_InMap_v089/release_collision_build.json"


def main():
    payload = json.loads(BASE.read_text(encoding="utf-8"))
    guides = json.loads(GUIDES.read_text(encoding="utf-8"))
    payload["$schema"] = "cairnwell/audit/pr009-release-collision-build-v089/v1"
    payload["generated_utc"] = datetime.now(timezone.utc).isoformat()
    payload["status"] = "V089_STATION_SIMPLE_COLLISION_PLUS_AUTHORED_OPEN_TRANSFER_GUIDES__FULL_RUNTIME_AND_SWEEP_GATES_REQUIRED__NOT_PROMOTED"
    payload["parent_map"] = guides["parent_map"]
    payload["target_map"] = guides["target_map"]
    for key in ("static_groups", "moving_collision_actors", "fixed_chassis_collision_actors"):
        for row in payload[key]:
            row["actor"] = row["actor"].replace("V087", "V089").replace("v087", "v089")
    payload["transfer_guide_collision_build"] = str(GUIDES.relative_to(ROOT)).replace("\\", "/")
    payload["transfer_guide_release_asset"] = guides["release_candidate_asset"]
    payload["transfer_guide_collision_counts"] = guides["collision_counts"]
    payload["transfer_guide_clear_channel_mm"] = guides["clear_channel_mm"]
    payload["blank_axis_authority"] = {
        "maximum_mm_flow_by_across": [2600, 1800],
        "station_local_x": "across strip/lane",
        "station_local_y": "material flow",
    }
    payload["experimental_v088_used_as_parent"] = False
    payload["parent_v087_modified"] = False
    payload["promotion_authorized"] = False
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
