"""Independently verify the copied PR-009 staging package without promoting it."""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGING = Path(r"C:\Users\greg_\Projects\LineBoss_PR009_PR010_Staging")
DEST = ROOT / "SourceAssets/PR009/AutomatedBlankStacker/Candidate_v001"
AUDIT = ROOT / "Saved/Audits/press_shop_pr009_source_intake_v001.json"
MANIFEST = DEST / "CANONICAL_INTAKE_MANIFEST.json"

EXCLUDED_ROOT_DIRS = {"PR010_Source", "PR010_Exports", "PR010_Renders", "PR010_Audits"}

def included(path: Path) -> bool:
    rel = path.relative_to(STAGING)
    return not rel.parts or rel.parts[0] not in EXCLUDED_ROOT_DIRS

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()

source_files = sorted(p for p in STAGING.rglob("*") if p.is_file() and included(p))
if not source_files:
    raise RuntimeError("No PR-009 staging files found")

entries = []
failures = []
for source in source_files:
    rel = source.relative_to(STAGING)
    copied = DEST / rel
    if not copied.is_file():
        failures.append(f"Missing canonical copy: {rel.as_posix()}")
        continue
    source_hash = digest(source)
    copied_hash = digest(copied)
    if source_hash != copied_hash or source.stat().st_size != copied.stat().st_size:
        failures.append(f"Copy mismatch: {rel.as_posix()}")
    entries.append({
        "path": rel.as_posix(),
        "bytes": copied.stat().st_size,
        "sha256": copied_hash,
    })

counts = Counter(Path(e["path"]).suffix.lower() or "<none>" for e in entries)
required_counts = {".blend": 1, ".fbx": 15, ".png": 12}
for suffix, minimum in required_counts.items():
    if counts[suffix] < minimum:
        failures.append(f"Expected at least {minimum} {suffix} files; found {counts[suffix]}")

validation = json.loads((DEST / "PR009_Audits/PR009_SOURCE_VALIDATION_v001.json").read_text(encoding="utf-8"))
exports = json.loads((DEST / "PR009_Audits/PR009_FBX_EXPORT_MANIFEST_v001.json").read_text(encoding="utf-8"))
interface = json.loads((DEST / "PR009_Audits/PR009_INTERFACE_MEASUREMENTS_v001.json").read_text(encoding="utf-8"))
if validation.get("status") != "PASS_NOT_PROMOTED" or validation.get("failures"):
    failures.append("Source validation receipt does not prove a clean source pass")
if exports.get("status") != "SOURCE_EXPORT_PASS__NOT_IMPORTED__NOT_PROMOTED":
    failures.append("FBX export receipt has an unexpected status")
if len(exports.get("files", [])) != 15:
    failures.append("FBX export manifest does not contain exactly 15 files")

old_handoff = json.loads((DEST / "09_HANDOFF_MANIFEST.json").read_text(encoding="utf-8"))
stale_handoff = old_handoff.get("validation", {}).get("unreal_or_source_binary_assets_created") == 0

status = (
    "PR009_SOURCE_PACKAGE_HASH_AND_STRUCTURE_PASS__SOURCE_ONLY__UNREAL_IMPORT_RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
    if not failures else
    "PR009_SOURCE_PACKAGE_INTAKE_FAIL__NOT_PROMOTED"
)
payload = {
    "$schema": "line-boss/audit/press-shop-pr009-source-intake-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": status,
    "source_staging": str(STAGING),
    "canonical_copy": str(DEST.relative_to(ROOT)).replace("\\", "/"),
    "file_count": len(entries),
    "extension_counts": dict(sorted(counts.items())),
    "files": entries,
    "source_receipts": {
        "validation_status": validation.get("status"),
        "export_status": exports.get("status"),
        "interface_status": interface.get("status"),
        "remaining_pr008_pr009_gap_mm": interface.get("remaining_pr008_pr009_gap_mm"),
        "roller_top_delta_vs_upstream_evidence_mm": interface.get("roller_top_delta_vs_upstream_evidence_mm"),
    },
    "warnings": [
        "The root 09_HANDOFF_MANIFEST.json predates the Blender/FBX build and incorrectly says no binary source assets exist. The newer PR009_Audits receipts and this independent manifest supersede that count only.",
        "The 2399.99985 mm unsupported PR-008-to-PR-009 span requires a separately supported transfer; fixed station datums must not be moved to hide it.",
        "Source renders are not Unreal runtime evidence and do not authorize promotion.",
    ] if stale_handoff else [
        "Source renders are not Unreal runtime evidence and do not authorize promotion."
    ],
    "failures": failures,
    "promotion_authorized": False,
}
MANIFEST.write_text(json.dumps(payload, indent=2), encoding="utf-8")
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(status)
if failures:
    raise SystemExit("; ".join(failures))
