"""Offline contract for recovering the preserved v438 Train A presentation.

This module deliberately has no Unreal dependency.  It pins the immutable source
evidence, rejects later/Meshy/vendor/developer references, validates the richer
manifest produced by the read-only Unreal exporter, and compiles a deterministic
HISM/static-component plan.  It never creates or modifies Content.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable


SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
SOURCE_MAP_SHA256 = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
TRAIN_SCOPE_TAG = "LB.PressTrain.Installed.TRAIN_A"
TRAIN_DATUM_CM = [3850.0, -4300.0, 0.0]
EXPECTED_ACTOR_COUNT = 338
EXPECTED_VISUAL_ACTOR_COUNT = 337
EXPECTED_CLASS_COUNTS = {
    "StaticMeshActor": 336,
    "TextRenderActor": 1,
    "LBPressTrainAStation": 1,
}
LEGACY_AUTHORITY_CLASS = "LBPressTrainAStation"
LEGACY_AUTHORITY_LABEL = "LB_INST_PTA_NativeAuthority_v223"

SOURCE_CAPTURE_RELATIVE = Path(
    "Saved/Audits/PressShopIntegration/press_shop_capture_layout_v452.json"
)
SOURCE_CAPTURE_SHA256 = "376B88B3B5F1D5BFAEDCBD317DF4D14652228EB76CEE683436B7A55DAFCA20E0"
SOURCE_CAPTURE_ALL_ACTOR_SIGNATURE_SHA256 = (
    "954C64F6428AC1FFA05AC2B06314373D33E466499903D11E661F686A0378423E"
)
SOURCE_CAPTURE_VISUAL_ACTOR_SIGNATURE_SHA256 = (
    "179B83D8029BB9FBBC5BAA3C5647CDDB06B57293C7D6999738E1BC2097A21120"
)

V448_AUDIT_RELATIVE = Path(
    "Saved/Audits/PressShopIntegration/press_shop_completed_train_visual_source_v448.json"
)
V448_AUDIT_SHA256 = "D45ADFC6D0C6BEEFE0F2107EE181BBD9AF18CDDF9A090B634412B5790D8ACE0E"
V449_RECEIPT_RELATIVE = Path(
    "Saved/Audits/PressTrains/press_train_complete_runtime_visual_build_v449.json"
)
V449_RECEIPT_SHA256 = "CF09E3F1EE7623501BCEB79318A264712DEC17303107E27573552A7BAAA74148"
V449_RUNTIME_MESH = (
    "/Game/LineBoss/PressTrains/RuntimeVisual_v449/"
    "SM_CA_MW_PressTrain_CompleteRuntimeVisual_v449"
)
V449_RUNTIME_MESH_RELATIVE = Path(
    "Content/LineBoss/PressTrains/RuntimeVisual_v449/"
    "SM_CA_MW_PressTrain_CompleteRuntimeVisual_v449.uasset"
)
V449_RUNTIME_MESH_SHA256 = "4344B058F78D66F178095201E13D824CAD017C827DF7AFCBA369193DCA73931E"
V449_MATERIAL_SLOT_COUNT = 306
V449_AGGREGATE_RELATIVE_LOCATION_CM = [9.25, 2367.5, 0.0]
V449_AGGREGATE_RELATIVE_SCALE = [100.0, 100.0, 100.0]

RESTORED_VALIDATION_RELATIVE = Path(
    "Saved/Audits/PressShopRestoration/FullFactoryRestored_v001/"
    "independent_validation_v001.json"
)
RESTORED_VALIDATION_SHA256 = "7B55A06093FB941EBF26221AEA95B2A75B2FDE901D92A119088C3E4B9BDC3F90"
RESTORED_DETAIL_SCREENSHOT_RELATIVE = Path(
    "Saved/ValidationScreenshots/PressShop/FullFactoryRestored_v001/"
    "04_recovered_press_train_detail.png"
)
RESTORED_DETAIL_SCREENSHOT_SHA256 = (
    "907BFFE910876E33415BD8E579C8ADD6BF637267515C1547D5D32667A8098486"
)
CURRENT_BLOCKOUT_SCREENSHOT_RELATIVE = Path(
    "Saved/ValidationScreenshots/OneFactory/v001/ActualPlayerPIE/"
    "20260815T035404438Z/02_populated_press_starter_wide_overview.png"
)
CURRENT_BLOCKOUT_SCREENSHOT_SHA256 = (
    "7645637C24E077BF6B0F61BAEC1C70A15467913EA0882ACE27D7C23532AEC1FA"
)

MATERIAL_HASHES = {
    "/Game/LineBoss/Candidates/PressTrains/InstalledPBR_v383/M_CA_MW_PT_ServiceCopper_v383":
        "35BCCBC9B8C98E9C98B70012E18609AC0BB298ED96725D18E13283E3A7E40053",
    "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_AmberSafetyActive_v086":
        "358B6D15507EB35BFF7E85C596CC0D02127CEF1FEEB6C232DCFEF6AB6E11E49B",
    "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_DriveBlue_v086":
        "C5540F7057AFA8ECB8960B981EC8284FB3974B51959A600F5B6C2EA8E8017C57",
    "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_EStopRed_v086":
        "1FD70A1F57AF72FCA8C73D9AABB03DA15CE6E57BBCE4B4E0F0BE69EADCB036B2",
    "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LabelWhite_v086":
        "5E759E45FB763F526094BF534E1BE897C9486E5BA67500C1009F573BC928EE61",
    "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LayeredCairnwellGreen_v086":
        "57CFAA364B2C005632AB3991B2427FB2F080EAC4C42C883D095048B7105BF755",
    "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LayeredFoundryCharcoal_v086":
        "033A2904005EF233BCD12AC5E18D647727F79187F89901B101B6CA4576F7AF1B",
    "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LayeredSafetyYellow_v086":
        "A20DACD220BC24302F7D04BE2DC09D93806ABF29BD95E4328D711B0B58B6A481",
    "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LayeredServiceGrey_v086":
        "BBDE8F750A5D58491FB9E183409130D43D7B79D7A853EEA4D7FDBA31F740C03A",
    "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_MachinedSteel_v086":
        "11C507A49C5F18153750703B1AF59A643CBBE737B3B7A57B7AA933016C359E5F",
    "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_OiledBlankSteel_v086":
        "2CCD6E49365D2758A3CCEDB9F207744A559C8DBFD15924ADB7DED1E1601D4DE9",
    "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_Rubber_v086":
        "2B5520FBBADC8D012C142274A6FC14CE336349C7506960BF04DA418DA02100A9",
    "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_SensorGlass_v086":
        "B3E09A0E120CA5E782885AEEDDAF145018FBA7800D78397363CC9EABB9347C02",
}

RAW_MANIFEST_SCHEMA = "cairnwell/one-factory/detailed-press/v438-train-a-source/v1"
PLAN_SCHEMA = "cairnwell/one-factory/detailed-press/materialization-plan/v1"

_REVISION_TOKEN = re.compile(r"(?:^|[/_.-])v(\d{3,})(?=$|[/_.-])", re.IGNORECASE)
_FORBIDDEN_TEXT = (
    "meshy",
    "/vendor/",
    "/vendors/",
    "/developer/",
    "/developers/",
    "developervalidation",
    "developer_validation",
    "developer-validation",
)
_MOVABLE_ROLE_TOKENS = (
    "querymover",
    "moving_",
    "carried_workpiece",
    "runtime_robot",
    "unload_robot",
    "runtime_hmi",
)


class ContractError(RuntimeError):
    """The preserved source or candidate manifest violated a fixed contract."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def package_to_file(root: Path, package: str) -> Path:
    package = package.split(".", 1)[0]
    if not package.startswith("/Game/"):
        raise ContractError(f"Package is not project Content: {package}")
    return root / "Content" / (package[len("/Game/") :] + ".uasset")


