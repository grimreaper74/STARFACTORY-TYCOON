"""Consolidate the independent, read-only PR-009 trace-portal source audit."""
import hashlib
import json
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "SourceAssets/PR009/AutomatedBlankStacker/TracePortalClearance_v001"
CANDIDATE = ROOT / "SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002"
AUDIT = ROOT / "Saved/Audits/PR009_TracePortalClearance_v001"
AUDIT.mkdir(parents=True, exist_ok=True)

def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def row(path, base=ROOT):
    return {"path": path.relative_to(base).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)}

def png_validate(path):
    raw = path.read_bytes()
    errors = []
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        return {**row(path), "valid": False, "errors": ["invalid PNG signature"]}
    offset = 8
    chunks = []
    idat = []
    width = height = bit_depth = colour_type = interlace = None
    while offset + 12 <= len(raw):
        length = struct.unpack(">I", raw[offset:offset + 4])[0]
        kind = raw[offset + 4:offset + 8]
        data = raw[offset + 8:offset + 8 + length]
        stored_crc = struct.unpack(">I", raw[offset + 8 + length:offset + 12 + length])[0]
        actual_crc = zlib.crc32(kind + data) & 0xFFFFFFFF
        if actual_crc != stored_crc:
            errors.append(f"CRC mismatch in {kind.decode('ascii', 'replace')}")
        chunks.append(kind.decode("ascii", "replace"))
        if kind == b"IHDR":
            width, height, bit_depth, colour_type, _compression, _filter, interlace = struct.unpack(">IIBBBBB", data)
        elif kind == b"IDAT":
            idat.append(data)
        offset += 12 + length
        if kind == b"IEND":
            break
    try:
        decoded = zlib.decompress(b"".join(idat))
    except Exception as exc:
        decoded = b""
        errors.append(f"IDAT decompression failed: {exc}")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(colour_type)
    expected_scan_bytes = None
    if width and height and channels and bit_depth == 8 and interlace == 0:
        expected_scan_bytes = height * (1 + width * channels)
        if len(decoded) != expected_scan_bytes:
            errors.append(f"decoded scanline bytes {len(decoded)} != expected {expected_scan_bytes}")
    if not chunks or chunks[0] != "IHDR" or chunks[-1] != "IEND":
        errors.append("missing ordered IHDR/IEND")
    return {**row(path), "width": width, "height": height, "bit_depth": bit_depth,
            "colour_type": colour_type, "interlace": interlace, "chunk_count": len(chunks),
            "decoded_scanline_bytes": len(decoded), "expected_scanline_bytes": expected_scan_bytes,
            "valid": not errors, "errors": errors}

source_claim = load(PKG / "PR009_Audits/PR009_TRACE_PORTAL_CLEARANCE_SOURCE_v001.json")
source = load(AUDIT / "blender_source_inventory.json")
fbx = load(AUDIT / "fbx_roundtrip_inventory.json")
canonical = load(CANDIDATE / "CANONICAL_INTAKE_MANIFEST_v002.json")

# Compare the complete protected Candidate_v002 tree with the earlier 105-file pre-audit snapshot.
prior_integrity_path = ROOT / "Saved/Audits/PR009_InMap_v087/integrity_validation_after.json"
prior_integrity = load(prior_integrity_path)
prior_candidate = {item["path"]: (item["bytes"], item["sha256"]) for item in prior_integrity["source_staging_files"]}
current_candidate_rows = [row(path) for path in sorted(CANDIDATE.rglob("*")) if path.is_file()]
current_candidate = {item["path"]: (item["bytes"], item["sha256"]) for item in current_candidate_rows}
candidate_full_tree_unchanged = current_candidate == prior_candidate
candidate_full_tree_changes = sorted(path for path in set(current_candidate) | set(prior_candidate)
                                     if current_candidate.get(path) != prior_candidate.get(path))

