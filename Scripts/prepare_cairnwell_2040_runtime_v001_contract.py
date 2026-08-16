"""Freeze the approved Cairnwell v005 authority into an Unreal contract.

Offline standard Python only.  The creation path is deliberately unusable until
the exact v005 winner manifest declares an approved ``unreal_import_authority``
block and a manually authored, visually validated v005 body-paint-mask audit.
The exact v005 manifest path must be supplied explicitly; v006 is evidence only
and can never be selected or reused by this runtime import lane.
It never imports or launches Unreal and never scans or changes Content, Source,
Config, maps, or saves.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
OUTPUT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_contract.json"
OUTPUT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_contract.sha256"
DEST = "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001"
DEST_DISK = PROJECT / "Content/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001"
ACK_TOKEN = "FREEZE_APPROVED_CAIRNWELL_V005_UNREAL_INPUT_CONTRACT_V001"
EXPECTED_ROLES = {
    "BIW_AutomotiveSkeleton",
    "BIW_UnderbodySubset",
    "EmeraldBodyVisualAuthority",
    "EmeraldRollingGearVisualAuthority",
}
EXPECTED_MESH_ASSET_NAMES = {
    "BIW_AutomotiveSkeleton": "SM_LB_C2040_BIW_AutomotiveSkeleton_v001",
    "BIW_UnderbodySubset": "SM_LB_C2040_BIW_UnderbodySubset_v001",
    "EmeraldBodyVisualAuthority": "SM_LB_C2040_EmeraldBodyVisualAuthority_v001",
    "EmeraldRollingGearVisualAuthority": "SM_LB_C2040_EmeraldRollingGearVisualAuthority_v001",
}
EXPECTED_MATERIALS = {
    "body": ("M_LB_C2040_BodyPaintTintPBR_v001", "textured_tint_pbr"),
    "rolling_gear": ("M_LB_C2040_RollingGearPBR_v001", "textured_pbr"),
    "biw_galvanised": ("M_LB_C2040_BIWGalvanized_v001", "solid_pbr"),
    "ed_coat": ("M_LB_C2040_EDCoat_v001", "solid_pbr"),
}
EXPECTED_ROLE_MATERIAL = {
    "BIW_AutomotiveSkeleton": "biw_galvanised",
    "BIW_UnderbodySubset": "ed_coat",
    "EmeraldBodyVisualAuthority": "body",
    "EmeraldRollingGearVisualAuthority": "rolling_gear",
}
EXPECTED_TEXTURE_SEMANTICS = {"base_color", "metallic_roughness", "normal"}
ALLOWED_RECIPES = {"textured_tint_pbr", "textured_pbr", "solid_pbr"}
ALLOWED_COMPRESSIONS = {"TC_DEFAULT", "TC_MASKS", "TC_NORMALMAP"}
EXPECTED_COMPRESSION = {
    "base_color": "TC_DEFAULT",
    "metallic_roughness": "TC_MASKS",
    "normal": "TC_NORMALMAP",
}
LOSSLESS_TEXTURE_SUFFIXES = {".png", ".tga", ".tif", ".tiff", ".exr"}
WINNER_VERSION = "v005"
WINNER_CANDIDATE = "ProductionCandidate_v005"
WINNER_ROOT = PROJECT / (
    "SourceAssets/Candidate/Vehicles/Cairnwell2040/FinishedVehicleRuntimeDerivative_v001/"
    "ProductionCandidate_v005"
)
EXPECTED_MANIFEST = WINNER_ROOT / "MANIFEST_v005.json"
PENDING_MARKER = WINNER_ROOT / "PENDING_ROOT_VISUAL_APPROVAL_DO_NOT_PROMOTE.md"
SUPERSESSION_RECORD = (
    WINNER_ROOT / "Audit/Cairnwell2040_v005_FinalApprovalSupersession.json"
)
SUPERSESSION_SCHEMA = "lineboss.cairnwell2040.v005.final-approval-supersession.v1"
SUPERSESSION_STATUS = (
    "APPROVED__V005_MANUAL_MASK_SUPERSEDES_HISTORICAL_DO_NOT_PROMOTE_WITHOUT_DELETION"
)
STALE_FREEZE_RECEIPT = (
    WINNER_ROOT / "Audit/Cairnwell2040_v005_AdditiveFreezeReceipt.json"
)
FREEZE_AMENDMENT_RECORD = (
    WINNER_ROOT / "Audit/Cairnwell2040_v005_AdditiveFreezeReceipt_v002.json"
)
FREEZE_AMENDMENT_SCHEMA = (
    "lineboss.cairnwell2040.v005.additive-freeze-amendment.v2"
)
FREEZE_AMENDMENT_STATUS = (
    "PASS__V005_ADDITIVE_FREEZE_RECEIPT_V002__CURRENT_CONTRACT_AUTHORITY__"
    "SOLE_SCHEMA_KEY_CORRECTION"
)
FREEZE_AMENDMENT_SHA256 = (
    "7BCE6A5A1DF2C0080011D8EB78D24C5839B44A4755F65FD2939F0E562D75A4A0"
)
FREEZE_AMENDMENT_BYTES = 24420
STALE_FREEZE_RECEIPT_SHA256 = (
    "F7C761D794F44E7EEEBB2958A7947F63D59D0EE828510E1803D7B69EA62642F0"
)
STALE_FREEZE_RECEIPT_BYTES = 24570
CURRENT_SUPERSESSION_SHA256 = (
    "738E19C3D1D07028C0F2C107AD023F14DBC94FD44DAE2107411D6C8A317A348C"
)
CURRENT_SUPERSESSION_BYTES = 3319
STALE_V1_SUPERSESSION_SHA256 = (
    "8E40E4ED420A7F343B8678562D8D38058EAFA72001007F9249AEA97718DE0B98"
)
FREEZE_AMENDMENT_PREEXISTING_COUNT = 36
FREEZE_AMENDMENT_SOLE_CHANGE = (
    "JSON key `schema` corrected to `$schema`; value and every other "
    "semantic/evidence field retained."
)
EXPECTED_SUPERSESSION_EVIDENCE = {
    "historical_do_not_promote_marker": PENDING_MARKER,
    "approved_manifest": EXPECTED_MANIFEST,
    "manual_paint_mask_audit": (
        WINNER_ROOT / "Audit/Cairnwell2040_v005_ManualPaintMask_Audit.json"
    ),
    "manual_paint_mask_texture": (
        WINNER_ROOT / "Textures/T_LB_C2040_Emerald_MR_BodyPaintMaskA_v005.png"
    ),
}
EXPECTED_SUPERSESSION_RENDERS = {
    name: WINNER_ROOT / (
        "Renders/PaintMaskAuthority_v005/"
        f"Cairnwell2040_v005_ManualPaintMask_{name}.png"
    )
    for name in ("front", "hero", "rear", "side")
}
PAINT_MASK_STATUS = "APPROVED__MANUALLY_AUTHORED_V005_BODY_PAINT_MASK__VISUALLY_VALIDATED"


class ContractError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT).as_posix()
    except ValueError as exc:
        raise ContractError(f"authority path escapes project: {path}") from exc


def source_row(path: Path, expected_sha256: str | None = None,
               expected_bytes: int | None = None,
               require_expected: bool = False) -> dict:
    if not path.is_file():
        raise ContractError(f"required approved source file missing: {path}")
    expected_hash = str(expected_sha256 or "").upper()
    if require_expected and (
            len(expected_hash) != 64
            or any(character not in "0123456789ABCDEF" for character in expected_hash)
            or expected_bytes is None
            or int(expected_bytes) <= 0):
        raise ContractError(f"approved manifest lacks exact hash/byte authority: {path}")
    actual_sha = sha256(path)
    actual_bytes = path.stat().st_size
    if expected_hash and actual_sha != expected_hash:
        raise ContractError(f"approved source hash drift: {path}")
    if expected_bytes is not None and actual_bytes != int(expected_bytes):
        raise ContractError(f"approved source size drift: {path}")
    return {"path": project_relative(path), "sha256": actual_sha, "bytes": actual_bytes}


def validate_freeze_amendment() -> dict:
    """Prove the preserved stale receipt -> corrected supersession -> v002 chain."""
    if not FREEZE_AMENDMENT_RECORD.is_file():
        raise ContractError("final v005 additive-freeze v002 amendment is absent")
    try:
        payload = json.loads(FREEZE_AMENDMENT_RECORD.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError("final v005 additive-freeze v002 amendment is unreadable") from exc
    if not isinstance(payload, dict):
        raise ContractError("final v005 additive-freeze v002 amendment must be a JSON object")

    amendment_row = source_row(
        FREEZE_AMENDMENT_RECORD,
        FREEZE_AMENDMENT_SHA256,
        FREEZE_AMENDMENT_BYTES,
        require_expected=True,
    )
    stale_row = source_row(
        STALE_FREEZE_RECEIPT,
        STALE_FREEZE_RECEIPT_SHA256,
        STALE_FREEZE_RECEIPT_BYTES,
        require_expected=True,
    )
    current_supersession_row = source_row(
        SUPERSESSION_RECORD,
        CURRENT_SUPERSESSION_SHA256,
        CURRENT_SUPERSESSION_BYTES,
        require_expected=True,
    )

    stale_relative = STALE_FREEZE_RECEIPT.resolve().relative_to(WINNER_ROOT.resolve()).as_posix()
    amendment_relative = (
        FREEZE_AMENDMENT_RECORD.resolve().relative_to(WINNER_ROOT.resolve()).as_posix()
    )
    supersession_relative = (
        SUPERSESSION_RECORD.resolve().relative_to(WINNER_ROOT.resolve()).as_posix()
    )

    def receipt_row_matches(row: object, relative: str,
                            expected_sha: str, expected_bytes: int) -> bool:
        return (isinstance(row, dict)
                and set(row) == {"path", "sha256", "bytes"}
                and row.get("path") == relative
                and str(row.get("sha256", "")).upper() == expected_sha
                and int(row.get("bytes", -1)) == expected_bytes)

    incident = payload.get("declared_post_v1_incident", {})
    expected_changed = {
        supersession_relative: {
            "current": {
                "bytes": CURRENT_SUPERSESSION_BYTES,
                "sha256": CURRENT_SUPERSESSION_SHA256,
            },
            "v1": {
                "bytes": CURRENT_SUPERSESSION_BYTES,
                "sha256": STALE_V1_SUPERSESSION_SHA256,
            },
        }
    }
    if (payload.get("$schema") != FREEZE_AMENDMENT_SCHEMA
            or payload.get("status") != FREEZE_AMENDMENT_STATUS
            or payload.get("selected_candidate") != WINNER_CANDIDATE
            or payload.get("selected_version") != WINNER_VERSION
            or payload.get("current_contract_authority") is not True
            or payload.get("supersedes_stale_v1_receipt_without_modifying_it") is not True
            or payload.get("unreal_import_or_promotion_performed") is not False
            or payload.get("stale_v1_receipt_expected_sha256")
            != STALE_FREEZE_RECEIPT_SHA256
            or payload.get("self_excluded_from_inventory") != amendment_relative
            or payload.get("self_exclusion_reason") != (
                "A content-addressed receipt cannot include its own final hash without circularity."
            )
            or not receipt_row_matches(
                payload.get("stale_v1_receipt"), stale_relative,
                STALE_FREEZE_RECEIPT_SHA256, STALE_FREEZE_RECEIPT_BYTES)
            or not receipt_row_matches(
                payload.get("current_supersession"), supersession_relative,
                CURRENT_SUPERSESSION_SHA256, CURRENT_SUPERSESSION_BYTES)
            or not isinstance(incident, dict)
            or incident.get("changed_path") != supersession_relative
            or incident.get("current_expected_bytes") != CURRENT_SUPERSESSION_BYTES
            or incident.get("current_expected_sha256") != CURRENT_SUPERSESSION_SHA256
            or incident.get("current_state") != {
                "bytes": CURRENT_SUPERSESSION_BYTES,
                "sha256": CURRENT_SUPERSESSION_SHA256,
            }
            or incident.get("v1_pinned_state") != {
                "bytes": CURRENT_SUPERSESSION_BYTES,
                "sha256": STALE_V1_SUPERSESSION_SHA256,
            }
            or incident.get("sole_change") != FREEZE_AMENDMENT_SOLE_CHANGE
            or payload.get("post_v1_changed_files") != expected_changed
            or payload.get("post_v1_changed_files_except_declared_schema_key") != []
            or payload.get("post_v1_missing_files") != []
            or payload.get("post_v1_unexpected_additions") != []
            or payload.get("changed_preexisting_files") != []):
        raise ContractError("final v005 additive-freeze v002 amendment identity/chain drift")

    before = payload.get("preexisting_inventory_before")
    after = payload.get("preexisting_inventory_after")
    final_inventory = payload.get("final_authority_and_additive_inventory")
    if (not isinstance(before, dict)
            or before != after
            or len(before) != FREEZE_AMENDMENT_PREEXISTING_COUNT
            or payload.get("preexisting_file_count") != FREEZE_AMENDMENT_PREEXISTING_COUNT
            or not isinstance(final_inventory, dict)
            or amendment_relative in final_inventory):
        raise ContractError("final v005 additive-freeze v002 amendment no-other-drift proof drift")

    verified: dict[str, dict] = {}

    def verify_inventory(inventory: dict, label: str) -> None:
        for relative, expected in inventory.items():
            candidate = (WINNER_ROOT / relative).resolve()
            try:
                candidate.relative_to(WINNER_ROOT.resolve())
            except ValueError as exc:
                raise ContractError(f"{label} path escapes exact v005 winner root: {relative}") from exc
            if (not isinstance(expected, dict)
                    or set(expected) != {"bytes", "sha256"}):
                raise ContractError(f"{label} row schema drift: {relative}")
            expected_simple = {
                "bytes": int(expected.get("bytes", -1)),
                "sha256": str(expected.get("sha256", "")).upper(),
            }
            cached = verified.get(relative)
            if cached is not None:
                if cached != expected_simple:
                    raise ContractError(f"{label} duplicate authority row drift: {relative}")
                continue
            actual = source_row(
                candidate,
                expected_simple["sha256"],
                expected_simple["bytes"],
                require_expected=True,
            )
            verified[relative] = {
                "bytes": actual["bytes"],
                "sha256": actual["sha256"],
            }

    verify_inventory(before, "v002 preexisting no-drift inventory")
    verify_inventory(final_inventory, "v002 final additive authority inventory")
    required_final = {
        stale_relative,
        supersession_relative,
        EXPECTED_MANIFEST.resolve().relative_to(WINNER_ROOT.resolve()).as_posix(),
        EXPECTED_SUPERSESSION_EVIDENCE["manual_paint_mask_audit"].resolve()
        .relative_to(WINNER_ROOT.resolve()).as_posix(),
        EXPECTED_SUPERSESSION_EVIDENCE["manual_paint_mask_texture"].resolve()
        .relative_to(WINNER_ROOT.resolve()).as_posix(),
        *(path.resolve().relative_to(WINNER_ROOT.resolve()).as_posix()
          for path in EXPECTED_SUPERSESSION_RENDERS.values()),
    }
    if not required_final.issubset(final_inventory):
        raise ContractError("final v005 additive-freeze v002 amendment authority closure drift")

    return {
        "schema": FREEZE_AMENDMENT_SCHEMA,
        "status": FREEZE_AMENDMENT_STATUS,
        "selected_candidate": WINNER_CANDIDATE,
        "selected_version": WINNER_VERSION,
        "current_contract_authority": True,
        "supersedes_stale_v1_receipt_without_modifying_it": True,
        "unreal_import_or_promotion_performed": False,
        "record": amendment_row,
        "stale_v1_receipt": stale_row,
        "current_supersession": current_supersession_row,
        "declared_post_v1_incident": incident,
        "preexisting_file_count": FREEZE_AMENDMENT_PREEXISTING_COUNT,
        "final_authority_and_additive_inventory_count": len(final_inventory),
        "no_missing_files": True,
        "no_unexpected_additions": True,
        "no_other_changed_files": True,
    }


def validate_approval_supersession(manifest_path: Path) -> dict:
    if manifest_path.resolve() != EXPECTED_MANIFEST.resolve():
        raise ContractError("approval supersession may name only exact v005 MANIFEST_v005.json")
    if not PENDING_MARKER.is_file():
        raise ContractError("historical v005 do-not-promote marker must remain preserved byte-exact")
    if not SUPERSESSION_RECORD.is_file():
        raise ContractError("final v005 approval-supersession record is absent")
    try:
        payload = json.loads(SUPERSESSION_RECORD.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError("final v005 approval-supersession record is unreadable") from exc
    if not isinstance(payload, dict):
        raise ContractError("final v005 approval-supersession record must be a JSON object")
    root_visual = payload.get("root_visual_approval", {})
    if (payload.get("$schema") != SUPERSESSION_SCHEMA
            or payload.get("status") != SUPERSESSION_STATUS
            or payload.get("selected_candidate") != WINNER_CANDIDATE
            or payload.get("selected_version") != WINNER_VERSION
            or payload.get("historical_marker_preserved_byte_exact") is not True
            or payload.get("supersedes_historical_marker_without_deletion") is not True
            or payload.get("unreal_import_or_promotion_performed") is not False
            or not isinstance(root_visual, dict)
            or root_visual.get("status") != "PASS"
            or int(root_visual.get("visible_isolated_false_positive_regions", -1)) != 0
            or root_visual.get("painted_roof_and_body_included") is not True
            or root_visual.get(
                "glazing_lamps_trim_diffuser_and_wheels_excluded") is not True):
        raise ContractError("final v005 approval-supersession identity/status drift")
    evidence_raw = payload.get("evidence")
    renders_raw = payload.get("manual_paint_mask_renders")
    if (not isinstance(evidence_raw, dict)
            or set(evidence_raw) != set(EXPECTED_SUPERSESSION_EVIDENCE)
            or not isinstance(renders_raw, dict)
            or set(renders_raw) != set(EXPECTED_SUPERSESSION_RENDERS)):
        raise ContractError("final v005 approval-supersession evidence closure drift")

    def exact_evidence_row(label: str, path: Path, row: dict) -> dict:
        if not isinstance(row, dict) or row.get("path") != project_relative(path):
            raise ContractError(f"approval-supersession path drift: {label}")
        return source_row(
            path, row.get("sha256"), row.get("bytes"), require_expected=True)

    evidence = {
        label: exact_evidence_row(label, path, evidence_raw[label])
        for label, path in EXPECTED_SUPERSESSION_EVIDENCE.items()
    }
    renders = {
        label: exact_evidence_row(label, path, renders_raw[label])
        for label, path in EXPECTED_SUPERSESSION_RENDERS.items()
    }
    freeze_amendment = validate_freeze_amendment()
    return {
        "status": SUPERSESSION_STATUS,
        "selected_candidate": WINNER_CANDIDATE,
        "selected_version": WINNER_VERSION,
        "historical_marker_preserved_byte_exact": True,
        "supersedes_historical_marker_without_deletion": True,
        "unreal_import_or_promotion_performed": False,
        "root_visual_approval": {
            "status": "PASS",
            "visible_isolated_false_positive_regions": 0,
            "painted_roof_and_body_included": True,
            "glazing_lamps_trim_diffuser_and_wheels_excluded": True,
        },
        "record": source_row(SUPERSESSION_RECORD),
        "evidence": evidence,
        "manual_paint_mask_renders": renders,
        "freeze_amendment": freeze_amendment,
    }


def as_vector(value, field: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ContractError(f"{field} must contain exactly three coordinates")
    result = [round(float(item), 6) for item in value]
    if any(not math.isfinite(item) for item in result):
        raise ContractError(f"{field} must contain only finite coordinates")
    if any(abs(item) > 100000.0 for item in result):
        raise ContractError(f"{field} is outside the bounded centimetre contract")
    return result


def object_record(folder: str, asset_name: str) -> dict:
    if not asset_name or "/" in asset_name or "." in asset_name:
        raise ContractError(f"invalid Unreal asset name: {asset_name!r}")
    package = f"{DEST}/{folder}/{asset_name}"
    return {
        "asset_name": asset_name,
        "package_path": package,
        "object_path": f"{package}.{asset_name}",
        "disk_path": "Content/" + package.removeprefix("/Game/") + ".uasset",
    }


def normalise_module(role: str, spec: dict) -> dict:
    if str(spec.get("asset_name", "")) != EXPECTED_MESH_ASSET_NAMES[role]:
        raise ContractError(
            f"{role} must use frozen runtime name {EXPECTED_MESH_ASSET_NAMES[role]}"
        )
    record = object_record("Meshes", str(spec.get("asset_name", "")))
    lods = spec.get("lods")
    if not isinstance(lods, list) or [row.get("lod") for row in lods] != [0, 1, 2]:
        raise ContractError(f"{role} must declare authored LOD0/1/2 in order")
    normalised_lods = []
    for index, lod in enumerate(lods):
        source = (PROJECT / str(lod.get("fbx_path", ""))).resolve()
        if source.suffix.casefold() != ".fbx":
            raise ContractError(f"{role}:LOD{index} must use an authored FBX source")
        slots = lod.get("material_slots")
        if not isinstance(slots, list) or not slots or any(not str(slot) for slot in slots):
            raise ContractError(f"{role}:LOD{index} lacks exact semantic material slots")
        minimum = as_vector(lod.get("bounds_min_cm"), f"{role}:LOD{index}:bounds_min_cm")
        maximum = as_vector(lod.get("bounds_max_cm"), f"{role}:LOD{index}:bounds_max_cm")
        pivot = as_vector(lod.get("pivot_cm"), f"{role}:LOD{index}:pivot_cm")
        if max(abs(value) for value in pivot) > 0.01:
            raise ContractError(f"{role}:LOD{index} does not share the zero vehicle datum")
        dimensions = [round(maximum[axis] - minimum[axis], 6) for axis in range(3)]
        if min(dimensions) <= 0.0:
            raise ContractError(f"{role}:LOD{index} has invalid bounds")
        triangles = int(lod.get("triangles", 0))
        vertices = int(lod.get("vertices", 0))
        uv_channels = int(lod.get("uv_channels", 0))
        degenerates = int(lod.get("degenerate_triangles", -1))
        if triangles <= 0 or vertices <= 0 or uv_channels not in (0, 1) or degenerates != 0:
            raise ContractError(f"{role}:LOD{index} triangle/vertex/UV/degenerate gate failed")
        normalised_lods.append({
            "lod": index,
            "source": source_row(
                source, lod.get("sha256"), lod.get("bytes"), require_expected=True),
            "triangles": triangles,
            # FBX source vertices are pinned as source evidence only. Unreal may
            # deterministically split render vertices at normals/UV/material
            # seams, so the runtime gate requires a positive imported count but
            # does not pretend Blender and Unreal vertex counts are identical.
            "source_vertices": vertices,
            "uv_channels": uv_channels,
            "degenerate_triangles": degenerates,
            "material_slots": [str(slot) for slot in slots],
            "expected_unreal_bounds": {
                "minimum_cm": minimum,
                "maximum_cm": maximum,
                "dimensions_cm": dimensions,
                "pivot_cm": pivot,
            },
        })
    chain = [row["triangles"] for row in normalised_lods]
    if not chain[0] > chain[1] > chain[2] > 0:
        raise ContractError(f"{role} lacks a strict descending authored LOD chain")
    if any(row["material_slots"] != normalised_lods[0]["material_slots"]
           for row in normalised_lods[1:]):
        raise ContractError(f"{role} material-slot order differs across authored LODs")
    bindings = spec.get("material_bindings")
    if not isinstance(bindings, dict) or set(bindings) != set(normalised_lods[0]["material_slots"]):
        raise ContractError(f"{role} does not bind every exact semantic slot once")
    closed_body_shell = bool(spec.get("closed_body_shell", False))
    semantic_object_count = int(spec.get("semantic_object_count", 0))
    if role == "EmeraldBodyVisualAuthority" and not closed_body_shell:
        raise ContractError("EmeraldBodyVisualAuthority must be the approved closed body shell")
    if role == "EmeraldRollingGearVisualAuthority" and semantic_object_count != 8:
        raise ContractError("EmeraldRollingGearVisualAuthority must close four tyres plus four rims")
    record.update({
        "role": role,
        "lods": normalised_lods,
        "triangle_chain": chain,
        "material_slots": normalised_lods[0]["material_slots"],
        "material_bindings": {str(key): str(value) for key, value in bindings.items()},
        "nanite_enabled": False,
        "collision": {"simple_count": 0, "convex_count": 0,
                      "trace_flag": "CTF_USE_SIMPLE_AS_COMPLEX"},
        "has_navigation_data": False,
        "closed_body_shell": closed_body_shell,
        "semantic_object_count_before_combined_import": semantic_object_count,
    })
    return record


def normalise_texture(semantic: str, spec: dict) -> dict:
    record = object_record("Textures", str(spec.get("asset_name", "")))
    source = (PROJECT / str(spec.get("source_path", ""))).resolve()
    width, height = int(spec.get("width", 0)), int(spec.get("height", 0))
    channels = int(spec.get("channels", 0))
    source_colorspace = str(spec.get("source_colorspace", ""))
    compression = str(spec.get("compression", ""))
    if width != 2048 or height != 2048:
        raise ContractError(f"{semantic} must retain its approved 2048x2048 source image")
    if compression not in ALLOWED_COMPRESSIONS:
        raise ContractError(f"{semantic} has unsupported texture compression: {compression}")
    if compression != EXPECTED_COMPRESSION[semantic]:
        raise ContractError(f"{semantic} exact Unreal compression contract drift")
    if source.suffix.casefold() not in LOSSLESS_TEXTURE_SUFFIXES:
        raise ContractError(f"{semantic} must use the approved standalone lossless source")
    channel_mapping = spec.get("channel_mapping")
    if not isinstance(channel_mapping, dict) or not channel_mapping:
        raise ContractError(f"{semantic} lacks exact channel mapping metadata")
    channel_mapping = {
        str(channel).upper(): str(meaning) for channel, meaning in channel_mapping.items()
    }
    record.update({
        "semantic": semantic,
        "source": source_row(
            source, spec.get("sha256"), spec.get("bytes"), require_expected=True),
        "width": width,
        "height": height,
        "channels": channels,
        "source_colorspace": source_colorspace,
        "srgb": bool(spec.get("srgb")),
        "compression": compression,
        "flip_green_channel": bool(spec.get("flip_green_channel", False)),
        "channel_mapping": channel_mapping,
    })
    if semantic == "base_color" and not record["srgb"]:
        raise ContractError("base_color must be sRGB")
    if semantic != "base_color" and record["srgb"]:
        raise ContractError(f"{semantic} must be non-colour data")
    if semantic == "base_color":
        if source_colorspace != "sRGB" or channels not in (3, 4):
            raise ContractError("base_color lossless source colours/channels drift")
    elif source_colorspace != "Non-Color":
        raise ContractError(f"{semantic} source colorspace must be Non-Color")
    if semantic == "metallic_roughness" and channels != 4:
        raise ContractError("packed metallic/roughness/body-mask source must retain RGBA")
    if semantic == "normal":
        normal_convention = str(spec.get("normal_convention", ""))
        if normal_convention not in {"OpenGL", "DirectX"}:
            raise ContractError("normal source convention must be explicit OpenGL or DirectX")
        if channels not in (3, 4):
            raise ContractError("normal lossless source channel count drift")
        if bool(record["flip_green_channel"]) != (normal_convention == "OpenGL"):
            raise ContractError("normal convention/Unreal green-channel conversion mismatch")
        record["normal_convention"] = normal_convention
    expected_channels = {
        "base_color": {"RGB": "base_color"},
        "metallic_roughness": {
            "G": "roughness",
            "B": "metallic",
            "A": "BodyPaintMask",
        },
        "normal": {"RGB": "tangent_space_normal"},
    }[semantic]
    for channel, meaning in expected_channels.items():
        if record["channel_mapping"].get(channel, "").casefold() != meaning.casefold():
            raise ContractError(f"{semantic} exact {channel} channel meaning drift")
    return record


def normalise_material(key: str, spec: dict, textures: dict) -> dict:
    if key not in EXPECTED_MATERIALS:
        raise ContractError(f"unexpected runtime material key: {key}")
    expected_asset_name, expected_recipe = EXPECTED_MATERIALS[key]
    if str(spec.get("asset_name", "")) != expected_asset_name:
        raise ContractError(f"{key} must use frozen runtime name {expected_asset_name}")
    record = object_record("Materials", str(spec.get("asset_name", "")))
    recipe = str(spec.get("recipe", ""))
    slot_name = str(spec.get("slot_name", ""))
    if recipe not in ALLOWED_RECIPES or recipe != expected_recipe or not slot_name:
        raise ContractError(f"{key} has an invalid recipe or semantic slot")
    record.update({"material_key": key, "slot_name": slot_name, "recipe": recipe})
    if recipe in {"textured_tint_pbr", "textured_pbr"}:
        texture_semantics = spec.get("texture_semantics")
        if set(texture_semantics or []) != EXPECTED_TEXTURE_SEMANTICS:
            raise ContractError(f"{key} textured recipe does not close all three Emerald maps")
        record["texture_semantics"] = list(texture_semantics)
        record["texture_object_paths"] = {
            semantic: textures[semantic]["object_path"] for semantic in texture_semantics
        }
        record["metallic_channel"] = str(spec.get("metallic_channel", ""))
        record["roughness_channel"] = str(spec.get("roughness_channel", ""))
        if record["metallic_channel"] not in "RGBA" or record["roughness_channel"] not in "RGBA":
            raise ContractError(f"{key} lacks exact packed metallic/roughness channels")
        if (record["metallic_channel"] != "B"
                or record["roughness_channel"] != "G"):
            raise ContractError(f"{key} must preserve PackedMR.B metallic / G roughness")
        if recipe == "textured_tint_pbr":
            record["parameter_name"] = str(spec.get("parameter_name", ""))
            record["parameter_output"] = "RGB"
            record["detail_luminance_weights"] = [0.2126, 0.7152, 0.0722]
            record["detail_normalization"] = 1.35
            record["detail_clamp_min"] = 0.35
            record["detail_clamp_max"] = 1.15
            record["default_paint_colour_linear"] = as_vector(
                spec.get("default_paint_colour_linear"),
                f"{key}:default_paint_colour_linear",
            )
            if any(value < 0.0 or value > 1.0
                   for value in record["default_paint_colour_linear"]):
                raise ContractError("body default paint colour must remain within linear [0,1]")
            record["paint_mask_texture_semantic"] = str(
                spec.get("paint_mask_texture_semantic", ""))
            record["paint_mask_channel"] = str(spec.get("paint_mask_channel", ""))
            record["paint_mask_target_input"] = "Alpha"
            record["tint_graph_topology"] = (
                "Lerp(BaseColor.RGB,VehiclePaintColour.RGB*"
                "Clamp(Dot(BaseColor.RGB,LinearLuminanceWeights)*1.35,0.35,1.15),"
                "metallic_roughness.A)->BaseColor"
            )
            if (record["parameter_name"] != "VehiclePaintColour"
                    or record["paint_mask_texture_semantic"] != "metallic_roughness"
                    or record["paint_mask_channel"] != "A"
                    or textures["metallic_roughness"]["channel_mapping"].get(
                        "A", "").casefold() != "bodypaintmask"):
                raise ContractError(
                    "body tint must use VehiclePaintColour through PackedMR.A BodyPaintMask"
                )
    else:
        record["base_color_linear"] = as_vector(
            spec.get("base_color_linear"), f"{key}:base_color_linear")
        if any(value < 0.0 or value > 1.0 for value in record["base_color_linear"]):
            raise ContractError(f"{key} base colour must remain within linear [0,1]")
        record["metallic"] = float(spec.get("metallic"))
        record["roughness"] = float(spec.get("roughness"))
        if not 0.0 <= record["metallic"] <= 1.0 or not 0.0 <= record["roughness"] <= 1.0:
            raise ContractError(f"{key} scalar material values are outside [0,1]")
        record["texture_semantics"] = []
        record["texture_object_paths"] = {}
    return record


def build_payload(manifest: dict, manifest_path: Path) -> dict:
    approval_supersession = validate_approval_supersession(manifest_path)
    authority = manifest.get("unreal_import_authority")
    if not isinstance(authority, dict):
        raise ContractError("final manifest lacks unreal_import_authority")
    if authority.get("approval_status") != "APPROVED_FOR_GUARDED_UNREAL_IMPORT":
        raise ContractError("selected authority has not received final visual/import approval")
    selected_candidate = str(authority.get("selected_candidate", "")).strip()
    selected_version = str(authority.get("selected_version", "")).strip()
    if not selected_candidate or not selected_version:
        raise ContractError("final authority lacks selected_candidate/selected_version identity")
    if selected_version != WINNER_VERSION or selected_candidate != WINNER_CANDIDATE:
        raise ContractError("selected authority must identify the approved v005 winner exactly")
    if manifest_path.resolve() != EXPECTED_MANIFEST.resolve():
        raise ContractError("selected manifest path must be exact v005 winner MANIFEST_v005.json")
    if "native" in (selected_candidate + " " + selected_version).casefold():
        raise ContractError("selected authority provenance must not be labelled Native")
    paint_mask_raw = authority.get("paint_mask_authority")
    if not isinstance(paint_mask_raw, dict):
        raise ContractError("v005 authority lacks the manual body-paint-mask approval block")
    paint_mask_audit_path = (PROJECT / str(paint_mask_raw.get("audit_path", ""))).resolve()
    try:
        paint_mask_audit_path.relative_to(WINNER_ROOT.resolve())
    except ValueError as exc:
        raise ContractError("manual v005 paint-mask audit escapes the v005 winner root") from exc
    if (paint_mask_raw.get("status") != PAINT_MASK_STATUS
            or paint_mask_raw.get("selected_version") != WINNER_VERSION
            or paint_mask_raw.get("texture_semantic") != "metallic_roughness"
            or paint_mask_raw.get("channel") != "A"
            or paint_mask_raw.get("manual_authored") is not True
            or paint_mask_raw.get("v006_mask_reused") is not False
            or int(paint_mask_raw.get("false_positive_fragment_count", -1)) != 0):
        raise ContractError("manual v005 paint-mask identity/validation/false-positive gate failed")
    paint_mask_authority = {
        "status": PAINT_MASK_STATUS,
        "selected_version": WINNER_VERSION,
        "texture_semantic": "metallic_roughness",
        "channel": "A",
        "manual_authored": True,
        "v006_mask_reused": False,
        "false_positive_fragment_count": 0,
        "audit": source_row(
            paint_mask_audit_path,
            paint_mask_raw.get("audit_sha256"),
            paint_mask_raw.get("audit_bytes"),
            require_expected=True,
        ),
    }
    shared = authority.get("shared_datum", {})
    if (shared.get("forward_axis") != "+X" or shared.get("up_axis") != "+Z"
            or as_vector(shared.get("pivot_cm"), "shared_datum:pivot_cm") != [0.0, 0.0, 0.0]):
        raise ContractError("shared vehicle datum/axis contract drift")
    modules_raw = authority.get("modules")
    if not isinstance(modules_raw, dict) or set(modules_raw) != EXPECTED_ROLES:
        raise ContractError("final manifest must declare exactly the four approved runtime modules")
    textures_raw = authority.get("textures")
    if not isinstance(textures_raw, dict) or set(textures_raw) != EXPECTED_TEXTURE_SEMANTICS:
        raise ContractError("final manifest must declare the exact three-image Emerald closure")
    textures = {key: normalise_texture(key, value) for key, value in textures_raw.items()}
    if (approval_supersession["evidence"]["approved_manifest"]
            != source_row(manifest_path)
            or approval_supersession["evidence"]["manual_paint_mask_audit"]
            != paint_mask_authority["audit"]
            or approval_supersession["evidence"]["manual_paint_mask_texture"]
            != textures["metallic_roughness"]["source"]):
        raise ContractError("final supersession does not bind the selected manifest/manual mask closure")
    materials_raw = authority.get("materials")
    if not isinstance(materials_raw, dict) or set(materials_raw) != set(EXPECTED_MATERIALS):
        raise ContractError("final manifest must declare exactly four runtime material recipes")
    materials = {key: normalise_material(key, value, textures)
                 for key, value in materials_raw.items()}
    modules = {key: normalise_module(key, value) for key, value in modules_raw.items()}
    module_fbx_paths = [
        lod["source"]["path"] for module in modules.values() for lod in module["lods"]
    ]
    if len(module_fbx_paths) != 12 or len(set(module_fbx_paths)) != 12:
        raise ContractError("runtime authority must provide 12 distinct role/LOD FBX sources")
    texture_source_paths = [texture["source"]["path"] for texture in textures.values()]
    if len(texture_source_paths) != 3 or len(set(texture_source_paths)) != 3:
        raise ContractError("runtime authority must provide three distinct texture source files")
    winner_root_relative = project_relative(WINNER_ROOT).rstrip("/") + "/"
    if not textures["metallic_roughness"]["source"]["path"].startswith(
            winner_root_relative):
        raise ContractError("manual v005 PackedMR/body-mask source must reside in v005 winner root")
    imported_source_paths = module_fbx_paths + texture_source_paths
    if any(not path.startswith(winner_root_relative) for path in imported_source_paths):
        raise ContractError("every imported runtime source must reside in the exact v005 winner root")
    if any("ProductionCandidate_v006" in path for path in imported_source_paths):
        raise ContractError("approved v005 runtime inputs may not reuse v006 candidate assets")
    material_by_key = {key: value["object_path"] for key, value in materials.items()}
    for role, module in modules.items():
        if set(module["material_bindings"].values()) != {EXPECTED_ROLE_MATERIAL[role]}:
            raise ContractError(
                f"{role} must bind only the frozen {EXPECTED_ROLE_MATERIAL[role]} material authority"
            )
        resolved = {}
        for slot, material_key in module["material_bindings"].items():
            if material_key not in material_by_key:
                raise ContractError(f"{role}:{slot} refers to an undeclared material recipe")
            if materials[material_key]["slot_name"] != slot:
                raise ContractError(f"{role}:{slot} material recipe semantic mismatch")
            if (materials[material_key]["recipe"] in {"textured_tint_pbr", "textured_pbr"}
                    and any(lod["uv_channels"] != 1 for lod in module["lods"])):
                raise ContractError(
                    f"{role}:{slot} uses the textured PBR recipe without exactly one UV channel"
                )
            resolved[slot] = material_by_key[material_key]
        module["material_bindings"] = resolved
    expected_packages = sorted(
        [row["package_path"] for row in modules.values()]
        + [row["package_path"] for row in textures.values()]
        + [row["package_path"] for row in materials.values()],
        key=str.casefold,
    )
    if len(expected_packages) != 11 or len(set(expected_packages)) != 11:
        raise ContractError("runtime closure must be exactly 4 meshes + 3 textures + 4 materials")
    extra_authority_files = []
    for row in authority.get("authority_files", []):
        path = (PROJECT / str(row.get("path", ""))).resolve()
        extra_authority_files.append(source_row(
            path, row.get("sha256"), row.get("bytes"), require_expected=True))
    supersession_sources = [approval_supersession["record"]]
    supersession_sources.extend(approval_supersession["evidence"].values())
    supersession_sources.extend(approval_supersession["manual_paint_mask_renders"].values())
    supersession_sources.extend((
        approval_supersession["freeze_amendment"]["record"],
        approval_supersession["freeze_amendment"]["stale_v1_receipt"],
    ))
    source_files = supersession_sources + [
        source_row(manifest_path), paint_mask_authority["audit"]
    ] + extra_authority_files
    for module in modules.values():
        source_files.extend(lod["source"] for lod in module["lods"])
    source_files.extend(texture["source"] for texture in textures.values())
    source_files = {row["path"]: row for row in source_files}
    lane_files = [
        "Scripts/prepare_cairnwell_2040_runtime_v001_contract.py",
        "Scripts/prepare_cairnwell_2040_runtime_v001_baseline.py",
        "Scripts/cairnwell_2040_runtime_v001.py",
        "Scripts/import_cairnwell_2040_runtime_v001.py",
        "Scripts/validate_cairnwell_2040_runtime_fresh_process_v001.py",
        "Scripts/run_cairnwell_2040_runtime_import_lane_v001.ps1",
        "Scripts/tests/test_cairnwell_2040_runtime_import_lane_v001.py",
        "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_UNREAL_IMPORT_LANE.md",
    ]
    return {
        "$schema": "lineboss/cairnwell-2040-runtime-v001/unreal-import-contract/v1",
        "status": "FROZEN__APPROVED_CAIRNWELL_V005_WINNER__READY_FOR_BASELINE",
        "provenance": {
            "description": (
                f"approved Meshy-derived Cairnwell {selected_candidate} "
                f"{selected_version} modular vehicle authority"
            ),
            "selected_candidate": selected_candidate,
            "selected_version": selected_version,
            "approval_status": authority["approval_status"],
            "manifest_schema": manifest.get("schema", manifest.get("$schema")),
            "manifest": source_row(manifest_path),
            "source_files": [source_files[key] for key in sorted(source_files, key=str.casefold)],
        },
        "destination": {
            "namespace": DEST,
            "disk_root": project_relative(DEST_DISK),
            "must_be_absent_before_run": True,
            "expected_mesh_count": 4,
            "expected_texture_count": 3,
            "expected_material_count": 4,
            "expected_package_count": 11,
            "expected_source_fbx_count": 12,
            "expected_package_paths": expected_packages,
        },
        "shared_datum": {"forward_axis": "+X", "up_axis": "+Z", "pivot_cm": [0.0, 0.0, 0.0]},
        "import_contract": {
            "fresh_only": True,
            "editor_bootstrap_world": "/Engine/Maps/Entry.Entry",
            "project_map_load_save_authorized": False,
            "editor_startup_map_override": (
                "-ini:EditorPerProjectUserSettings:"
                "[/Script/UnrealEd.EditorLoadingSavingSettings]:LoadLevelAtStartup=None"
            ),
            "replace_existing": False,
            "combine_meshes": True,
            "import_materials_from_fbx": False,
            "import_textures_from_fbx": False,
            "import_animations": False,
            "generate_lightmap_uvs": False,
            "auto_generate_collision": False,
            "remove_degenerates": False,
            "nanite_enabled": False,
            "has_navigation_data": False,
            "collision_trace_flag": "CTF_USE_SIMPLE_AS_COMPLEX",
            "lod_screen_sizes": [1.0, 0.35, 0.12],
            "auto_compute_lod_screen_size": False,
            "bounds_tolerance_cm": 0.25,
            "pivot_tolerance_cm": 0.01,
            "exact_texture_material_dependency_closure": True,
        },
        "modules": modules,
        "textures": textures,
        "materials": materials,
        "paint_mask_authority": paint_mask_authority,
        "approval_supersession": approval_supersession,
        "lane_files_to_pin_when_baseline_is_cut": lane_files,
        "policy": {
            "overwrite_reimport_delete_authorized": False,
            "map_load_save_authorized": False,
            "runtime_binding_or_map_promotion_authorized": False,
            "panel_module_namespace_or_packages_authorized": False,
            "automatic_partial_cleanup": False,
            "content_writes_authorized_only_inside_fresh_destination": True,
            "source_config_maps_saves_writes_authorized": False,
            "baseline_must_be_cut_after_contract_freeze_and_before_unreal": True,
        },
    }


def write_contract(manifest_path: Path, acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise ContractError("exact contract-freeze acknowledgement missing")
    if OUTPUT.exists() or OUTPUT_SHA.exists():
        raise ContractError("refusing to overwrite an existing contract or sidecar")
    if DEST_DISK.exists():
        raise ContractError(f"fresh destination already exists: {DEST_DISK}")
    if not manifest_path.is_file():
        raise ContractError(f"final selected-authority manifest is not present: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    payload = build_payload(manifest, manifest_path)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = sha256(OUTPUT)
    OUTPUT_SHA.write_text(f"{digest}  {OUTPUT.name}\n", encoding="ascii")
    print("PASS__CAIRNWELL_2040_V005_UNREAL_INPUT_CONTRACT_FROZEN")
    print(digest)


def verify_contract() -> None:
    if not OUTPUT.is_file() or not OUTPUT_SHA.is_file():
        raise ContractError(
            "contract intentionally absent pending the exact approved v005 manifest and manual mask audit"
        )
    sidecar = OUTPUT_SHA.read_text(encoding="ascii").strip().split()[0].upper()
    if sidecar != sha256(OUTPUT):
        raise ContractError("contract sidecar mismatch")
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    manifest_path = PROJECT / payload["provenance"]["manifest"]["path"]
    rebuilt = build_payload(json.loads(manifest_path.read_text(encoding="utf-8-sig")), manifest_path)
    if payload != rebuilt:
        raise ContractError("approved manifest/source files no longer reproduce the frozen contract")
    print("PASS__CAIRNWELL_2040_V005_UNREAL_INPUT_CONTRACT_REVERIFIED")
    print(sidecar)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--acknowledgement", default="")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify_contract()
    else:
        if args.manifest is None:
            raise ContractError("--manifest must be the exact approved v005 MANIFEST_v005.json")
        write_contract(args.manifest.resolve(), args.acknowledgement)


if __name__ == "__main__":
    main()
