#!/usr/bin/env python3
"""Independently verify and record the immutable canonical PR-009 v002 intake."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
STAGING = Path(r"C:\Users\greg_\Projects\LineBoss_PR009_PR010_Staging")
CANDIDATE = PROJECT / "SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002"
AUDIT_OUT = PROJECT / "Saved/Audits/press_shop_pr009_source_intake_v002.json"
MANIFEST_OUT = CANDIDATE / "CANONICAL_INTAKE_MANIFEST_v002.json"

ROOT_FILES = (
    "01_SOURCE_AUTHORITY_AUDIT.md",
    "02_DIMENSIONED_ASSET_INVENTORY.csv",
    "03_LAYOUT_AND_DATUM_PLAN.json",
    "04_MATERIAL_REQUIREMENTS.json",
    "05_MACHINE_IDENTITY_AND_INTERACTION_MANIFEST.json",
    "06_UNREAL_IMPORT_PLAN.md",
    "07_PRIMARY_TASK_HANDOFF.md",
    "08_VALIDATION_CHECKLIST.md",
    "09_HANDOFF_MANIFEST.json",
    "README.md",
)
SUBTREES = (
    "PR009_Source",
    "PR009_Audits/v002",
    "PR009_Exports/v002_candidate",
    "PR009_Renders/v002",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def selected_files(root: Path) -> list[Path]:
    files = [root / name for name in ROOT_FILES]
    for subtree in SUBTREES:
        base = root / subtree
        if base.exists():
            files.extend(path for path in base.rglob("*") if path.is_file())
    return sorted(files, key=lambda path: path.relative_to(root).as_posix().lower())


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []

    if not STAGING.is_dir():
        failures.append(f"Missing staging root: {STAGING}")
    if not CANDIDATE.is_dir():
        failures.append(f"Missing canonical candidate: {CANDIDATE}")
    if failures:
        records: list[dict] = []
    else:
        staging_files = selected_files(STAGING)
        canonical_files = selected_files(CANDIDATE)
        staging_rel = {path.relative_to(STAGING).as_posix(): path for path in staging_files}
        canonical_rel = {path.relative_to(CANDIDATE).as_posix(): path for path in canonical_files}

        staging_only = sorted(set(staging_rel) - set(canonical_rel))
        canonical_only = sorted(set(canonical_rel) - set(staging_rel))
        if staging_only:
            failures.append(f"Selected files absent from canonical copy: {staging_only}")
        if canonical_only:
            failures.append(f"Unexpected selected files in canonical copy: {canonical_only}")

        records = []
        for relative in sorted(set(staging_rel) & set(canonical_rel)):
            source = staging_rel[relative]
            copy = canonical_rel[relative]
            source_hash = sha256(source)
            copy_hash = sha256(copy)
            matches = source_hash == copy_hash and source.stat().st_size == copy.stat().st_size
            records.append(
                {
                    "relative_path": relative,
                    "bytes": copy.stat().st_size,
                    "sha256": copy_hash,
                    "staging_sha256": source_hash,
                    "matches_staging": matches,
                }
            )
            if not matches:
                failures.append(f"Hash or size mismatch: {relative}")

    blend = CANDIDATE / "PR009_Source/CA_MW_PR009_AutomatedBlankStacker_ProductionSource_v002.blend"
    exports = CANDIDATE / "PR009_Exports/v002_candidate"
    renders = CANDIDATE / "PR009_Renders/v002"
    audit_dir = CANDIDATE / "PR009_Audits/v002"

    if not blend.is_file():
        failures.append("Missing v002 production Blender source")
    export_files = sorted(exports.glob("*.fbx")) if exports.is_dir() else []
    render_files = sorted(renders.glob("*.png")) if renders.is_dir() else []
    if len(export_files) != 19:
        failures.append(f"Expected 19 v002 FBX exports, found {len(export_files)}")
    if len(render_files) != 16:
        failures.append(f"Expected 16 v002 source renders, found {len(render_files)}")

    required_audits = {
        "PR009_COMPLETION_AUDIT_v002.json": "TECHNICAL_SOURCE_PASS__UNREAL_RETEST_REQUIRED__VISUAL_REWORK__NOT_PROMOTED",
        "PR009_DIMENSION_AND_PIVOT_VALIDATION_v002.json": "PASS_NOT_PROMOTED",
        "PR009_FBX_EXPORT_MANIFEST_v002.json": "SOURCE_EXPORT_PASS__INDEPENDENT_REIMPORT_REQUIRED__NOT_PROMOTED",
        "PR009_FBX_REIMPORT_VALIDATION_v002.json": "PASS_NOT_PROMOTED",
        "PR009_FBX_REPRODUCIBILITY_v002.json": "PASS_NOT_PROMOTED",
        "PR009_FBX_UNREAL_CONTRACT_VALIDATION_v002.json": "PASS_NOT_PROMOTED",
        "PR009_INTERFACE_MEASUREMENTS_v002.json": None,
        "PR009_PRODUCTION_SOURCE_VALIDATION_v002.json": "PASS_NOT_PROMOTED",
        "PR009_SK_BINDING_MANIFEST_v002.json": "PASS_NOT_PROMOTED",
        "PR009_SOURCE_RENDER_MANIFEST_v002.json": "FRESH_PRODUCTION_SOURCE_RENDERS_NOT_PROMOTED",
        "PR009_VISUAL_REVIEW_v002.json": "SOURCE_ART_PASS_WITH_REWORK__NOT_PROMOTED",
    }
    audit_statuses: dict[str, str | None] = {}
    for name, expected_status in required_audits.items():
        path = audit_dir / name
        if not path.is_file():
            failures.append(f"Missing required v002 audit: {name}")
            continue
        data = read_json(path)
        status = data.get("status")
        audit_statuses[name] = status
        if expected_status is not None and status != expected_status:
            failures.append(f"Unexpected status in {name}: {status!r}")
        if data.get("promotion_authorized") is True:
            failures.append(f"Source audit improperly authorizes promotion: {name}")
        if data.get("failures"):
            failures.append(f"Source audit contains failures: {name}")

    export_manifest_path = audit_dir / "PR009_FBX_EXPORT_MANIFEST_v002.json"
    if export_manifest_path.is_file():
        export_manifest = read_json(export_manifest_path)
        manifest_files = export_manifest.get("files", [])
        if len(manifest_files) != 19:
            failures.append(f"Export manifest contains {len(manifest_files)} entries, expected 19")
        for entry in manifest_files:
            export_path = exports / entry.get("file", "")
            if not export_path.is_file():
                failures.append(f"Manifest export missing: {entry.get('file')}")
                continue
            if sha256(export_path) != str(entry.get("sha256", "")).upper():
                failures.append(f"Export manifest hash mismatch: {entry.get('file')}")

    handoff_manifest_path = CANDIDATE / "09_HANDOFF_MANIFEST.json"
    handoff_manifest_count = 0
    if not handoff_manifest_path.is_file():
        failures.append("Missing final handoff manifest")
    else:
        handoff_manifest = read_json(handoff_manifest_path)
        declared = handoff_manifest.get("deliverables", [])
        handoff_manifest_count = len(declared)
        if handoff_manifest.get("deliverable_count") != handoff_manifest_count:
            failures.append("Final handoff manifest deliverable count is inconsistent")
        if handoff_manifest.get("summary", {}).get("pr010_started") is not False:
            failures.append("Final handoff manifest does not prove PR-010 remained untouched")
        if handoff_manifest.get("unreal_repository_written") is not False:
            failures.append("Staging task claims it wrote to the canonical Unreal repository")
        if handoff_manifest.get("promotion_authorized") is not False:
            failures.append("Staging task improperly authorizes promotion")
        for entry in declared:
            relative = entry.get("file", "")
            path = CANDIDATE / relative
            if not path.is_file():
                failures.append(f"Final handoff deliverable missing: {relative}")
                continue
            if path.stat().st_size != int(entry.get("bytes", -1)) or sha256(path) != str(entry.get("sha256", "")).upper():
                failures.append(f"Final handoff deliverable hash or size mismatch: {relative}")

    handoff = CANDIDATE / "07_PRIMARY_TASK_HANDOFF.md"
    newest_v002_audit = max(
        (path.stat().st_mtime for path in audit_dir.glob("*.json")),
        default=0,
    )
    handoff_stale_vs_v002 = handoff.is_file() and handoff.stat().st_mtime < newest_v002_audit
    if handoff_stale_vs_v002:
        warnings.append(
            "Root 07_PRIMARY_TASK_HANDOFF.md predates v002 audits; v002 audit files are authoritative for v002 source evidence only."
        )

    status = (
        "CANONICAL_V002_SOURCE_INTAKE_HASH_AND_MANIFEST_PASS__UNREAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures
        else "CANONICAL_V002_SOURCE_INTAKE_FAIL__DO_NOT_IMPORT_OR_PROMOTE"
    )
    result = {
        "$schema": "cairnwell/canonical-intake/pr009-v002/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "promotion_authorized": False,
        "staging_root": str(STAGING),
        "canonical_root": str(CANDIDATE),
        "selected_scope": {"root_files": list(ROOT_FILES), "subtrees": list(SUBTREES)},
        "counts": {
            "verified_files": len(records),
            "v002_fbx_exports": len(export_files),
            "v002_png_renders": len(render_files),
            "final_handoff_manifest_files": handoff_manifest_count,
        },
        "required_audit_statuses": audit_statuses,
        "handoff_stale_vs_v002_audits": handoff_stale_vs_v002,
        "files": records,
        "warnings": warnings,
        "failures": failures,
        "notes": [
            "This intake proves byte identity only for the explicitly selected v002 source scope.",
            "Technical source passes do not constitute Unreal import, runtime, visual or promotion approval.",
            "PR-010 is outside this intake and remains on hold.",
        ],
    }

    AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    for destination in (AUDIT_OUT, MANIFEST_OUT):
        with destination.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")

    print(json.dumps({"status": status, "counts": result["counts"], "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