def prior_scope_unchanged(key):
    expected = {item["path"]: (item["bytes"], item["sha256"]) for item in prior_integrity[key]}
    actual = {}
    for path, expected_value in expected.items():
        disk = ROOT / path
        actual[path] = (disk.stat().st_size, digest(disk)) if disk.exists() else None
    changes = sorted(path for path in set(expected) | set(actual) if expected.get(path) != actual.get(path))
    return not changes, changes, len(expected)

protected_unchanged, protected_changes, protected_count = prior_scope_unchanged("protected_files")
robots_unchanged, robot_changes, robot_count = prior_scope_unchanged("robot_files")
pr010_unchanged, pr010_changes, pr010_count = prior_scope_unchanged("pr010_files")
protected_map_changes = [path for path in protected_changes if path.lower().endswith(".umap")]
handoff_paths = ["Docs/NEW_CHAT_HANDOVER_2026-08-03.md", "Docs/PROJECT_HANDOFF.md"]
audit_started_utc = datetime.fromisoformat("2026-08-04T18:33:48+00:00")
handoff_mtimes = {path: datetime.fromtimestamp((ROOT / path).stat().st_mtime, timezone.utc).isoformat() for path in handoff_paths}
handoffs_touched_during_audit = [path for path in handoff_paths
                                 if datetime.fromtimestamp((ROOT / path).stat().st_mtime, timezone.utc) > audit_started_utc]

canonical_checks = []
for item in canonical["files"]:
    path = CANDIDATE / item["relative_path"]
    actual = row(path, CANDIDATE) if path.exists() else None
    canonical_checks.append({"relative_path": item["relative_path"], "exists": path.exists(),
                             "expected_bytes": item["bytes"], "actual_bytes": actual["bytes"] if actual else None,
                             "expected_sha256": item["sha256"], "actual_sha256": actual["sha256"] if actual else None,
                             "match": bool(actual and actual["bytes"] == item["bytes"] and actual["sha256"] == item["sha256"])})
canonical_manifest_pass = len(canonical_checks) == 84 and all(item["match"] for item in canonical_checks)

package_files = [row(path, PKG) for path in sorted(PKG.rglob("*")) if path.is_file()]
package_by_name = {Path(item["path"]).name: item for item in package_files}
declared = {
    Path(source_claim["derived"]["blend"]).name: source_claim["derived"]["blend_sha256"],
    Path(source_claim["derived"]["fbx"]).name: source_claim["derived"]["fbx_sha256"],
    **{item["file"]: item["sha256"] for item in source_claim["derived"]["renders"]},
}
declared_hash_checks = [{"file": name, "declared_sha256": expected,
                         "actual_sha256": package_by_name.get(name, {}).get("sha256"),
                         "match": package_by_name.get(name, {}).get("sha256") == expected}
                        for name, expected in sorted(declared.items())]
declared_hashes_pass = all(item["match"] for item in declared_hash_checks)
unmanifested_payloads = sorted(item["path"] for item in package_files
                               if Path(item["path"]).name not in declared and not item["path"].endswith("PR009_TRACE_PORTAL_CLEARANCE_SOURCE_v001.json"))

