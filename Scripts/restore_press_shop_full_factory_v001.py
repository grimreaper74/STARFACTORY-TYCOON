"""One-shot, non-overwriting restoration of the preserved full Press Shop.

This script duplicates the exact protected v438 Unreal map asset.  It never
changes the clean v913 default map, any source map, Config, Source, or saves.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
DEST_MAP = "/Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001"
DEST_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap"
RECEIPT = ROOT / "Saved/Audits/PressShopRestoration/FullFactoryRestored_v001/build_receipt_v001.json"

PROTECTED = {
    "v438_full_source": (
        ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap",
        "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8",
    ),
    "v913_clean_default": (
        ROOT / "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap",
        "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6",
    ),
    "v249_preserved_parent": (
        ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v249.umap",
        "CCA3DA3BA67DAD74E4C58D7B0AB0F811639521F666B108987D2C775FA9C12B47",
    ),
    "v288_preserved_parent": (
        ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288.umap",
        "D022A98D905916D9A2464CC87D02B2D383F951729DFE1562A5671D58490A47F5",
    ),
}

TRAIN_TAGS = {letter: f"LB.PressTrain.Installed.TRAIN_{letter}" for letter in "ABCD"}
AGGREGATE_MESH = "/Game/LineBoss/Candidates/PressTrains/TrainA/ProDetailVisual_v354/SM_CA_MW_PressTrainA_ProDetailUnrealAggregate_v049"
INBOUND_TOKENS = ("coilagv", "coil agv", "lorry", "truck", "inbound", "delivery", "crane", "coilslot", "pr003", "pr-003")
EXPECTED_INBOUND_CLASSES = {
    "StaticMeshActor": 466,
    "TextRenderActor": 38,
    "CameraActor": 46,
    "SphereReflectionCapture": 1,
    "LBBridgeCraneController": 1,
    "PointLight": 1,
    "TargetPoint": 1,
    "LBSupportCraneController": 1,
    "SpotLight": 2,
    "LBCoilAGVController": 1,
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def rounded(values):
    return [round(float(value), 4) for value in values]


def component_visual_signature(actor):
    rows = []
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.static_mesh
        materials = []
        for index in range(component.get_num_materials()):
            material = component.get_material(index)
            materials.append(material.get_path_name() if material else "")
        rows.append({
            "mesh": mesh.get_path_name().split(".", 1)[0] if mesh else "",
            "materials": materials,
        })
    return sorted(rows, key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")))


def inventory_loaded_map():
    actor_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = actor_api.get_all_level_actors()
    records = []
    class_counts = Counter()
    tag_counts = Counter()
    inbound_class_counts = Counter()
    inbound_count = 0
    aggregate_count = 0

    for actor in actors:
        label = actor.get_actor_label()
        class_name = actor.get_class().get_name()
        tags = sorted(str(tag) for tag in actor.tags)
        location = rounded(actor.get_actor_location().to_tuple())
        rotation = rounded(actor.get_actor_rotation().to_tuple())
        scale = rounded(actor.get_actor_scale3d().to_tuple())
        visuals = component_visual_signature(actor)
        records.append({
            "label": label,
            "class": class_name,
            "tags": tags,
            "location_cm": location,
            "rotation_deg": rotation,
            "scale": scale,
            "visual_components": visuals,
        })
        class_counts[class_name] += 1
        tag_counts.update(tags)
        search = (label + " " + class_name + " " + " ".join(tags)).lower()
        if any(token in search for token in INBOUND_TOKENS):
            inbound_count += 1
            inbound_class_counts[class_name] += 1
        aggregate_count += sum(row["mesh"] == AGGREGATE_MESH for row in visuals)

    canonical = sorted(
        records,
        key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")),
    )
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    authorities = [actor for actor in actors if actor.get_class().get_name() == "LBPressShopBuildAuthority"]
    bay_count = 0
    spine_count = 0
    if len(authorities) == 1:
        bay_count = len(authorities[0].get_editor_property("build_bays"))
        spine_count = len(authorities[0].get_editor_property("utility_spines"))

    return {
        "actor_count": len(records),
        "actor_signature_sha256": hashlib.sha256(encoded).hexdigest().upper(),
        "class_counts": dict(sorted(class_counts.items())),
        "train_actor_counts": {letter: tag_counts[tag] for letter, tag in TRAIN_TAGS.items()},
        "build_authority_count": class_counts["LBPressShopBuildAuthority"],
        "build_bay_count": bay_count,
        "utility_spine_count": spine_count,
        "aggregate_train_visual_count": aggregate_count,
        "inbound_matching_actor_count": inbound_count,
        "inbound_class_counts": dict(sorted(inbound_class_counts.items())),
        "runtime_tag_counts": {
            tag: tag_counts[tag]
            for tag in ("LB.Vehicle.CoilAGV", "LB.Vehicle.CoilAGV.LiftDeck", "LB.Inventory.InTransfer")
        },
    }


def validate_frozen_evidence(inventory, scope):
    failures = []
    if inventory["train_actor_counts"] != {letter: 338 for letter in "ABCD"}:
        failures.append(f"{scope}: train actor counts drifted: {inventory['train_actor_counts']}")
    if inventory["build_authority_count"] != 1:
        failures.append(f"{scope}: build authority count is {inventory['build_authority_count']}, expected 1")
    if inventory["build_bay_count"] != 4 or inventory["utility_spine_count"] != 4:
        failures.append(
            f"{scope}: bays/spines are {inventory['build_bay_count']}/{inventory['utility_spine_count']}, expected 4/4"
        )
    if inventory["aggregate_train_visual_count"] != 4:
        failures.append(f"{scope}: detailed aggregate train visual count is {inventory['aggregate_train_visual_count']}, expected 4")
    if inventory["inbound_matching_actor_count"] != 558:
        failures.append(f"{scope}: inbound scope count is {inventory['inbound_matching_actor_count']}, expected 558")
    if inventory["inbound_class_counts"] != dict(sorted(EXPECTED_INBOUND_CLASSES.items())):
        failures.append(f"{scope}: inbound class inventory drifted: {inventory['inbound_class_counts']}")
    if inventory["runtime_tag_counts"] != {
        "LB.Vehicle.CoilAGV": 1,
        "LB.Vehicle.CoilAGV.LiftDeck": 1,
        "LB.Inventory.InTransfer": 1,
    }:
        failures.append(f"{scope}: inbound runtime tags drifted: {inventory['runtime_tag_counts']}")
    if failures:
        raise RuntimeError("; ".join(failures))


def protected_hashes():
    return {name: sha256(path) for name, (path, _expected) in PROTECTED.items()}


def main():
    asset_library = unreal.EditorAssetLibrary

    before = protected_hashes()
    for name, (_path, expected) in PROTECTED.items():
        if before[name] != expected:
            raise RuntimeError(f"protected hash drift before restore: {name} {before[name]} != {expected}")
    if not asset_library.does_asset_exist(SOURCE_MAP):
        raise RuntimeError(f"protected source asset is missing: {SOURCE_MAP}")
    if asset_library.does_asset_exist(DEST_MAP) or DEST_FILE.exists() or RECEIPT.exists():
        raise RuntimeError(f"one-shot refusal: destination or receipt already exists: {DEST_MAP}")

    unreal.EditorLoadingAndSavingUtils.load_map(SOURCE_MAP)
    source_inventory = inventory_loaded_map()
    validate_frozen_evidence(source_inventory, "source")

    duplicated = asset_library.duplicate_asset(SOURCE_MAP, DEST_MAP)
    if not duplicated or not asset_library.does_asset_exist(DEST_MAP):
        raise RuntimeError("Unreal asset duplication failed")
    if not asset_library.save_loaded_asset(duplicated, only_if_is_dirty=False):
        raise RuntimeError("explicit destination UWorld save failed")

    # A Python reference to a duplicated UWorld prevents load_map() garbage
    # collection and can trigger Unreal's World Memory Leaks fatal.  Release it
    # here and leave the destination fresh-load/inventory comparison to the
    # independent validator's separate process.
    duplicated = None
    unreal.collect_garbage()

    after = protected_hashes()
    if after != before:
        raise RuntimeError(f"protected map changed during restore: before={before}, after={after}")
    if not DEST_FILE.exists():
        raise RuntimeError(f"destination package missing after explicit save: {DEST_FILE}")

    payload = {
        "$schema": "cairnwell/audit/press-shop-full-factory-restoration-build-v001/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__EXACT_V438_UNREAL_ASSET_DUPLICATE__EXPLICITLY_SAVED__PROTECTED_MAPS_UNCHANGED__INDEPENDENT_FRESH_LOAD_VALIDATION_REQUIRED",
        "source_map": SOURCE_MAP,
        "destination_map": DEST_MAP,
        "duplication_method": "unreal.EditorAssetLibrary.duplicate_asset",
        "protected_sha256_before": before,
        "protected_sha256_after": after,
        "destination_sha256": sha256(DEST_FILE),
        "source_inventory": source_inventory,
        "destination_inventory": "DEFERRED_TO_INDEPENDENT_FRESH_PROCESS_VALIDATOR",
        "source_destination_actor_signature_equal": "PENDING_INDEPENDENT_VALIDATOR",
        "default_map_changed": False,
        "promotion_authorized": False,
        "runtime_note": "Saved plant, authorities, controller actors and bindings are static map content. PIE may spawn transient workpieces/effects, but they are not required to restore the authored Press Shop.",
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log(json.dumps(payload, indent=2))


main()
unreal.SystemLibrary.quit_editor()
