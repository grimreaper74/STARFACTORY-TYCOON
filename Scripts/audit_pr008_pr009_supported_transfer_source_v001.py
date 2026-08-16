"""Record the source-only visual gate for the PR-008 to PR-009 supported bridge."""
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SourceAssets/PR009/AutomatedBlankStacker/Interface_v001"
MANIFEST = json.loads((SOURCE / "pr008_pr009_supported_transfer_manifest_v001.json").read_text(encoding="utf-8"))
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_pr009_supported_transfer_source_v001.json"
names = (
    "PR008_PR009_Transfer_v001_isometric.png",
    "PR008_PR009_Transfer_v001_process.png",
    "PR008_PR009_Transfer_v001_service.png",
)
images = []
for name in names:
    path = SOURCE / "Validation" / name
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"Invalid PNG: {path}")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (1600, 900):
        raise RuntimeError(f"Unexpected source render size: {width}x{height}")
    images.append({
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(data).hexdigest().upper(),
        "bytes": len(data), "width": width, "height": height,
    })

if not MANIFEST.get("within_authored_limits") or MANIFEST.get("supported_span_mm") != 2400.0:
    raise RuntimeError("Transfer source manifest does not prove the measured horizontal span")
payload = {
    "$schema": "line-boss/audit/press-shop-pr008-pr009-supported-transfer-source-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SUPPORTED_TRANSFER_SOURCE_DIMENSION_PIVOT_OPEN_MESH_AND_INSTALLATION_DIRECTION_PASS__UNREAL_INTERFACE_RUNTIME_COLLISION_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "source_manifest_status": MANIFEST["status"],
    "images": images,
    "passes": [
        "A separately supported 2400 mm bridge closes the measured planning span without moving either fixed station datum.",
        "Seventeen individually pivoted rollers retain the local-X 0-60 m/min stop/brake-safe contract.",
        "Six floor-supported legs, crossmembers, bearings, drive guarding, services, sensors and open-mesh sides make the interface structurally legible.",
        "The 990 mm roller top is only 10 mm above the upstream evidence and matches the PR-009 receiver source measurement.",
    ],
    "holds": [
        "These are Blender source renders, not Unreal import or runtime evidence.",
        "Guarding partially obscures the process and service close views; Unreal fixed-camera composition must prove management readability.",
        "The identity plate requires diegetic Cairnwell/Moorcross text in Unreal and remains blank in the source render.",
        "Collision, navigation, swept blank transfer, roller motion, isolation, faults and save restore remain unproved.",
    ],
    "decision": "Retain as the source direction for the required PR-008-to-PR-009 supported interface; do not promote.",
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(payload["status"])