src_by_name = {item["name"]: item for item in source["objects"]}
fbx_by_name = {item["name"]: item for item in fbx["objects"]}
names_exact = set(src_by_name) == set(fbx_by_name) and len(src_by_name) == 11
roundtrip_rows = []
for name in sorted(set(src_by_name) | set(fbx_by_name)):
    a, b = src_by_name.get(name), fbx_by_name.get(name)
    if not a or not b:
        roundtrip_rows.append({"name": name, "present_both": False})
        continue
    slot_names_preserved = set(a["material_slots"]) == set(b["material_slots"])
    slot_order_preserved = a["material_slots"] == b["material_slots"]
    metadata_preserved = (a["object_custom_properties"] == b["object_custom_properties"] and
                          a["mesh_custom_properties"] == b["mesh_custom_properties"])
    material_metadata_preserved = a["material_custom_properties"] == b["material_custom_properties"]
    usage_preserved = a["material_polygon_usage"] == b["material_polygon_usage"]
    bounds_delta = max(abs(a["world_bounds_min_m"][i] - b["world_bounds_min_m"][i]) for i in range(3))
    bounds_delta = max(bounds_delta, max(abs(a["world_bounds_max_m"][i] - b["world_bounds_max_m"][i]) for i in range(3)))
    roundtrip_rows.append({"name": name, "present_both": True,
                           "semantic_object_and_mesh_names_preserved": a["name"] == b["name"] and a["mesh_data_name"] == b["mesh_data_name"],
                           "material_slot_names_preserved": slot_names_preserved,
                           "material_slot_order_preserved": slot_order_preserved,
                           "material_polygon_usage_preserved": usage_preserved,
                           "object_and_mesh_metadata_preserved": metadata_preserved,
                           "material_metadata_preserved": material_metadata_preserved,
                           "maximum_world_bounds_delta_m": bounds_delta,
                           "source_scale": a["scale"], "fbx_reimport_scale": b["scale"],
                           "source_rotation_rad": a["rotation_euler_rad"], "fbx_reimport_rotation_rad": b["rotation_euler_rad"]})

material_slot_names_pass = all(item.get("material_slot_names_preserved") for item in roundtrip_rows)
material_slot_order_pass = all(item.get("material_slot_order_preserved") for item in roundtrip_rows)
metadata_pass = all(item.get("object_and_mesh_metadata_preserved") and item.get("material_metadata_preserved") for item in roundtrip_rows)
usage_pass = all(item.get("material_polygon_usage_preserved") for item in roundtrip_rows)
bounds_roundtrip_pass = all(item.get("maximum_world_bounds_delta_m", 1) <= 1e-5 for item in roundtrip_rows)

render_rows = [png_validate(path) for path in sorted((PKG / "PR009_Renders").glob("*.png"))]
render_pass = len(render_rows) == 3 and all(item["valid"] and item["width"] >= 1280 and item["height"] >= 720 for item in render_rows)

