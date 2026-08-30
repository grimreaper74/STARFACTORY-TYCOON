"""Read-only Unreal verification for the Press Shop 2126 deck candidate.

Loads the assembled candidate from a clean unrelated editor world, validates
its saved actors/components against the hash-locked installer contract, writes
one validation receipt under Saved/Audits, and never saves or mutates an asset.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
INSTALLER = PROJECT / "Tools" / "install_pressshop_2126_overhead_deck_presentation_v001.py"
INSTALLER_SHA256 = "11076a18620e670c2f44b1875720278468191315667f30ee991accabf2a4b7d5"
INSTALL_RECEIPT = (
    PROJECT / "Saved" / "Audits" / "PressShop2126" / "OverheadPresentation_v002"
    / "install_receipt_v001.json"
)
INSTALL_RECEIPT_SHA256 = "eec9ebd5661e835943ceb606ba1569b209b8eb4ee2ab2836bcfb287c8634803d"
RECOVERY_RECEIPT_HASHES = {
    INSTALL_RECEIPT.parent / "failed_run_recovery_receipt_v001.json":
        "3736b43e99e4dd59c0a0e6e1f2526d1bfa0c3684f30aa88180c71afcb30dc630",
    INSTALL_RECEIPT.parent / "failed_run_recovery_receipt_v002.json":
        "9e9712b997cbe1719085a4a11e64348d5428d401736e54f6af2337cec3a4ff0e",
    INSTALL_RECEIPT.parent / "failed_run_recovery_receipt_v003.json":
        "68e2a8d824f87f8f8f290d5b57687cd361497c067f574cb0d4d5d922bc29b3d2",
}
VALIDATION_RECEIPT = INSTALL_RECEIPT.parent / "validation_receipt_v001.json"
VALIDATION_SCHEMA = "cairnwell.press_shop.overhead_deck_presentation_validation.v001"
EXPECTED_FINAL_ACTORS = 218
TOLERANCE = 0.01


class VerificationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise VerificationError(
        "PRESSSHOP_2126_OVERHEAD_DECK_PRESENTATION_VERIFY_V001_FAIL: " + message
    )


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest().lower()


def load_json(path: Path, expected_hash: str) -> Mapping[str, Any]:
    if not path.is_file() or digest(path) != expected_hash:
        fail("evidence file is missing or changed: " + path.as_posix())
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail("evidence file is unreadable: " + str(exc))
    if not isinstance(value, dict):
        fail("evidence file is not a JSON object: " + path.as_posix())
    return value


def load_installer_contract() -> Any:
    if not INSTALLER.is_file() or digest(INSTALLER) != INSTALLER_SHA256:
        fail("installer contract is missing or changed")
    spec = importlib.util.spec_from_file_location(
        "pressshop_2126_overhead_deck_installer_contract_v001", INSTALLER
    )
    if spec is None or spec.loader is None:
        fail("could not construct installer contract module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def near(actual: float, expected: float, context: str) -> None:
    if abs(float(actual) - float(expected)) > TOLERANCE:
        fail("{} changed: expected {}, found {}".format(context, expected, actual))


def verify_vector(actual: Any, expected: Sequence[float], context: str) -> None:
    for name, wanted in zip(("x", "y", "z"), expected):
        near(getattr(actual, name), float(wanted), context + "." + name)


def verify_rotation(actual: Any, expected: Sequence[float], context: str) -> None:
    for name, wanted in zip(("pitch", "yaw", "roll"), expected):
        near(getattr(actual, name), float(wanted), context + "." + name)


def normalised_name(value: Any) -> str:
    return "".join(character.lower() for character in str(value) if character.isalnum())


def verify_inert_primitive(
    contract: Any, actor: Any, component: Any, label: str
) -> Dict[str, Any]:
    if bool(actor.get_actor_enable_collision()):
        fail("saved presentation actor collision is enabled: " + label)
    enabled = str(component.get_collision_enabled())
    if "NO_COLLISION" not in enabled.upper():
        fail("saved primitive collision is not NO_COLLISION: " + label)
    profile = str(component.get_collision_profile_name())
    profile_name = normalised_name(profile)
    if profile_name not in {"nocollision", "custom"}:
        fail("saved primitive collision profile is unexpected: " + label)
    ignored = []
    for channel_name in contract.COLLISION_CHANNEL_NAMES:
        channel = getattr(unreal.CollisionChannel, channel_name)
        response = str(component.get_collision_response_to_channel(channel))
        if "ECR_IGNORE" not in response.upper():
            fail("saved primitive does not ignore {}: {}".format(channel_name, label))
        ignored.append(channel_name)
    return {
        "actor_collision_enabled": False,
        "component_collision_enabled": enabled,
        "collision_profile": profile,
        "profile_acceptance": (
            "NativeNoCollision" if profile_name == "nocollision"
            else "CustomWithNoCollisionAndIgnoreAll"
        ),
        "ignored_channels": ignored,
    }


def actor_tags(actor: Any) -> set[str]:
    return {str(tag) for tag in actor.tags}


def tag_count(records: Iterable[Mapping[str, Any]], tag: str) -> int:
    return sum(1 for row in records if tag in set(row.get("tags", ())))


def write_receipt(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    try:
        with path.open("xb") as handle:
            handle.write(payload)
    except FileExistsError:
        fail("validation receipt already exists; refusing overwrite")


def main() -> None:
    if VALIDATION_RECEIPT.exists():
        fail("validation receipt already exists; refusing rerun")
    contract = load_installer_contract()
    install = load_json(INSTALL_RECEIPT, INSTALL_RECEIPT_SHA256)
    for path, expected_hash in RECOVERY_RECEIPT_HASHES.items():
        load_json(path, expected_hash)

    exact_install_fields = {
        "schema": contract.RECEIPT_SCHEMA,
        "status": "PASS_CANDIDATE_PRESENTATION_MAP_ASSEMBLED__VISUAL_CAPTURE_AND_RUNTIME_PENDING",
        "target_map": contract.TARGET_MAP,
        "target_map_sha256": "58fe57f3af0dfcf4021d6bbcd3a52d7d66de22187b561fb2db41becd83023275",
        "target_map_bytes": 1097822,
        "source_actor_count": contract.EXPECTED_SOURCE_ACTORS,
        "legacy_presentation_removed_count": contract.EXPECTED_SOURCE_LEGACY_REMOVALS,
        "created_box_actor_count": 64,
        "created_text_actor_count": 15,
        "created_camera_actor_count": 3,
        "created_actor_count": 82,
        "roof_actor_count_after": 0,
    }
    for key, expected in exact_install_fields.items():
        if install.get(key) != expected:
            fail("install receipt {} changed".format(key))
    for key in (
        "runtime_validated", "runtime_ready", "packaged_build_validated",
        "visual_capture_validated", "steam_capture_validated",
    ):
        if install.get(key) is not False:
            fail("install receipt overclaims " + key)
    if install.get("collision_enabled_on_created_presentation") is not False:
        fail("install receipt collision claim changed")
    if install.get("failed_run_recovery", {}).get("schema") != contract.RECOVERY_RECEIPT_SCHEMA_V003:
        fail("install receipt does not cite the third exact recovery")
    if not contract.TARGET_FILE.is_file():
        fail("target map package is missing")
    if digest(contract.TARGET_FILE) != install["target_map_sha256"]:
        fail("target map hash differs from install receipt")

    protected_before = contract.protected_snapshot()
    if contract.dirty_package_paths() != {"content": [], "maps": []}:
        fail("editor has dirty packages before read-only validation")
    world_before = contract._editor_world()
    world_before_name = contract._world_package_name(world_before)
    if world_before_name in {contract.SOURCE_MAP, contract.TARGET_MAP}:
        fail("run verifier from an unrelated clean editor world")

    level_subsystem = contract._level_subsystem()
    if not level_subsystem.load_level(contract.TARGET_MAP):
        fail("could not load the saved candidate map")
    world = contract._editor_world()
    if contract._world_package_name(world) != contract.TARGET_MAP:
        fail("saved candidate is not the active editor world")
    if contract._world_game_mode_path(world) != contract.EXPECTED_GAME_MODE:
        fail("saved candidate GameMode changed")

    actors = list(contract._actor_subsystem().get_all_level_actors())
    records = [contract.actor_record(actor) for actor in actors]
    if len(records) != EXPECTED_FINAL_ACTORS:
        fail("saved candidate actor count changed")
    exact_tag_counts = {
        contract.VISUAL_LAYER_TAG: contract.EXPECTED_SOURCE_VISUAL_LAYERS,
        contract.PRESENTATION_TAG: 1,
        contract.BOOTSTRAP_TAG: 1,
        contract.BUILD_AUTHORITY_TAG: 1,
        contract.PLAYER_START_TAG: 1,
        contract.PASS_TAG: 82,
        contract.CAMERA_TAG: 3,
        contract.SOURCE_CAMERA_TAG: 0,
    }
    actual_tag_counts = {tag: tag_count(records, tag) for tag in exact_tag_counts}
    if actual_tag_counts != exact_tag_counts:
        fail("saved candidate tag counts changed")
    if any(contract.legacy_removal_reason(row) for row in records):
        fail("legacy presentation actor survived in the saved candidate")
    roof_records = [row for row in records if contract.is_roof_record(row)]
    if roof_records:
        fail("roof/ceiling/canopy actor exists in the saved candidate")

    pass_actors = [actor for actor in actors if contract.PASS_TAG in actor_tags(actor)]
    boxes = [actor for actor in pass_actors if isinstance(actor, unreal.StaticMeshActor)]
    texts = [actor for actor in pass_actors if isinstance(actor, unreal.TextRenderActor)]
    cameras = [actor for actor in pass_actors if isinstance(actor, unreal.CameraActor)]
    if (len(boxes), len(texts), len(cameras)) != (64, 15, 3):
        fail("saved presentation native class counts changed")
    if len(boxes) + len(texts) + len(cameras) != len(pass_actors):
        fail("saved presentation contains an unexpected actor class")

    box_specs = {str(row["label"]): row for row in contract.build_box_specs()}
    text_specs = {str(row["label"]): row for row in contract.build_text_specs()}
    camera_specs = {str(row["label"]): row for row in contract.CAMERA_SPECS}
    if {str(actor.get_actor_label()) for actor in boxes} != set(box_specs):
        fail("saved box labels changed")
    if {str(actor.get_actor_label()) for actor in texts} != set(text_specs):
        fail("saved text labels changed")
    if {str(actor.get_actor_label()) for actor in cameras} != set(camera_specs):
        fail("saved camera labels changed")

    material_paths = {
        str(row["id"]): contract.MATERIAL_ROOT + "/" + str(row["name"])
        for row in contract.MATERIAL_SPECS
    }
    collision_readbacks = []
    for actor in boxes:
        label = str(actor.get_actor_label())
        spec = box_specs[label]
        component = actor.get_editor_property("static_mesh_component")
        if component is None:
            fail("saved box lacks StaticMeshComponent: " + label)
        mesh = component.get_editor_property("static_mesh")
        if mesh is None or str(mesh.get_path_name()) != contract.CUBE_ASSET:
            fail("saved box is not the native engine cube: " + label)
        verify_vector(actor.get_actor_location(), spec["location_cm"], label + ".location")
        dimensions = spec["dimensions_cm"]
        verify_vector(
            actor.get_actor_scale3d(),
            (float(dimensions[0]) / 100.0, float(dimensions[1]) / 100.0,
             float(dimensions[2]) / 100.0),
            label + ".scale",
        )
        near(actor.get_actor_rotation().yaw, spec["yaw_deg"], label + ".yaw")
        material = component.get_material(0)
        expected_material = material_paths[str(spec["material_id"])]
        if material is None or str(material.get_path_name()) != expected_material:
            fail("saved box material changed: " + label)
        collision_readbacks.append(
            verify_inert_primitive(contract, actor, component, label)
        )

    for actor in texts:
        label = str(actor.get_actor_label())
        spec = text_specs[label]
        component = actor.get_editor_property("text_render")
        if component is None:
            fail("saved text actor lacks TextRenderComponent: " + label)
        verify_vector(actor.get_actor_location(), spec["location_cm"], label + ".location")
        verify_rotation(
            actor.get_actor_rotation(), spec["rotation_deg_pitch_yaw_roll"],
            label + ".rotation",
        )
        if str(component.get_text()) != str(spec["text"]):
            fail("saved TextRender content changed: " + label)
        near(component.get_editor_property("world_size"), spec["world_size_cm"],
             label + ".world_size")
        collision_readbacks.append(
            verify_inert_primitive(contract, actor, component, label)
        )

    camera_readbacks = []
    for actor in cameras:
        label = str(actor.get_actor_label())
        spec = camera_specs[label]
        center = spec["center_xy_cm"]
        verify_vector(
            actor.get_actor_location(),
            (float(center[0]), float(center[1]), contract.CAMERA_Z_CM),
            label + ".location",
        )
        verify_rotation(actor.get_actor_rotation(), contract.CAMERA_ROTATION,
                        label + ".rotation")
        component = actor.get_editor_property("camera_component")
        if component is None:
            fail("saved camera lacks CameraComponent: " + label)
        projection = str(component.get_editor_property("projection_mode"))
        if "ORTHOGRAPHIC" not in projection.upper():
            fail("saved camera is not orthographic: " + label)
        width = float(component.get_editor_property("ortho_width"))
        near(width, spec["ortho_width_cm"], label + ".ortho_width")
        required_tags = {
            contract.PASS_TAG, contract.CAMERA_TAG, str(spec["role_tag"]),
            *[str(tag) for tag in spec.get("additional_tags", ())],
        }
        if not required_tags.issubset(actor_tags(actor)):
            fail("saved camera tags changed: " + label)
        if bool(actor.get_actor_enable_collision()):
            fail("saved camera actor collision is enabled: " + label)
        camera_readbacks.append({
            "id": str(spec["id"]),
            "label": label,
            "location_cm": [float(center[0]), float(center[1]), contract.CAMERA_Z_CM],
            "rotation_deg_pitch_yaw_roll": list(contract.CAMERA_ROTATION),
            "ortho_width_cm": width,
            "projection": "ORTHOGRAPHIC",
            "required_tags": sorted(required_tags),
        })

    material_disk = []
    install_materials = {str(row["asset"]): row for row in install["created_materials"]}
    for spec in contract.MATERIAL_SPECS:
        asset = material_paths[str(spec["id"])]
        path = contract.asset_disk_path(asset)
        row = install_materials.get(asset)
        if row is None or not path.is_file():
            fail("saved candidate material evidence is incomplete: " + asset)
        actual_hash = digest(path)
        if actual_hash != row.get("sha256") or path.stat().st_size != row.get("bytes"):
            fail("saved candidate material differs from install receipt: " + asset)
        material_disk.append({
            "asset": asset, "sha256": actual_hash, "bytes": path.stat().st_size,
        })

    if contract.dirty_package_paths() != {"content": [], "maps": []}:
        fail("read-only validation dirtied an Unreal package")
    protected_after = contract.protected_snapshot()
    if protected_after != protected_before:
        fail("protected map changed during read-only validation")
    if digest(contract.TARGET_FILE) != install["target_map_sha256"]:
        fail("target map changed during read-only validation")

    profile_counts: Dict[str, int] = {}
    for row in collision_readbacks:
        key = str(row["profile_acceptance"])
        profile_counts[key] = profile_counts.get(key, 0) + 1
    receipt = {
        "schema": VALIDATION_SCHEMA,
        "status": "PASS_SAVED_CANDIDATE_NATIVE_PRESENTATION_CONTRACT__RUNTIME_AND_CAPTURE_PENDING",
        "read_only": True,
        "source_map_mutated": False,
        "protected_authority_map_mutated": False,
        "installer": INSTALLER.as_posix(),
        "installer_sha256": INSTALLER_SHA256,
        "install_receipt": INSTALL_RECEIPT.as_posix(),
        "install_receipt_sha256": INSTALL_RECEIPT_SHA256,
        "recovery_receipt_hashes": {
            path.as_posix(): value for path, value in RECOVERY_RECEIPT_HASHES.items()
        },
        "target_map": contract.TARGET_MAP,
        "target_map_sha256": digest(contract.TARGET_FILE),
        "target_map_bytes": contract.TARGET_FILE.stat().st_size,
        "current_world_before_load": world_before_name,
        "saved_actor_count": len(records),
        "tag_counts": actual_tag_counts,
        "native_box_count": len(boxes),
        "native_text_count": len(texts),
        "native_camera_count": len(cameras),
        "collision_primitive_count": len(collision_readbacks),
        "collision_profile_acceptance_counts": profile_counts,
        "all_collision_primitives_no_collision_ignore_all": True,
        "cameras": camera_readbacks,
        "materials": material_disk,
        "roof_actor_count": 0,
        "game_mode": contract._world_game_mode_path(world),
        "dirty_packages_after": contract.dirty_package_paths(),
        "protected_hashes_before": protected_before,
        "protected_hashes_after": protected_after,
        "runtime_validated": False,
        "runtime_ready": False,
        "packaged_build_validated": False,
        "visual_capture_validated": False,
        "steam_capture_validated": False,
        "honest_status": (
            "Saved candidate asset structure and native presentation component state are "
            "verified in-editor; gameplay runtime, rendered capture, cook and packaged "
            "validation remain separate gates."
        ),
    }
    write_receipt(VALIDATION_RECEIPT, receipt)
    unreal.log(
        "PRESSSHOP_2126_OVERHEAD_DECK_PRESENTATION_VERIFY_V001_PASS map={} receipt={}".format(
            contract.TARGET_MAP, VALIDATION_RECEIPT.as_posix()
        )
    )
    unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
