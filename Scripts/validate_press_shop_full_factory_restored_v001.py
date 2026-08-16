"""Independent, read-only fresh-load validation of FullFactoryRestored_v001."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
RESTORED_MAP = "/Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001"
SOURCE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
RESTORED_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap"
V913_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap"
BUILD_RECEIPT = ROOT / "Saved/Audits/PressShopRestoration/FullFactoryRestored_v001/build_receipt_v001.json"
OUT = ROOT / "Saved/Audits/PressShopRestoration/FullFactoryRestored_v001/independent_validation_v001.json"
SOURCE_SHA = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
V913_SHA = "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6"
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

SIGNATURE_NORMALIZATION = {
    "method": "replace_only_the_source_or_restored_world_object_prefix_with_<DUPLICATED_WORLD>",
    "scope": "map-owned object references only; external asset paths and all actor data remain exact",
    "reason": "Unreal asset duplication necessarily rebases map-owned dynamic material instance paths to the destination world package",
    "read_only_diagnostic": "Saved/Audits/PressShopRestoration/FullFactoryRestored_v001/signature_diagnostic_v001.json",
    "diagnostic_result": "9 source-only and 9 restored-only raw rows; zero differing rows after world-prefix-only normalization",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def rounded(values):
    return [round(float(value), 4) for value in values]


def normalized_duplicated_world_object_path(path):
    """Normalize only the package root that Unreal must rebase during UWorld duplication."""
    for map_path in (SOURCE_MAP, RESTORED_MAP):
        world_name = map_path.rsplit("/", 1)[-1]
        world_object_path = f"{map_path}.{world_name}"
        if path == world_object_path:
            return "<DUPLICATED_WORLD>"
        if path.startswith(world_object_path + ":"):
            return "<DUPLICATED_WORLD>" + path[len(world_object_path):]
    return path


def inventory_loaded_map():
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    records = []
    classes = Counter()
    tags = Counter()
    inbound_classes = Counter()
    inbound_count = 0
    aggregate_count = 0

    for actor in actors:
        label = actor.get_actor_label()
        class_name = actor.get_class().get_name()
        actor_tags = sorted(str(tag) for tag in actor.tags)
        visuals = []
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = component.static_mesh
            materials = []
            for index in range(component.get_num_materials()):
                material = component.get_material(index)
                material_path = material.get_path_name() if material else ""
                materials.append(normalized_duplicated_world_object_path(material_path))
            mesh_path = mesh.get_path_name().split(".", 1)[0] if mesh else ""
            visuals.append({"mesh": mesh_path, "materials": materials})
            aggregate_count += mesh_path == AGGREGATE_MESH
        visuals.sort(key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")))
        records.append({
            "label": label,
            "class": class_name,
            "tags": actor_tags,
            "location_cm": rounded(actor.get_actor_location().to_tuple()),
            "rotation_deg": rounded(actor.get_actor_rotation().to_tuple()),
            "scale": rounded(actor.get_actor_scale3d().to_tuple()),
            "visual_components": visuals,
        })
        classes[class_name] += 1
        tags.update(actor_tags)
        search = (label + " " + class_name + " " + " ".join(actor_tags)).lower()
        if any(token in search for token in INBOUND_TOKENS):
            inbound_count += 1
            inbound_classes[class_name] += 1

    canonical = sorted(records, key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")))
    signature = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()
    authorities = [actor for actor in actors if actor.get_class().get_name() == "LBPressShopBuildAuthority"]
    bay_count = len(authorities[0].get_editor_property("build_bays")) if len(authorities) == 1 else 0
    spine_count = len(authorities[0].get_editor_property("utility_spines")) if len(authorities) == 1 else 0
    return {
        "actor_count": len(records),
        "actor_signature_sha256": signature,
        "class_counts": dict(sorted(classes.items())),
        "train_actor_counts": {
            letter: tags[f"LB.PressTrain.Installed.TRAIN_{letter}"] for letter in "ABCD"
        },
        "build_authority_count": classes["LBPressShopBuildAuthority"],
        "build_bay_count": bay_count,
        "utility_spine_count": spine_count,
        "aggregate_train_visual_count": aggregate_count,
        "inbound_matching_actor_count": inbound_count,
        "inbound_class_counts": dict(sorted(inbound_classes.items())),
        "runtime_tag_counts": {
            tag: tags[tag]
            for tag in ("LB.Vehicle.CoilAGV", "LB.Vehicle.CoilAGV.LiftDeck", "LB.Inventory.InTransfer")
        },
    }


def key_failures(inventory, scope):
    failures = []
    if inventory["train_actor_counts"] != {letter: 338 for letter in "ABCD"}:
        failures.append(f"{scope}: train actor counts {inventory['train_actor_counts']}")
    if inventory["build_authority_count"] != 1:
        failures.append(f"{scope}: build authority count {inventory['build_authority_count']}")
    if inventory["build_bay_count"] != 4 or inventory["utility_spine_count"] != 4:
        failures.append(f"{scope}: bays/spines {inventory['build_bay_count']}/{inventory['utility_spine_count']}")
    if inventory["aggregate_train_visual_count"] != 4:
        failures.append(f"{scope}: aggregate train visuals {inventory['aggregate_train_visual_count']}")
    if inventory["inbound_matching_actor_count"] != 558:
        failures.append(f"{scope}: inbound matching actors {inventory['inbound_matching_actor_count']}")
    if inventory["inbound_class_counts"] != dict(sorted(EXPECTED_INBOUND_CLASSES.items())):
        failures.append(f"{scope}: inbound class counts drifted")
    if inventory["runtime_tag_counts"] != {
        "LB.Vehicle.CoilAGV": 1,
        "LB.Vehicle.CoilAGV.LiftDeck": 1,
        "LB.Inventory.InTransfer": 1,
    }:
        failures.append(f"{scope}: runtime tag counts {inventory['runtime_tag_counts']}")
    return failures


def main():
    failures = []
    if sha256(SOURCE_FILE) != SOURCE_SHA:
        raise RuntimeError("protected v438 source hash drift before validation")
    if sha256(V913_FILE) != V913_SHA:
        raise RuntimeError("protected v913 default hash drift before validation")
    if not unreal.EditorAssetLibrary.does_asset_exist(RESTORED_MAP) or not RESTORED_FILE.exists():
        raise RuntimeError(f"restored map is missing: {RESTORED_MAP}")

    # Destination is deliberately fresh-loaded first; this validator never saves a map.
    unreal.EditorLoadingAndSavingUtils.load_map(RESTORED_MAP)
    restored_inventory = inventory_loaded_map()
    failures.extend(key_failures(restored_inventory, "restored"))

    unreal.EditorLoadingAndSavingUtils.load_map(SOURCE_MAP)
    source_inventory = inventory_loaded_map()
    failures.extend(key_failures(source_inventory, "source"))
    if restored_inventory != source_inventory:
        failures.append(
            "actor inventory differs after duplicated-world-prefix-only normalization: "
            f"restored={restored_inventory['actor_signature_sha256']} source={source_inventory['actor_signature_sha256']}"
        )

    receipt_destination_sha = None
    if BUILD_RECEIPT.exists():
        receipt_destination_sha = json.loads(BUILD_RECEIPT.read_text(encoding="utf-8")).get("destination_sha256")
        if receipt_destination_sha != sha256(RESTORED_FILE):
            failures.append("destination package hash differs from build receipt")
    else:
        failures.append("build receipt is missing")

    if sha256(SOURCE_FILE) != SOURCE_SHA or sha256(V913_FILE) != V913_SHA:
        failures.append("protected source/default hash changed during read-only validation")

    payload = {
        "$schema": "cairnwell/audit/press-shop-full-factory-restoration-validation-v001/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__FRESH_LOAD_WORLD_PREFIX_NORMALIZED_ACTOR_SIGNATURE_AND_KEY_PRESS_FAMILIES_MATCH_V438__READ_ONLY" if not failures else "FAIL__RESTORED_PRESS_SHOP_NOT_PROVEN",
        "source_map": SOURCE_MAP,
        "restored_map": RESTORED_MAP,
        "map_saved": False,
        "source_sha256": sha256(SOURCE_FILE),
        "restored_sha256": sha256(RESTORED_FILE),
        "receipt_destination_sha256": receipt_destination_sha,
        "source_inventory": source_inventory,
        "restored_inventory": restored_inventory,
        "signature_normalization": SIGNATURE_NORMALIZATION,
        "normalized_actor_signature_equal": source_inventory["actor_signature_sha256"] == restored_inventory["actor_signature_sha256"],
        "runtime_spawn_dependency": "NOT_REQUIRED_FOR_SAVED_FACTORY_RESTORATION; transient workpieces/effects still require later PIE validation",
        "promotion_authorized": False,
        "failures": failures,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log(json.dumps(payload, indent=2))
    if failures:
        raise RuntimeError("; ".join(failures))


main()
unreal.SystemLibrary.quit_editor()