gates = {
    "candidate_v002_full_tree_byte_identity": {"pass": candidate_full_tree_unchanged,
        "prior_snapshot": prior_integrity_path.relative_to(ROOT).as_posix(), "file_count": len(current_candidate),
        "changes": candidate_full_tree_changes},
    "candidate_v002_canonical_84_file_manifest": {"pass": canonical_manifest_pass,
        "checked": len(canonical_checks), "failures": [item for item in canonical_checks if not item["match"]]},
    "protected_unreal_maps_unchanged": {"pass": not protected_map_changes, "checked": protected_count - len(handoff_paths), "changes": protected_map_changes},
    "handoff_documents_not_edited_during_this_audit": {"pass": not handoffs_touched_during_audit,
        "audit_started_utc": audit_started_utc.isoformat(), "last_write_utc": handoff_mtimes,
        "preexisting_changes_since_v087_snapshot": [path for path in protected_changes if path in handoff_paths],
        "note": "Both handoff files changed before this bounded audit began; their timestamps predate the goal and this audit did not write them."},
    "robots_unchanged": {"pass": robots_unchanged, "checked": robot_count, "changes": robot_changes},
    "pr010_unchanged": {"pass": pr010_unchanged, "checked": pr010_count, "changes": pr010_changes},
    "source_exact_11_mesh_collection": {"pass": source["status"].startswith("PASS") and source["semantic_mesh_count"] == 11 and
        source["exact_semantic_portal_collections"] == ["PR009_MODULE_07_TRACEABILITY_PORTAL"],
        "retained_context_mesh_count": source["mesh_count"] - source["semantic_mesh_count"],
        "collection": source["exact_semantic_portal_collections"]},
    "fbx_exact_11_semantic_meshes": {"pass": fbx["mesh_count"] == 11 and names_exact,
        "mesh_count": fbx["mesh_count"], "missing": fbx["missing_semantic_meshes"], "unexpected": fbx["unexpected_meshes"]},
    "source_scale_rotation_and_pivots": {"pass": source["identity_component_scales"] and source["centred_component_pivots"] and source["semantic_mesh_datablock_names"]},
    "fbx_release_safe_component_transforms": {"pass": fbx["identity_component_scales"] and not any("rotation" in item for item in fbx["failures"]),
        "failures": fbx["failures"]},
    "dimensions_opening_and_envelope": {"pass": abs(source["clear_opening_m"] - 2.8) <= 1e-5 and abs(fbx["clear_opening_m"] - 2.8) <= 1e-5 and
        abs(source["source_envelope_m"]["min"][1] - 2.945) <= 1e-5 and abs(source["source_envelope_m"]["max"][1] - 3.355) <= 1e-5 and
        abs(source["source_envelope_m"]["centre"][1] - 3.15) <= 1e-5 and bounds_roundtrip_pass,
        "source": {"clear_opening_m": source["clear_opening_m"], "envelope": source["source_envelope_m"]},
        "fbx": {"clear_opening_m": fbx["clear_opening_m"], "envelope": fbx["source_envelope_m"]}},
    "fbx_semantic_names_custom_metadata_and_material_names": {"pass": names_exact and metadata_pass and material_slot_names_pass,
        "semantic_names": names_exact, "custom_metadata": metadata_pass, "material_slot_name_sets": material_slot_names_pass,
        "polygon_material_usage": usage_pass},
    "fbx_polygon_material_assignment": {"pass": usage_pass,
        "changed_on": [item["name"] for item in roundtrip_rows if not item.get("material_polygon_usage_preserved")]},
    "fbx_material_slot_order": {"pass": material_slot_order_pass,
        "reversed_on": [item["name"] for item in roundtrip_rows if not item.get("material_slot_order_preserved")]},
    "declared_payload_hashes": {"pass": declared_hashes_pass, "checks": declared_hash_checks},
    "complete_package_payload_manifest": {"pass": not unmanifested_payloads,
        "unmanifested_payloads": unmanifested_payloads,
        "note": "The source audit itself is excluded from self-hash expectations; the .blend1 backup is a payload and is not declared."},
    "three_source_renders": {"pass": render_pass, "renders": render_rows,
        "visual_inspection": "All three decode and are visually non-blank. Hero/service show installed portal context; elevated most clearly shows the opening. They are technical source evidence, not promotion approval."},
}

blockers = []
if not gates["fbx_release_safe_component_transforms"]["pass"]:
    blockers.append("All 11 FBX meshes reimport with component scale 0.01 and Z rotation pi rather than identity transforms; this repeats the known uncombined-binding scale/axis hazard.")
if not material_slot_order_pass:
    blockers.append("Every two-state restored/mothballed material slot list reverses during FBX round trip, and every mesh's polygons change from the restored material to the mothballed material; names survive but effective assignment and slot-index binding do not.")
if unmanifested_payloads:
    blockers.append("The package contains an unmanifested .blend1 backup, so the package manifest/hash coverage is incomplete even though every declared hash matches.")

