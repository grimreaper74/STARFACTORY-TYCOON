"""Read-only diagnosis of v005 actor fingerprints after a fresh editor load.

The v006 installer intentionally refuses to proceed when the frozen v005 actor
inventory cannot be reproduced.  This probe loads only the already-hashed v005
map, records both path-keyed and clone-stable semantic hashes, proves that no
package was dirtied, and writes evidence under Saved/Audits.  It never creates,
saves, imports, duplicates, renames, or deletes a Content asset.
"""

from __future__ import annotations

import datetime as _dt
import importlib.util
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
INSTALLER = PROJECT / "Tools/install_pressshop_2126_overhead_presentation_correction_v001.py"
OUT_DIR = (
    PROJECT / "Saved/Audits/PressShop2126/OverheadPresentation_v006"
    / "diagnostics/loaded_v005_fingerprints_v001"
)


def _load_installer():
    spec = importlib.util.spec_from_file_location("pressshop_v006_diagnostic_locked", INSTALLER)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load v006 installer module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def main() -> None:
    mod = _load_installer()
    started = _dt.datetime.now(_dt.timezone.utc)
    run_id = started.strftime("%Y%m%dT%H%M%S%fZ")
    output = OUT_DIR / ("loaded_v005_fingerprints_" + run_id + ".json")

    contract = mod.validate_offline_contract(require_fresh_target=True)
    protected_before = mod.protected_snapshot()
    mod._v005._assert_dirty_packages(
        {"content": [], "maps": []}, "diagnostic editor was dirty before source load"
    )
    level_subsystem = mod._v005._level_subsystem()
    actor_subsystem = mod._v005._actor_subsystem()
    if not level_subsystem.load_level(mod.SOURCE_MAP):
        raise RuntimeError("could not load frozen v005 source")
    world = mod._v005._editor_world()
    if mod._v005._world_package_name(world) != mod.SOURCE_MAP:
        raise RuntimeError("v005 source was not the active world")
    actors = list(actor_subsystem.get_all_level_actors() or [])
    if len(actors) != mod.EXPECTED_SOURCE_ACTOR_COUNT:
        raise RuntimeError("loaded actor count changed")

    path_records = mod._records_by_path(actors)
    rows = list(path_records.values())
    nonpresentation = {
        path: row for path, row in path_records.items()
        if mod.PRESENTATION_PASS_TAG not in set(row["tags"])
    }
    unchanged_v005 = {
        path: row for path, row in path_records.items()
        if mod.PRESENTATION_PASS_TAG in set(row["tags"])
        and mod.V005_UPGRADE_TAG not in set(row["tags"])
    }
    visual = {
        path: row for path, row in path_records.items()
        if mod.VISUAL_LAYER_TAG in set(row["tags"])
    }
    cargo = {
        path: row for path, row in visual.items()
        if mod.CARGO_MAP_TAG in set(row["tags"])
    }
    machinery = {
        path: row for path, row in visual.items()
        if mod.CARGO_MAP_TAG not in set(row["tags"])
    }
    groups = {
        "preserved_nonpresentation": nonpresentation,
        "unchanged_v005_presentation": unchanged_v005,
        "combined_visual": visual,
        "machinery_visual": machinery,
        "cargo_visual": cargo,
    }

    group_evidence = {}
    for name, group in groups.items():
        semantic = mod._semantic_records_from_rows(group.values())
        actual = mod._hash_records(group)
        expected = mod.EXPECTED_SOURCE_HASHES[name]
        group_evidence[name] = {
            "count": len(group),
            "path_keyed_actual_sha256": actual,
            "path_keyed_expected_sha256": expected,
            "path_keyed_matches_receipt": actual == expected,
            "semantic_sha256": mod._hash_records(semantic),
            "first_five_paths": sorted(group)[:5],
            "first_five_semantic_keys": sorted(semantic)[:5],
            "semantic_records": semantic,
        }

    exact_tags = {
        tag: mod._count_tag(rows, tag) for tag in (
            mod.VISUAL_LAYER_TAG, mod.CARGO_MAP_TAG, mod.CARGO_SOURCE_TAG,
            mod.PRESENTATION_PASS_TAG, mod.PRESENTATION_CAMERA_TAG,
            mod.PRESENTATION_ADAPTER_TAG, mod.V004_POLISH_TAG, mod.V005_UPGRADE_TAG,
        )
    }
    mod._v005._assert_dirty_packages(
        {"content": [], "maps": []}, "read-only v005 fingerprint diagnostic dirtied packages"
    )
    protected_after = mod.protected_snapshot()
    if protected_after != protected_before:
        raise RuntimeError("protected map changed during read-only diagnostic")

    payload = {
        "schema": "cairnwell.press_shop.v005_loaded_fingerprint_diagnostic.v001",
        "status": "PASS_READ_ONLY_DIAGNOSTIC__NO_CONTENT_MUTATION",
        "started_utc": started.isoformat(),
        "source_map": mod.SOURCE_MAP,
        "source_map_sha256": mod.SOURCE_FILE_SHA256,
        "source_receipt_sha256": mod.SOURCE_RECEIPT_SHA256,
        "source_capture_receipt_sha256": mod.SOURCE_CAPTURE_RECEIPT_SHA256,
        "actor_count": len(actors),
        "presentation_actor_count": sum(
            mod.PRESENTATION_PASS_TAG in set(row["tags"]) for row in rows
        ),
        "tag_counts": exact_tags,
        "groups": group_evidence,
        "all_actor_semantic_sha256": mod._hash_records(
            mod._semantic_records_from_rows(rows)
        ),
        "protected_hashes_before": protected_before,
        "protected_hashes_after": protected_after,
        "offline_contract_source_receipt_status": contract["source_receipt"]["status"],
        "writes_to_content": False,
        "saves_performed": False,
    }
    _atomic_json(output, payload)
    unreal.log("PRESSSHOP_V005_LOADED_FINGERPRINT_DIAGNOSTIC_PASS " + output.as_posix())
    unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