def forbidden_reference_reason(path: str) -> str | None:
    normalized = str(path).replace("\\", "/")
    lowered = normalized.lower()
    for token in _FORBIDDEN_TEXT:
        if token in lowered:
            return f"forbidden provenance token {token!r}"
    revisions = [int(match.group(1)) for match in _REVISION_TOKEN.finditer(lowered)]
    if any(revision >= 700 for revision in revisions):
        return f"forbidden v700+ revision token(s) {revisions}"
    if lowered.startswith("/game/") and not lowered.startswith("/game/lineboss/"):
        return "project asset escapes /Game/LineBoss"
    if lowered.startswith("/") and not lowered.startswith(
        ("/game/lineboss/", "/engine/", "/script/")
    ):
        return "reference is outside approved project/Engine/Script roots"
    return None


def _require_hash(path: Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise ContractError(f"Missing {label}: {path}")
    actual = sha256(path)
    if actual != expected:
        raise ContractError(f"{label} hash drift: {actual} != {expected}")


def _seed_projection(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (row["label"], row["class"]))


def validate_preserved_evidence(root: Path) -> dict[str, Any]:
    """Prove the source map, exact 338 inventory, v449 fallback and screenshot."""
    root = root.resolve()
    map_file = root / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
    _require_hash(map_file, SOURCE_MAP_SHA256, "protected v438 map")

    capture_path = root / SOURCE_CAPTURE_RELATIVE
    _require_hash(capture_path, SOURCE_CAPTURE_SHA256, "v452 actor capture")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if capture.get("map") != SOURCE_MAP:
        raise ContractError("v452 actor capture names the wrong source map")
    actors = [
        row for row in capture.get("actors", [])
        if TRAIN_SCOPE_TAG in row.get("tags", [])
    ]
    if len(actors) != EXPECTED_ACTOR_COUNT:
        raise ContractError(f"Train A actor count drift: {len(actors)}")
    if Counter(row.get("class") for row in actors) != Counter(EXPECTED_CLASS_COUNTS):
        raise ContractError("Train A class inventory drift")
    if len({row.get("label") for row in actors}) != EXPECTED_ACTOR_COUNT:
        raise ContractError("Train A actor labels are not unique")
    if canonical_sha256(_seed_projection(actors)) != SOURCE_CAPTURE_ALL_ACTOR_SIGNATURE_SHA256:
        raise ContractError("Train A 338-actor canonical signature drift")
    visual_rows = [row for row in actors if row.get("class") != LEGACY_AUTHORITY_CLASS]
    if len(visual_rows) != EXPECTED_VISUAL_ACTOR_COUNT:
        raise ContractError("Train A visual actor count drift")
    if canonical_sha256(_seed_projection(visual_rows)) != SOURCE_CAPTURE_VISUAL_ACTOR_SIGNATURE_SHA256:
        raise ContractError("Train A 337-visual-actor canonical signature drift")
    legacy = [row for row in actors if row.get("class") == LEGACY_AUTHORITY_CLASS]
    if len(legacy) != 1 or legacy[0].get("label") != LEGACY_AUTHORITY_LABEL:
        raise ContractError("Legacy v438 gameplay authority identity drift")
    for row in visual_rows:
        reason = forbidden_reference_reason(
            " ".join([str(row.get("label", "")), *map(str, row.get("tags", []))])
        )
        if reason:
            raise ContractError(f"Forbidden Train A actor provenance: {reason}")

    v448_path = root / V448_AUDIT_RELATIVE
    _require_hash(v448_path, V448_AUDIT_SHA256, "v448 aggregate audit")
    v448 = json.loads(v448_path.read_text(encoding="utf-8"))
    if v448.get("map") != SOURCE_MAP or v448.get("count") != 4:
        raise ContractError("v448 aggregate audit no longer proves four v438 instances")

    v449_path = root / V449_RECEIPT_RELATIVE
    _require_hash(v449_path, V449_RECEIPT_SHA256, "v449 runtime visual receipt")
    v449 = json.loads(v449_path.read_text(encoding="utf-8"))
    if (
        v449.get("source_map") != SOURCE_MAP
        or v449.get("source_map_sha256") != SOURCE_MAP_SHA256
        or v449.get("runtime_mesh") != V449_RUNTIME_MESH
        or v449.get("runtime_mesh_sha256") != V449_RUNTIME_MESH_SHA256
        or v449.get("material_slot_count") != V449_MATERIAL_SLOT_COUNT
    ):
        raise ContractError("v449 runtime visual receipt contract drift")
    _require_hash(
        root / V449_RUNTIME_MESH_RELATIVE,
        V449_RUNTIME_MESH_SHA256,
        "v449 runtime visual mesh",
    )
    unique_materials = sorted({str(value).split(".", 1)[0] for value in v449["materials"]})
    if unique_materials != sorted(MATERIAL_HASHES):
        raise ContractError("v449 exact 13-material family drift")
    for package, expected_hash in MATERIAL_HASHES.items():
        reason = forbidden_reference_reason(package)
        if reason:
            raise ContractError(f"Forbidden v449 material [{package}]: {reason}")
        _require_hash(package_to_file(root, package), expected_hash, package)

    validation_path = root / RESTORED_VALIDATION_RELATIVE
    _require_hash(validation_path, RESTORED_VALIDATION_SHA256, "restored-map validation")
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    source_inventory = validation.get("source_inventory", {})
    if (
        not str(validation.get("status", "")).startswith("PASS__")
        or source_inventory.get("train_actor_counts", {}).get("A") != EXPECTED_ACTOR_COUNT
        or source_inventory.get("aggregate_train_visual_count") != 4
    ):
        raise ContractError("restored-map validation no longer proves the source visuals")
    _require_hash(
        root / RESTORED_DETAIL_SCREENSHOT_RELATIVE,
        RESTORED_DETAIL_SCREENSHOT_SHA256,
        "restored press-train detail screenshot",
    )
    _require_hash(
        root / CURRENT_BLOCKOUT_SCREENSHOT_RELATIVE,
        CURRENT_BLOCKOUT_SCREENSHOT_SHA256,
        "current OneFactory blockout screenshot",
    )

    return {
        "status": "PASS__PRESERVED_PRE_MESHY_V438_TRAIN_A_EVIDENCE_PINNED",
        "source_map": SOURCE_MAP,
        "source_map_sha256": SOURCE_MAP_SHA256,
        "actor_count": len(actors),
        "visual_actor_count": len(visual_rows),
        "class_counts": dict(sorted(Counter(row["class"] for row in actors).items())),
        "train_datum_cm": TRAIN_DATUM_CM,
        "v449_fidelity_fallback": {
            "mesh": V449_RUNTIME_MESH,
            "mesh_sha256": V449_RUNTIME_MESH_SHA256,
            "material_slot_count": V449_MATERIAL_SLOT_COUNT,
            "unique_material_count": len(unique_materials),
            "relative_location_cm": V449_AGGREGATE_RELATIVE_LOCATION_CM,
            "relative_scale": V449_AGGREGATE_RELATIVE_SCALE,
        },
        "legacy_authority_policy": "AUDIT IDENTITY ONLY; NEVER MATERIALIZE CURRENT CONSTRUCTOR ART",
        "visual_recovery_baseline": {
            "current_blockout_screenshot_sha256": CURRENT_BLOCKOUT_SCREENSHOT_SHA256,
            "restored_v438_detail_screenshot_sha256": RESTORED_DETAIL_SCREENSHOT_SHA256,
        },
    }


def _finite_vector(value: Any, length: int = 3) -> bool:
    return (
        isinstance(value, list)
        and len(value) == length
        and all(isinstance(item, (int, float)) and math.isfinite(float(item)) for item in value)
    )


def _iter_component_references(component: dict[str, Any]) -> Iterable[str]:
    mesh_path = component.get("mesh_path")
    if mesh_path:
        yield str(mesh_path)
    font_path = component.get("font_path")
    if font_path:
        yield str(font_path)
    for material in component.get("materials", []):
        for key in ("object_path", "parent_path"):
            if material.get(key):
                yield str(material[key])
        for value in material.get("texture_parameters", {}).values():
            if value:
                yield str(value)


def package_from_object_reference(reference: str) -> str:
    """Return a Content package name without retaining an object/subobject path."""
    normalized = str(reference).replace("\\", "/")
    if not normalized.startswith(("/Game/", "/Engine/")):
        return ""
    return normalized.split(":", 1)[0].split(".", 1)[0]


def material_requires_runtime_clone(material: dict[str, Any]) -> bool:
    """True when a material object cannot be referenced by a fresh loaded map."""
    path = str(material.get("object_path", "")).lower()
    class_path = str(material.get("class_path", "")).lower()
    return bool(
        material.get("map_owned")
        or "materialinstancedynamic" in class_path
        or path.startswith("/engine/transient")
        or path.startswith("/temp/")
        or path.startswith("/memory/")
    )


def validate_extraction_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if payload.get("$schema") != RAW_MANIFEST_SCHEMA:
        failures.append("wrong manifest schema")
    if payload.get("source_map") != SOURCE_MAP:
        failures.append("wrong source map")
    if payload.get("source_map_sha256_before") != SOURCE_MAP_SHA256:
        failures.append("source hash before extraction is wrong")
    if payload.get("source_map_sha256_after") != SOURCE_MAP_SHA256:
        failures.append("source hash after extraction is wrong")
    if payload.get("source_map_saved") is not False:
        failures.append("extractor claims the source map was saved")
    if payload.get("scope_tag") != TRAIN_SCOPE_TAG:
        failures.append("wrong Train A scope tag")
    if payload.get("train_datum_cm") != TRAIN_DATUM_CM:
        failures.append("wrong Train A datum")

    actors = payload.get("actors")
    if not isinstance(actors, list) or len(actors) != EXPECTED_ACTOR_COUNT:
        failures.append("manifest does not contain exactly 338 actors")
        actors = actors if isinstance(actors, list) else []
    labels = [str(row.get("label", "")) for row in actors]
    if len(set(labels)) != len(labels):
        failures.append("actor labels are not unique")
    counts = Counter(str(row.get("class_name", "")) for row in actors)
    if counts != Counter(EXPECTED_CLASS_COUNTS):
        failures.append(f"class inventory drift: {dict(counts)}")

    legacy_rows = [row for row in actors if row.get("class_name") == LEGACY_AUTHORITY_CLASS]
    if len(legacy_rows) != 1:
        failures.append("legacy authority count is not exactly one")
    elif (
        legacy_rows[0].get("label") != LEGACY_AUTHORITY_LABEL
        or legacy_rows[0].get("materialization_policy")
            != "excluded_current_native_constructor"
        or legacy_rows[0].get("components")
    ):
        failures.append("legacy authority is not identity-only and excluded")

    seed_projection: list[dict[str, Any]] = []
    visual_component_count = 0
    render_primitive_count = 0
    reference_count = 0
    project_packages: set[str] = set()
    for actor in actors:
        class_name = str(actor.get("class_name", ""))
        if TRAIN_SCOPE_TAG not in actor.get("tags", []):
            failures.append(f"actor lacks Train A scope tag: {actor.get('label')}")
        if not all(
            _finite_vector(actor.get(key))
            for key in (
                "world_location_cm", "world_rotation_deg", "world_scale",
                "relative_location_cm", "relative_rotation_deg", "relative_scale",
            )
        ):
            failures.append(f"actor transform is incomplete: {actor.get('label')}")
        if class_name != LEGACY_AUTHORITY_CLASS:
            seed_projection.append(actor.get("seed_projection", {}))
        components = actor.get("components", [])
        if class_name != LEGACY_AUTHORITY_CLASS and not components:
            failures.append(f"visual actor has no components: {actor.get('label')}")
        for component in components:
            if not all(
                _finite_vector(component.get(key))
                for key in (
                    "world_location_cm", "world_rotation_deg", "world_scale",
                    "relative_location_cm", "relative_rotation_deg", "relative_scale",
                )
            ):
                failures.append(
                    f"component transform is incomplete: {actor.get('label')}/"
                    f"{component.get('component_name')}"
                )
            kind = component.get("visual_kind")
            if kind in {"static_mesh", "instanced_static_mesh"}:
                visual_component_count += 1
                if not component.get("mesh_path") or not component.get("materials"):
                    failures.append(
                        f"static visual lacks mesh/materials: {actor.get('label')}/"
                        f"{component.get('component_name')}"
                    )
                if kind == "instanced_static_mesh":
                    instances = component.get("source_instances", [])
                    expected_instances = component.get("source_instance_count")
                    if (
                        not isinstance(expected_instances, int)
                        or expected_instances < 1
                        or not isinstance(instances, list)
                        or len(instances) != expected_instances
                    ):
                        failures.append(
                            "instanced visual lacks its exact instance transforms: "
                            f"{actor.get('label')}/{component.get('component_name')}"
                        )
                    if [row.get("instance_index") for row in instances] != list(
                        range(len(instances))
                    ):
                        failures.append(
                            "instanced visual instance indexes are not exact/contiguous: "
                            f"{actor.get('label')}/{component.get('component_name')}"
                        )
                    for instance in instances:
                        if not all(
                            _finite_vector(instance.get(key))
                            for key in (
                                "world_location_cm", "world_rotation_deg", "world_scale",
                                "relative_location_cm", "relative_rotation_deg", "relative_scale",
                            )
                        ):
                            failures.append(
                                "instanced visual has an incomplete instance transform: "
                                f"{actor.get('label')}/{component.get('component_name')}"
                            )
                    render_primitive_count += len(instances)
                else:
                    render_primitive_count += 1
            elif kind == "text":
                visual_component_count += 1
                render_primitive_count += 1
                if not component.get("text"):
                    failures.append(f"text visual is empty: {actor.get('label')}")
            for reference in _iter_component_references(component):
                reference_count += 1
                reason = forbidden_reference_reason(reference)
                if reason:
                    failures.append(f"forbidden reference [{reference}]: {reason}")
                package = package_from_object_reference(reference)
                if package.startswith("/Game/") and package != SOURCE_MAP:
                    project_packages.add(package)
            for material in component.get("materials", []):
                if material_requires_runtime_clone(material) and not material.get("parent_path"):
                    failures.append(
                        "ephemeral/map-owned material lacks a reusable parent/parameter snapshot: "
                        f"{material.get('object_path')}"
                    )

    if len(seed_projection) != EXPECTED_VISUAL_ACTOR_COUNT:
        failures.append("visual seed projection does not contain 337 actors")
    elif canonical_sha256(_seed_projection(seed_projection)) != (
        SOURCE_CAPTURE_VISUAL_ACTOR_SIGNATURE_SHA256
    ):
        failures.append("337-visual-actor v452 seed signature mismatch")
    if visual_component_count < EXPECTED_VISUAL_ACTOR_COUNT:
        failures.append("manifest has fewer visual components than visual actors")

    provenance_rows = payload.get("project_asset_provenance", [])
    if not isinstance(provenance_rows, list):
        failures.append("project asset provenance is not a list")
        provenance_rows = []
    provenance_by_package = {
        str(row.get("package_path", "")): row for row in provenance_rows
    }
    if set(provenance_by_package) != project_packages:
        failures.append(
            "project asset provenance does not exactly cover referenced packages: "
            f"expected={sorted(project_packages)} actual={sorted(provenance_by_package)}"
        )
    for package, row in provenance_by_package.items():
        digest = str(row.get("sha256", ""))
        size = row.get("size_bytes")
        if (
            forbidden_reference_reason(package)
            or not re.fullmatch(r"[0-9A-F]{64}", digest)
            or not isinstance(size, int)
            or size <= 0
            or not row.get("file_relative")
        ):
            failures.append(f"invalid project asset provenance row: {package}")

    if failures:
        raise ContractError("; ".join(failures))
    return {
        "actor_count": len(actors),
        "visual_actor_count": len(seed_projection),
        "visual_component_count": visual_component_count,
        "render_primitive_count": render_primitive_count,
        "reference_count": reference_count,
        "project_asset_count": len(project_packages),
        "class_counts": dict(sorted(counts.items())),
    }


def validate_manifest_asset_files(root: Path, payload: dict[str, Any]) -> None:
    """Re-hash every project dependency named by a previously validated manifest."""
    validate_extraction_manifest(payload)
    root = root.resolve()
    for row in payload.get("project_asset_provenance", []):
        package = str(row["package_path"])
        relative = Path(str(row["file_relative"]))
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError as error:
            raise ContractError(f"Asset provenance escapes project root: {relative}") from error
        expected_base = root / "Content" / package[len("/Game/") :]
        approved = {
            expected_base.with_suffix(".uasset").resolve(),
            expected_base.with_suffix(".umap").resolve(),
        }
        if path not in approved:
            raise ContractError(
                f"Asset provenance file/package mismatch: {package} -> {relative}"
            )
        if not path.is_file():
            raise ContractError(f"Asset provenance file is missing: {relative}")
        if path.stat().st_size != row["size_bytes"] or sha256(path) != row["sha256"]:
            raise ContractError(f"Asset provenance hash/size drift: {package}")


def _material_key(materials: list[dict[str, Any]]) -> str:
    normalized = []
    for material in materials:
        normalized.append({
            "object_path": material.get("object_path", ""),
            "parent_path": material.get("parent_path", ""),
            "scalar_parameters": material.get("scalar_parameters", {}),
            "vector_parameters": material.get("vector_parameters", {}),
            "texture_parameters": material.get("texture_parameters", {}),
        })
    return canonical_sha256(normalized)


def _material_for_plan(material: dict[str, Any]) -> dict[str, Any]:
    """Remove any live dependency on a protected-map-owned dynamic instance."""
    if not material_requires_runtime_clone(material):
        return dict(material)
    clone_payload = {
        "parent_path": material.get("parent_path", ""),
        "scalar_parameters": material.get("scalar_parameters", {}),
        "vector_parameters": material.get("vector_parameters", {}),
        "texture_parameters": material.get("texture_parameters", {}),
    }
    return {
        "object_path": "",
        "class_path": material.get("class_path", ""),
        "parent_path": clone_payload["parent_path"],
        "map_owned": False,
        "material_clone_id": "OF_PRESS_V438_MI_" + canonical_sha256(clone_payload)[:16],
        "source_map_material_evidence": material.get("object_path", ""),
        "scalar_parameters": clone_payload["scalar_parameters"],
        "vector_parameters": clone_payload["vector_parameters"],
        "texture_parameters": clone_payload["texture_parameters"],
    }


def _requires_individual_component(actor: dict[str, Any]) -> bool:
    search = " ".join(
        [str(actor.get("label", "")), *map(str, actor.get("tags", []))]
    ).lower()
    return any(token in search for token in _MOVABLE_ROLE_TOKENS)


def compile_materialization_plan(payload: dict[str, Any]) -> dict[str, Any]:
    """Group immutable visuals without creating Content or runtime objects."""
    summary = validate_extraction_manifest(payload)
    hism_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    static_components: list[dict[str, Any]] = []
    text_components: list[dict[str, Any]] = []

    for actor in payload["actors"]:
        if actor.get("class_name") == LEGACY_AUTHORITY_CLASS:
            continue
        individual = _requires_individual_component(actor)
        for component in actor.get("components", []):
            kind = component.get("visual_kind")
            record = {
                "source_actor": actor["label"],
                "source_component": component.get("component_name", ""),
                "relative_location_cm": component["relative_location_cm"],
                "relative_rotation_deg": component["relative_rotation_deg"],
                "relative_scale": component["relative_scale"],
                "mesh_path": component.get("mesh_path", ""),
                "materials": [
                    _material_for_plan(material)
                    for material in component.get("materials", [])
                ],
            }
            if kind == "text":
                record["text"] = component.get("text", "")
                record["font_path"] = component.get("font_path", "")
                text_components.append(record)
                continue
            if kind not in {"static_mesh", "instanced_static_mesh"}:
                continue
            if kind == "instanced_static_mesh":
                source_instances = component.get("source_instances", [])
                if individual:
                    record["source_instances"] = source_instances
                    static_components.append(record)
                    continue
                key = (record["mesh_path"], _material_key(record["materials"]))
                for source_instance in source_instances:
                    instance_record = dict(record)
                    instance_record.update({
                        "source_instance_index": source_instance["instance_index"],
                        "relative_location_cm": source_instance["relative_location_cm"],
                        "relative_rotation_deg": source_instance["relative_rotation_deg"],
                        "relative_scale": source_instance["relative_scale"],
                    })
                    hism_groups[key].append(instance_record)
                continue
            if individual:
                static_components.append(record)
                continue
            key = (record["mesh_path"], _material_key(record["materials"]))
            hism_groups[key].append(record)

    groups = []
    for (mesh_path, material_signature), instances in sorted(hism_groups.items()):
        groups.append({
            "mesh_path": mesh_path,
            "material_signature_sha256": material_signature,
            "materials": instances[0]["materials"],
            "instance_count": len(instances),
            "instances": instances,
        })

    return {
        "$schema": PLAN_SCHEMA,
        "status": "PASS__OFFLINE_GROUPING_PLAN_ONLY__NO_CONTENT_CREATED",
        "source_map": SOURCE_MAP,
        "source_map_sha256": SOURCE_MAP_SHA256,
        "source_manifest_sha256": canonical_sha256(payload),
        "train_datum_cm": TRAIN_DATUM_CM,
        "authority_policy": (
            "current OneFactory Press layout/gameplay authority remains sole authority; "
            "legacy LBPressTrainAStation is excluded"
        ),
        "presentation_policy": {
            "represents_process_wip": False,
            "collision": "NoCollision",
            "can_ever_affect_navigation": False,
            "save_game_fields": False,
        },
        "source_summary": summary,
        "hism_group_count": len(groups),
        "hism_instance_count": sum(group["instance_count"] for group in groups),
        "static_component_count": len(static_components),
        "text_component_count": len(text_components),
        "hism_groups": groups,
        "static_components": static_components,
        "text_components": text_components,
        "v449_pixel_fidelity_fallback": {
            "mesh": V449_RUNTIME_MESH,
            "mesh_sha256": V449_RUNTIME_MESH_SHA256,
            "relative_location_cm": V449_AGGREGATE_RELATIVE_LOCATION_CM,
            "relative_scale": V449_AGGREGATE_RELATIVE_SCALE,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    evidence = validate_preserved_evidence(args.project_root)
    result: dict[str, Any] = {"evidence": evidence}
    if args.manifest:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        validate_manifest_asset_files(args.project_root, manifest)
        result["materialization_plan"] = compile_materialization_plan(manifest)
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        if args.output.exists():
            raise ContractError(f"Refusing to overwrite output: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