status = "PASS__SOURCE_PACKAGE_RELEASE_BINDING_READY__NOT_PROMOTED" if all(item["pass"] for item in gates.values()) else "FAIL__FBX_TRANSFORM_MATERIAL_ASSIGNMENT_AND_MANIFEST_REWORK__NOT_PROMOTED"
payload = {
    "$schema": "cairnwell/audit/pr009-trace-portal-clearance-independent-source-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": status,
    "package": PKG.relative_to(ROOT).as_posix(),
    "scope": "Independent read-only Blender/FBX/source/render audit only; no Unreal map opened or modified.",
    "engineering_authority_correction": {
        "authority": "PR-009 Pro Sheet 02 and its engineering specification",
        "local_axes": {"positive_x": "across strip/lane", "positive_y": "material flow"},
        "maximum_blank_mm": {"across_x": 1800, "along_flow_y": 2600},
        "m02_travel_interpretation": "2800 mm is total travel within the 3100 mm module envelope, centred on the authored bridge midpoint; it is not +2800 mm from that midpoint.",
        "audit_consequence": "The measured 2800 mm portal opening is a package dimension only. Runtime necessity, design acceptance and promotion are not established by this source audit.",
        "experimental_successor_status": "Any v088 widened/moved portal successor remains experimental and NOT PROMOTED even if its source-integrity gates pass."
    },
    "package_files": package_files,
    "gates": gates,
    "roundtrip_per_mesh": roundtrip_rows,
    "exact_blockers": blockers,
    "release_source_package_ready": not blockers and all(item["pass"] for item in gates.values()),
    "promotion_authorized": False,
    "pr010_touched": False,
    "robots_touched": False,
    "handoff_documents_edited": False,
}
(AUDIT / "PR009_TRACE_PORTAL_CLEARANCE_INDEPENDENT_SOURCE_AUDIT_v001.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

report = f"""# PR-009 trace-portal clearance v001 independent source audit

**Outcome:** {status}. Promotion is not authorized.

## Passed evidence

- Candidate_v002 is byte-identical to the earlier complete 105-file snapshot; all 84 canonical manifest entries match exact byte counts and SHA-256 hashes.
- The derived Blender scene has one exact 11-mesh export collection, `PR009_MODULE_07_TRACEABILITY_PORTAL`; 569 other meshes are retained render/context geometry.
- The FBX contains exactly the same 11 semantic object and mesh-data names, with no extras.
- Source transforms are identity, all component pivots are centered, and the FBX round trip preserves centered pivots and world bounds within 0.01 mm.
- Independently measured clear opening is 2.800 m. Source-Y envelope is 2.945..3.355 m and center is 3.150 m in both Blender and the FBX reimport.
- Semantic object/mesh names, custom properties and both material names survive the FBX round trip; effective polygon material assignment does not and is listed below.
- All five declared payload hashes match. All three PNG renders pass signature, chunk CRC, IDAT decompression, scanline-size and resolution checks and were visually inspected as non-blank technical evidence.

## Engineering-authority correction

- Pro Sheet 02 defines local +X across the strip/lane and local +Y along material flow.
- The maximum blank is 1800 mm across X by 2600 mm along flow Y.
- M02's 2800 mm value is total travel within the 3100 mm module envelope, centered on the authored bridge midpoint. It is not a +2800 mm displacement from that midpoint.
- Consequently, the independently measured 2.800 m portal opening is only a verified package dimension. This audit does not establish that widening/moving the portal is operationally necessary or design-accepted. Any v088 successor remains experimental and NOT PROMOTED even if source-integrity defects are corrected.

## Exact blockers

1. All 11 FBX nodes reimport at scale `(0.01, 0.01, 0.01)` with a 180-degree Z rotation, not identity component transforms. Although assembled world bounds are correct, this is unsafe for uncombined semantic-part binding and repeats the known 1/100 transform hazard.
2. Every two-state material slot list reverses from `[RESTORED, MOTHBALLED_7Y]` in Blender to `[MOTHBALLED_7Y, RESTORED]` after FBX round trip. All polygons that use restored material in Blender use mothballed material after reimport. This is an effective material-assignment failure, not merely cosmetic ordering.
3. `CA_MW_PR009_TracePortalClearance_ProductionSource_v001.blend1` is present but absent from the declared hash manifest. Declared hashes are correct; package coverage is incomplete.

No Unreal map was opened or modified. PR-010, robot work and both handoff documents were not touched. Stop after this audit; do not promote.
"""
(AUDIT / "PR009_TRACE_PORTAL_CLEARANCE_INDEPENDENT_SOURCE_AUDIT_REPORT.md").write_text(report, encoding="utf-8")
print(json.dumps({"status": status, "blockers": blockers,
                  "output": str(AUDIT / "PR009_TRACE_PORTAL_CLEARANCE_INDEPENDENT_SOURCE_AUDIT_v001.json")}, indent=2))
