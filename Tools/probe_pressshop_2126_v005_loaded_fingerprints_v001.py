"""Read-only proof for the v005 saved-map actor-path fingerprint discrepancy.

This Unreal Editor probe loads the immutable v004 and v005 maps, reads actor
fingerprints, and writes evidence under ``Saved/Audits`` only.  It never clones,
creates, saves, renames, imports, deletes or modifies a Content asset/package.

The v005 install receipt was generated from actors in the transient in-memory
result of ``new_level_from_template``.  Its legacy dictionaries use
``Actor.get_path_name()`` both as their keys and inside every value.  It also
stores MotionStart/MotionEnd via ``str(Transform)``, whose repr embeds a
per-process pointer.  A later load of the saved v005 map is therefore allowed
to differ in those two unstable encodings.  This probe proves the scope by
comparing v004 and saved-v005 after removing only the top-level ephemeral path
and parsing all ten numeric transform values out of those two reprs; all asset,
actor/motion transform, material, collision, tag and visual-metadata fields remain.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

try:
    import unreal  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - intended for Unreal execution
    unreal = None  # type: ignore


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CONTRACT_PATH = (
    PROJECT / "Tools/install_pressshop_2126_overhead_presentation_correction_v001.py"
)
OUTPUT = (
    PROJECT / "Saved/Audits/PressShop2126/OverheadPresentation_v006"
    / "loaded_v005_fingerprint_probe_v001.json"
)
SCHEMA = "cairnwell.press_shop.v005_loaded_fingerprint_probe.v001"
STATUS = (
    "PASS_ONLY_EPHEMERAL_ACTOR_OBJECT_PATH_AND_TRANSFORM_REPR_ADDRESS_DIFFER__"
    "ALL_UNCHANGED_V004_TO_SAVED_V005_SEMANTICS_EXACT"
)
GROUP_COUNTS: Mapping[str, int] = {
    "preserved_nonpresentation": 162,
    "unchanged_v005_presentation": 24,
    "combined_visual": 146,
    "machinery_visual": 120,
    "cargo_visual": 26,
}


class LoadedFingerprintProbeError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise LoadedFingerprintProbeError(
        "PRESSSHOP_2126_V005_LOADED_FINGERPRINT_PROBE_V001_FAIL: " + message
    )


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest().lower()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def load_contract() -> Any:
    if not CONTRACT_PATH.is_file():
        fail("v006 installer contract is missing")
    spec = importlib.util.spec_from_file_location(
        "pressshop_v006_loaded_fingerprint_probe_contract", CONTRACT_PATH
    )
    if spec is None or spec.loader is None:
        fail("could not construct the v006 installer contract import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tags(row: Mapping[str, Any]) -> set[str]:
    return {str(value) for value in row.get("tags", ())}


def pathless_row(contract: Any, row: Mapping[str, Any]) -> Dict[str, Any]:
    # Round-trip through the production helper so the probe uses exactly the
    # same narrow path/pointer normalization as the guarded installer.
    singleton = contract._semantic_records_from_rows([row])
    if len(singleton) != 1:
        fail("probe semantic normalization lost an actor")
    result = next(iter(singleton.values()))
    if "path" in result:
        fail("probe semantic normalization retained actor object path")
    return copy.deepcopy(result)


def legacy_groups(
    contract: Any,
    actors: Sequence[Any],
    mutation_labels: set[str],
    stage: str,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    records = contract._records_by_path(actors)
    if stage == "v004":
        source_package = (
            contract._v005.SOURCE_MAP + "."
            + contract._v005.SOURCE_MAP.rsplit("/", 1)[-1]
        )
    elif stage == "v005":
        source_package = contract.SOURCE_MAP + "." + contract.SOURCE_MAP.rsplit("/", 1)[-1]
    else:
        fail("unknown group stage")
    if any(not path.startswith(source_package) for path in records):
        fail(stage + " actor escaped its immutable source package")

    nonpresentation = {
        path: row for path, row in records.items()
        if contract.PRESENTATION_PASS_TAG not in tags(row)
    }
    if stage == "v004":
        unchanged = {
            path: row for path, row in records.items()
            if contract.PRESENTATION_PASS_TAG in tags(row)
            and str(row["label"]) not in mutation_labels
        }
    else:
        unchanged = {
            path: row for path, row in records.items()
            if contract.PRESENTATION_PASS_TAG in tags(row)
            and contract.V005_UPGRADE_TAG not in tags(row)
        }
    visual = {
        path: row for path, row in records.items()
        if contract.VISUAL_LAYER_TAG in tags(row)
    }
    cargo = {
        path: row for path, row in visual.items()
        if contract.CARGO_MAP_TAG in tags(row)
    }
    machinery = {
        path: row for path, row in visual.items()
        if contract.CARGO_MAP_TAG not in tags(row)
    }
    groups = {
        "preserved_nonpresentation": nonpresentation,
        "unchanged_v005_presentation": unchanged,
        "combined_visual": visual,
        "machinery_visual": machinery,
        "cargo_visual": cargo,
    }
    for name, expected in GROUP_COUNTS.items():
        if len(groups[name]) != expected:
            fail("{} {} actor count changed".format(stage, name))
    return groups


def semantic_groups(
    contract: Any,
    groups: Mapping[str, Mapping[str, Mapping[str, Any]]],
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    result = {
        name: contract._semantic_records_from_rows(group.values())
        for name, group in groups.items()
    }
    for name, expected in GROUP_COUNTS.items():
        if len(result[name]) != expected:
            fail("semantic multiset lost actor multiplicity: " + name)
    return result


def differing_path_samples(
    contract: Any,
    before: Mapping[str, Mapping[str, Any]],
    after: Mapping[str, Mapping[str, Any]],
    limit: int = 12,
) -> List[Dict[str, Any]]:
    def index(group: Mapping[str, Mapping[str, Any]]) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        for path, row in group.items():
            clean = pathless_row(contract, row)
            identity = "\x1f".join((
                str(clean.get("class_path", "")), str(clean.get("label", "")),
                hashlib.sha256(canonical_json_bytes(clean)).hexdigest(),
            ))
            result.setdefault(identity, []).append(path)
        return {key: sorted(paths) for key, paths in result.items()}

    left, right = index(before), index(after)
    if set(left) != set(right):
        fail("pathless sample identities differ despite semantic equality")
    samples: List[Dict[str, Any]] = []
    for key in sorted(left):
        if left[key] == right[key]:
            continue
        class_path, label, semantic_hash = key.split("\x1f")
        samples.append({
            "class_path": class_path,
            "label": label,
            "semantic_row_sha256": semantic_hash,
            "v004_saved_paths": left[key],
            "v005_saved_paths": right[key],
        })
        if len(samples) >= limit:
            break
    return samples


def main() -> None:
    if unreal is None:
        fail("probe must run inside UnrealEditor Python")
    contract = load_contract()
    inputs = contract.validate_offline_contract(require_fresh_target=False)
    protected_before = contract.protected_snapshot()
    contract._v005._assert_dirty_packages(
        {"content": [], "maps": []}, "probe requires a clean editor"
    )
    initial_map = contract._v005._world_package_name(contract._v005._editor_world())
    subsystem = contract._v005._level_subsystem()
    actor_subsystem = contract._v005._actor_subsystem()
    mutation_labels = {
        str(row["source"]["label"]) for row in contract._v005_plan()["mutations"]
    }

    if not subsystem.load_level(contract._v005.SOURCE_MAP):
        fail("could not load immutable v004 map")
    v004_world = contract._v005._editor_world()
    if contract._v005._world_package_name(v004_world) != contract._v005.SOURCE_MAP:
        fail("v004 map did not become the active editor world")
    v004_actors = list(actor_subsystem.get_all_level_actors() or [])
    contract._v005.validate_source_actor_inventory(v004_actors)
    v004_groups = legacy_groups(contract, v004_actors, mutation_labels, "v004")
    v004_semantic = semantic_groups(contract, v004_groups)
    contract._v005._assert_dirty_packages(
        {"content": [], "maps": []}, "v004 read-only probe dirtied packages"
    )

    if not subsystem.load_level(contract.SOURCE_MAP):
        fail("could not load immutable v005 map")
    v005_world = contract._v005._editor_world()
    if contract._v005._world_package_name(v005_world) != contract.SOURCE_MAP:
        fail("v005 map did not become the active editor world")
    v005_actors = list(actor_subsystem.get_all_level_actors() or [])
    v005_inventory = contract._validate_loaded_source_actor_groups(v005_actors)
    v005_groups = legacy_groups(contract, v005_actors, mutation_labels, "v005")
    v005_semantic = semantic_groups(contract, v005_groups)

    for name in GROUP_COUNTS:
        contract._assert_semantic_records_equal(
            v004_semantic[name], v005_semantic[name],
            "immutable v004 to saved-v005 unchanged group " + name,
        )
    legacy_matches = dict(v005_inventory["legacy_receipt_path_hash_matches"])
    mismatched_groups = sorted(name for name, matched in legacy_matches.items() if not matched)
    if "preserved_nonpresentation" not in mismatched_groups:
        fail("the reported preserved_nonpresentation legacy path mismatch did not reproduce")

    samples = differing_path_samples(
        contract,
        v004_groups["preserved_nonpresentation"],
        v005_groups["preserved_nonpresentation"],
    )
    if not samples:
        fail("no differing actor object paths were observed for the reproduced mismatch")

    contract._v005._assert_dirty_packages(
        {"content": [], "maps": []}, "v005 read-only probe dirtied packages"
    )
    if contract.protected_snapshot() != protected_before:
        fail("a protected map changed during the read-only probe")

    source_receipt = inputs["source_receipt"]
    expected_legacy = {
        "preserved_nonpresentation": source_receipt[
            "preserved_nonpresentation_actor_fingerprints_after_sha256"
        ],
        "unchanged_v005_presentation": source_receipt[
            "unchanged_presentation_actor_fingerprints_after_sha256"
        ],
        "combined_visual": source_receipt[
            "visual_layer_actor_fingerprints_after_sha256"
        ],
        "machinery_visual": source_receipt[
            "machinery_actor_fingerprints_after_sha256"
        ],
        "cargo_visual": source_receipt[
            "cargo_actor_fingerprints_after_sha256"
        ],
    }
    report = {
        "schema": SCHEMA,
        "status": STATUS,
        "read_only": True,
        "content_assets_created": 0,
        "content_assets_saved": 0,
        "content_assets_modified": 0,
        "maps_cloned": 0,
        "maps_saved": 0,
        "v004_map": contract._v005.SOURCE_MAP,
        "v004_map_sha256": contract._v005.SOURCE_FILE_SHA256,
        "v005_map": contract.SOURCE_MAP,
        "v005_map_sha256": contract.SOURCE_FILE_SHA256,
        "v005_install_receipt_sha256": contract.SOURCE_RECEIPT_SHA256,
        "v005_capture_receipt_sha256": contract.SOURCE_CAPTURE_RECEIPT_SHA256,
        "v005_capture_png_sha256": {
            name: row["sha256"] for name, row in contract.SOURCE_CAPTURE_LOCKS.items()
        },
        "group_counts": dict(GROUP_COUNTS),
        "v005_receipt_legacy_path_keyed_hashes": expected_legacy,
        "v005_saved_reload_legacy_path_keyed_hashes": (
            v005_inventory["legacy_path_keyed_group_hashes"]
        ),
        "v005_saved_reload_legacy_receipt_hash_matches": legacy_matches,
        "legacy_path_hash_mismatched_groups": mismatched_groups,
        "semantic_normalization": (
            "only the top-level Actor.get_path_name() field/key is removed and only "
            "the process pointer in MotionStart/MotionEnd str(Transform) is replaced "
            "by all ten parsed numeric components; class, label, asset, actor/motion "
            "transforms, materials, collision, tags and all remaining visual metadata "
            "remain exact; duplicate labels and multiplicity are retained"
        ),
        "v004_semantic_group_hashes": {
            name: contract._hash_records(rows) for name, rows in v004_semantic.items()
        },
        "v005_saved_reload_semantic_group_hashes": {
            name: contract._hash_records(rows) for name, rows in v005_semantic.items()
        },
        "semantic_group_equality": {name: True for name in GROUP_COUNTS},
        "preserved_nonpresentation_differing_path_samples": samples,
        "conclusion": (
            "The locked v005 receipt's legacy hash mismatch is confined to ephemeral "
            "actor object-path keys/fields from the transient template-clone world and "
            "per-process pointers embedded by Unreal in MotionStart/MotionEnd transform "
            "reprs. Removing only the path and pointer while retaining every parsed "
            "numeric component makes every unchanged v004-to-saved-v005 actor record "
            "exact, including all machine/cargo actor/motion transforms, materials, "
            "collision, tags and remaining visual-metadata fields."
        ),
        "protected_hashes_before": protected_before,
        "protected_hashes_after": contract.protected_snapshot(),
        "dirty_packages_after": contract._v005.dirty_package_paths(),
        "initial_editor_map": initial_map,
        "final_editor_map": contract._v005._world_package_name(
            contract._v005._editor_world()
        ),
        "probe_contract_path": CONTRACT_PATH.as_posix(),
        "probe_contract_sha256": digest(CONTRACT_PATH),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        with OUTPUT.open("xb") as handle:
            handle.write(canonical_json_bytes(report))
    except FileExistsError:
        fail("probe receipt already exists; refusing overwrite")
    unreal.log(
        "PRESSSHOP_2126_V005_LOADED_FINGERPRINT_PROBE_V001_PASS output={}".format(
            OUTPUT.as_posix()
        )
    )
    unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
