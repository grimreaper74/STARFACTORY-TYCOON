"""Audit the deterministic PR-010 Blender/FBX blockout before Unreal intake."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/PR010/FourLaneBuffer/Blockout_v001"
MANIFEST = SOURCE / "PR010_BLOCKOUT_MANIFEST_v001.json"
OUT = ROOT / "Saved/Audits/PR010_Blockout/pr010_dimensioned_source_v001.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

failures = []
if manifest.get("world_datum_cm") != [1350, -2000, 0]: failures.append("world datum mismatch")
if manifest.get("world_yaw_deg") != -90: failures.append("world yaw must be -90 degrees")
if manifest.get("fixed_lane_centres_x_mm") != [-4500, -1500, 1500, 4500]: failures.append("fixed lane centres mismatch")
if manifest.get("lane_pitch_mm") != 3000: failures.append("lane pitch mismatch")
if manifest.get("estimated_equipment_envelope_mm") != [14000, 8400, 3600]: failures.append("equipment envelope mismatch")
if manifest.get("press_train_datums") != "TBC_NOT_INVENTED": failures.append("press-train datums were invented")

placements = manifest.get("placements", [])
lane_beds = [row for row in placements if "lane_bed" in row.get("tags", [])]
carriers = [row for row in placements if "carrier_position" in row.get("tags", [])]
pylons = [row for row in placements if "lane_identity" in row.get("tags", [])]
if len(lane_beds) != 4: failures.append(f"expected four lane beds, found {len(lane_beds)}")
if len(carriers) != 8: failures.append(f"expected eight carrier positions, found {len(carriers)}")
if len(pylons) != 4: failures.append(f"expected four lane pylons, found {len(pylons)}")
if sorted(row["location_mm"][0] for row in lane_beds) != [-4500, -1500, 1500, 4500]:
    failures.append("lane-bed centres do not match fixed authority")

shuttle = [row for row in placements if "moving_infeed_shuttle" in row.get("tags", [])]
if len(shuttle) != 1 or shuttle[0]["location_mm"] != [0, -3300, 350]: failures.append("infeed shuttle datum mismatch")
shuttle_world_x_cm = 1350 + (shuttle[0]["location_mm"][1] / 10.0) if shuttle else None
if shuttle_world_x_cm != 1020.0: failures.append("infeed shuttle does not land at fixed world X 1020 cm")

assets = manifest.get("assets", [])
hashes = []
for row in assets:
    path = SOURCE / row["file"]
    if not path.is_file() or path.stat().st_size < 500:
        failures.append(f"missing or undersized FBX: {row['file']}")
        continue
    hashes.append({"file": row["file"], "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper()})
blend = SOURCE / manifest.get("source_blend", "")
if not blend.is_file() or blend.stat().st_size < 10_000: failures.append("missing or undersized Blender source")

result = {
    "$schema": "cairnwell/audit/pr010-dimensioned-blockout-source-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_DIMENSIONED_SOURCE_AND_SEMANTIC_EXPORTS__UNREAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_SOURCE_BLOCKOUT__NOT_PROMOTED",
    "source": str(SOURCE.relative_to(ROOT)),
    "asset_count": len(assets),
    "placement_count": len(placements),
    "lane_bed_count": len(lane_beds),
    "carrier_position_count": len(carriers),
    "lane_pylon_count": len(pylons),
    "shuttle_world_x_cm": shuttle_world_x_cm,
    "hashes": hashes,
    "failures": failures,
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({"status": result["status"], "output": str(OUT), "failures": failures}, indent=2))
if failures: raise SystemExit(1)
