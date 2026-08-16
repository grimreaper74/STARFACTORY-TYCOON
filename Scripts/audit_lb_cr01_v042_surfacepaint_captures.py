"""Independently gate the six CR01 v042 Surface Paint screenshot files and logs."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct


REPO = Path(__file__).resolve().parents[1]
SAVED = REPO / "Saved"
OUT = SAVED / "ValidationScreenshots/SupportRobots/CR01/Candidate_v042_SurfacePaint"
AUDIT = SAVED / "Audits/lb_cr01_v042_surfacepaint_capture.json"
CAPTURES = {
    "mothballed_oblique": "LB_CR01_v042_CAM_Mothballed_Oblique",
    "mothballed_left": "LB_CR01_v042_CAM_Mothballed_Left",
    "restored_oblique": "LB_CR01_v042_CAM_Restored_Oblique",
    "restored_right": "LB_CR01_v042_CAM_Restored_Right",
    "restored_front": "LB_CR01_v042_CAM_Restored_Front",
    "restored_top": "LB_CR01_v042_CAM_Restored_Top",
}
BAD_LOG_PATTERNS = (
    "LogMaterial: Error",
    "Failed to compile Material",
    "Default Material will be used",
    "LogPython: Error",
    "Traceback (most recent call last)",
    "Fatal error:",
    "Unhandled Exception",
    "Ensure condition failed",
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def png_dimensions(path):
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return None
    return list(struct.unpack(">II", header[16:24]))


records = []
failures = []
hashes = set()
for capture_id, camera in CAPTURES.items():
    image = OUT / f"lb_cr01_v042_surfacepaint_{capture_id}.png"
    log = SAVED / f"Logs/LB_CR01_v042_SurfacePaintCapture_{capture_id}.log"
    record = {
        "id": capture_id,
        "camera": camera,
        "path": str(image),
        "log": str(log),
        "status": "CAPTURE_FAIL",
    }
    if not image.exists():
        failures.append(f"missing image: {capture_id}")
    else:
        dimensions = png_dimensions(image)
        digest = sha256(image)
        record.update(
            {
                "bytes": image.stat().st_size,
                "dimensions": dimensions,
                "sha256": digest,
            }
        )
        if image.stat().st_size < 100_000:
            failures.append(f"undersized image: {capture_id}")
        if dimensions != [1920, 1080]:
            failures.append(f"wrong dimensions {dimensions}: {capture_id}")
        if digest in hashes:
            failures.append(f"duplicate image hash: {capture_id}")
        hashes.add(digest)
    if not log.exists():
        failures.append(f"missing capture log: {capture_id}")
        record["log_gate_hits"] = ["MISSING_LOG"]
    else:
        log_text = log.read_text(encoding="utf-8", errors="replace")
        hits = [pattern for pattern in BAD_LOG_PATTERNS if pattern in log_text]
        record["log_gate_hits"] = hits
        record["direct_map_confirmed"] = (
            "/Game/LineBoss/Developer/Validation/LB_CR01_Candidate_v042_SurfacePaintTechnical"
            in log_text
        )
        if hits:
            failures.append(f"capture log gate hit {hits}: {capture_id}")
        if not record["direct_map_confirmed"]:
            failures.append(f"direct map not confirmed in log: {capture_id}")
    if not any(capture_id in failure for failure in failures):
        record["status"] = "CAPTURE_TECHNICAL_PASS"
    records.append(record)

passed = not failures and len(records) == len(CAPTURES)
result = {
    "$schema": "line-boss/audit/lb-cr01-v042-surfacepaint-capture",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "FRESH_UNREAL_SCREENSHOTS_TECHNICAL_GATE_PASS__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED"
        if passed
        else "SCREENSHOT_TECHNICAL_GATE_FAIL__NOT_PROMOTED"
    ),
    "map": "/Game/LineBoss/Developer/Validation/LB_CR01_Candidate_v042_SurfacePaintTechnical",
    "resolution": [1920, 1080],
    "captures": records,
    "failures": failures,
    "excluded_non_evidence_attempt": str(SAVED / "Logs/LB_CR01_v042_SurfacePaintCapture.log"),
    "visual_gate_passed": False,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(result["status"])
print(f"captures={len(records)} failures={len(failures)} audit={AUDIT}")
if not passed:
    for failure in failures:
        print(f"FAIL: {failure}")
    raise SystemExit(1)
