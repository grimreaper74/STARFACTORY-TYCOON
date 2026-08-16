"""Read-only Unreal audit for the exact v438 tagged Train A visual source.

Run only after the offline contract/tests pass and an explicit Unreal green-light.
The script never saves a map or asset, never spawns/destroys an actor, and refuses
to overwrite its one-shot manifest.  The serialized LBPressTrainAStation identity
is recorded but its *current* constructor components are deliberately not read:
that native class acquired later v700+/Meshy-era art and is not source evidence.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import unreal


ROOT = Path(unreal.Paths.project_dir())
SCRIPT_DIR = ROOT / "Scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from one_factory_detailed_press_v001_contract import (  # noqa: E402
    ContractError,
    EXPECTED_ACTOR_COUNT,
    LEGACY_AUTHORITY_CLASS,
    LEGACY_AUTHORITY_LABEL,
    RAW_MANIFEST_SCHEMA,
    SOURCE_CAPTURE_VISUAL_ACTOR_SIGNATURE_SHA256,
    SOURCE_MAP,
    SOURCE_MAP_SHA256,
    TRAIN_DATUM_CM,
    TRAIN_SCOPE_TAG,
    canonical_sha256,
    forbidden_reference_reason,
    validate_extraction_manifest,
    validate_preserved_evidence,
)


SOURCE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
PROTECTED_FILES = {
    "source_v438": SOURCE_FILE,
    "restored_v001": ROOT / "Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap",
    "current_v913": ROOT / "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap",
}
EXPECTED_PROTECTED_HASHES = {
    "source_v438": SOURCE_MAP_SHA256,
    "restored_v001": "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5",
    "current_v913": "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6",
}
OUT = (
    ROOT
    / "Saved/Audits/OneFactory/DetailedPressPresentation_v001/"
    "v438_train_a_source_manifest_v001.json"
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def vec(value: Any) -> list[float]:
    return [float(value.x), float(value.y), float(value.z)]


def rot(value: Any) -> list[float]:
    return [float(value.roll), float(value.pitch), float(value.yaw)]


def colour(value: Any) -> list[float]:
    return [float(value.r), float(value.g), float(value.b), float(value.a)]


def object_path(value: Any) -> str:
    return value.get_path_name() if value else ""


def relative_location(world_location: Any) -> list[float]:
    return [
        float(world_location.x) - TRAIN_DATUM_CM[0],
        float(world_location.y) - TRAIN_DATUM_CM[1],
        float(world_location.z) - TRAIN_DATUM_CM[2],
    ]


def transform_record(transform: Any) -> dict[str, list[float]]:
    location = transform.translation
    rotation = transform.rotation.rotator()
    scale = transform.scale3d
    return {
        "world_location_cm": vec(location),
        "world_rotation_deg": rot(rotation),
        "world_scale": vec(scale),
        "relative_location_cm": relative_location(location),
        "relative_rotation_deg": rot(rotation),
        "relative_scale": vec(scale),
    }


def unpack_instance_transform(result: Any) -> Any:
    """UE Python versions return either Transform or (success, Transform)."""
    if isinstance(result, tuple):
        if len(result) == 2 and isinstance(result[0], bool):
            if not result[0]:
                raise ContractError("Instanced-mesh transform query returned failure")
            return result[1]
        if len(result) == 2 and isinstance(result[1], bool):
            if not result[1]:
                raise ContractError("Instanced-mesh transform query returned failure")
            return result[0]
        if not result:
            raise ContractError("Instanced-mesh transform query returned no value")
        return result[-1]
    if result is None:
        raise ContractError("Instanced-mesh transform query returned None")
    return result


def actor_transform(actor: Any) -> dict[str, list[float]]:
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    return {
        "world_location_cm": vec(location),
        "world_rotation_deg": rot(rotation),
        "world_scale": vec(scale),
        "relative_location_cm": relative_location(location),
        "relative_rotation_deg": rot(rotation),
        "relative_scale": vec(scale),
    }


def component_transform(component: Any) -> dict[str, list[float]]:
    location = component.get_world_location()
    rotation = component.get_world_rotation()
    scale = component.get_world_scale()
    return {
        "world_location_cm": vec(location),
        "world_rotation_deg": rot(rotation),
        "world_scale": vec(scale),
        "relative_location_cm": relative_location(location),
        "relative_rotation_deg": rot(rotation),
        "relative_scale": vec(scale),
    }


def material_descriptor(material: Any) -> dict[str, Any]:
    if not material:
        return {
            "object_path": "",
            "class_path": "",
            "parent_path": "",
            "map_owned": False,
            "scalar_parameters": {},
            "vector_parameters": {},
            "texture_parameters": {},
        }

    path = object_path(material)
    parent = None
    try:
        parent = material.get_editor_property("parent")
    except Exception:
        parent = None
    parent_path = object_path(parent)
    scalar_parameters: dict[str, float] = {}
    vector_parameters: dict[str, list[float]] = {}
    texture_parameters: dict[str, str] = {}
    editing = unreal.MaterialEditingLibrary
    parameter_source = parent or material
    try:
        for name in editing.get_scalar_parameter_names(parameter_source):
            scalar_parameters[str(name)] = float(
                editing.get_material_instance_scalar_parameter_value(material, name)
            )
        for name in editing.get_vector_parameter_names(parameter_source):
            vector_parameters[str(name)] = colour(
                editing.get_material_instance_vector_parameter_value(material, name)
            )
        for name in editing.get_texture_parameter_names(parameter_source):
            texture = editing.get_material_instance_texture_parameter_value(material, name)
            texture_parameters[str(name)] = object_path(texture)
    except Exception as error:
        # A base Material has no instance overrides; this is evidence, not mutation.
        unreal.log_warning(f"Material parameter audit skipped for {path}: {error}")

    return {
        "object_path": path,
        "class_path": material.get_class().get_path_name(),
        "parent_path": parent_path,
        "map_owned": path.startswith(SOURCE_MAP + ".") or path.startswith(SOURCE_MAP + ":"),
        "scalar_parameters": dict(sorted(scalar_parameters.items())),
        "vector_parameters": dict(sorted(vector_parameters.items())),
        "texture_parameters": dict(sorted(texture_parameters.items())),
    }


def source_instance_records(component: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(int(component.get_instance_count())):
        # World-space capture avoids inheriting the protected map's component hierarchy.
        transform = unpack_instance_transform(component.get_instance_transform(index, True))
        rows.append({"instance_index": index, **transform_record(transform)})
    return rows


def component_tags(component: Any) -> list[str]:
    try:
        return [str(value) for value in component.get_editor_property("component_tags")]
    except Exception:
        return []


def scene_component_record(component: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "component_name": component.get_name(),
        "class_path": component.get_class().get_path_name(),
        "component_tags": component_tags(component),
        "visual_kind": "non_visual",
        **component_transform(component),
    }
    try:
        record["mobility"] = str(component.get_editor_property("mobility"))
    except Exception:
        record["mobility"] = ""
    try:
        record["visible"] = bool(component.get_editor_property("visible"))
        record["hidden_in_game"] = bool(component.get_editor_property("hidden_in_game"))
    except Exception:
        record["visible"] = True
        record["hidden_in_game"] = False

    if isinstance(component, unreal.StaticMeshComponent):
        mesh = component.static_mesh
        record["visual_kind"] = (
            "instanced_static_mesh"
            if isinstance(component, unreal.InstancedStaticMeshComponent)
            else "static_mesh"
        )
        record["mesh_path"] = object_path(mesh).split(".", 1)[0]
        record["materials"] = [
            material_descriptor(component.get_material(index))
            for index in range(component.get_num_materials())
        ]
        try:
            record["collision_enabled"] = str(component.get_collision_enabled())
        except Exception:
            record["collision_enabled"] = ""
        try:
            record["cast_shadow"] = bool(component.get_editor_property("cast_shadow"))
            record["can_ever_affect_navigation"] = bool(
                component.get_editor_property("can_ever_affect_navigation")
            )
        except Exception:
            record["cast_shadow"] = True
            record["can_ever_affect_navigation"] = False
        if isinstance(component, unreal.InstancedStaticMeshComponent):
            record["source_instance_count"] = int(component.get_instance_count())
            record["source_instances"] = source_instance_records(component)
    elif isinstance(component, unreal.TextRenderComponent):
        record["visual_kind"] = "text"
        record["text"] = str(component.get_editor_property("text"))
        record["font_path"] = object_path(component.get_editor_property("font"))
        record["materials"] = [material_descriptor(component.get_material(0))]
        record["world_size"] = float(component.get_editor_property("world_size"))
        record["text_render_color"] = colour(
            component.get_editor_property("text_render_color")
        )
    return record


def seed_projection(actor: Any, class_name: str, tags: list[str]) -> dict[str, Any]:
    origin, extent = actor.get_actor_bounds(False)
    return {
        "label": actor.get_actor_label(),
        "class": class_name,
        "location_cm": vec(actor.get_actor_location()),
        "bounds_origin_cm": vec(origin),
        "bounds_extent_cm": vec(extent),
        "tags": tags,
    }


def actor_record(actor: Any) -> dict[str, Any]:
    label = actor.get_actor_label()
    class_name = actor.get_class().get_name()
    tags = [str(value) for value in actor.tags]
    record: dict[str, Any] = {
        "label": label,
        "class_name": class_name,
        "class_path": actor.get_class().get_path_name(),
        "tags": tags,
        **actor_transform(actor),
    }
    if class_name == LEGACY_AUTHORITY_CLASS:
        if label != LEGACY_AUTHORITY_LABEL:
            raise ContractError(f"Unexpected legacy authority identity: {label}")
        record["materialization_policy"] = "excluded_current_native_constructor"
        record["exclusion_reason"] = (
            "The serialized v438 authority identity is real, but its current native "
            "constructor art is later v700+/Meshy-era and is not source evidence."
        )
        record["components"] = []
        return record

    record["materialization_policy"] = "eligible_visual_only"
    record["seed_projection"] = seed_projection(actor, class_name, tags)
    components = actor.get_components_by_class(unreal.SceneComponent)
    record["components"] = sorted(
        (scene_component_record(component) for component in components),
        key=lambda row: (row["component_name"], row["class_path"]),
    )
    return record


def references_from_actor(record: dict[str, Any]) -> list[str]:
    references: list[str] = []
    for component in record.get("components", []):
        for key in ("mesh_path", "font_path"):
            if component.get(key):
                references.append(str(component[key]))
        for material in component.get("materials", []):
            for key in ("object_path", "parent_path"):
                if material.get(key):
                    references.append(str(material[key]))
            references.extend(
                str(value) for value in material.get("texture_parameters", {}).values()
                if value
            )
    return references


def package_from_reference(reference: str) -> str:
    normalized = str(reference).replace("\\", "/")
    if not normalized.startswith(("/Game/", "/Engine/", "/Script/")):
        return ""
    return normalized.split(":", 1)[0].split(".", 1)[0]


def project_asset_file(package: str) -> Path:
    relative = package[len("/Game/") :]
    asset = ROOT / "Content" / (relative + ".uasset")
    if asset.is_file():
        return asset
    level = ROOT / "Content" / (relative + ".umap")
    if level.is_file():
        return level
    raise ContractError(f"Referenced project package has no file: {package}")


def build_project_asset_provenance(references: set[str]) -> list[dict[str, Any]]:
    packages = sorted({
        package_from_reference(reference)
        for reference in references
        if package_from_reference(reference).startswith("/Game/")
        and package_from_reference(reference) != SOURCE_MAP
    })
    rows: list[dict[str, Any]] = []
    for package in packages:
        reason = forbidden_reference_reason(package)
        if reason:
            raise ContractError(f"Forbidden project package [{package}]: {reason}")
        path = project_asset_file(package)
        rows.append({
            "package_path": package,
            "file_relative": path.relative_to(ROOT).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": file_sha256(path),
            "provenance_policy": "PINNED_PRE_MESHY_SOURCE_DEPENDENCY",
        })
    return rows


def main() -> None:
    validate_preserved_evidence(ROOT)
    if OUT.exists():
        raise ContractError(f"Refusing to overwrite one-shot manifest: {OUT}")
    protected_before = {label: file_sha256(path) for label, path in PROTECTED_FILES.items()}
    if protected_before != EXPECTED_PROTECTED_HASHES:
        raise ContractError(
            "Protected map hash drift before load: " + json.dumps(protected_before)
        )

    unreal.EditorLoadingAndSavingUtils.load_map(SOURCE_MAP)
    actor_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    matches = [
        actor for actor in actor_api.get_all_level_actors()
        if TRAIN_SCOPE_TAG in {str(value) for value in actor.tags}
    ]
    if len(matches) != EXPECTED_ACTOR_COUNT:
        raise ContractError(f"Expected exact 338 tagged Train A actors, found {len(matches)}")
    records = sorted((actor_record(actor) for actor in matches), key=lambda row: row["label"])
    if len({row["label"] for row in records}) != EXPECTED_ACTOR_COUNT:
        raise ContractError("Tagged Train A actor labels are not unique")

    visual_seed = [
        row["seed_projection"] for row in records
        if row["class_name"] != LEGACY_AUTHORITY_CLASS
    ]
    visual_seed_signature = canonical_sha256(
        sorted(visual_seed, key=lambda row: (row["label"], row["class"]))
    )
    if visual_seed_signature != SOURCE_CAPTURE_VISUAL_ACTOR_SIGNATURE_SHA256:
        raise ContractError(
            "Exact 337 visual actor signature differs from preserved v452 evidence: "
            + visual_seed_signature
        )

    forbidden: list[dict[str, str]] = []
    references: set[str] = set()
    for record in records:
        for reference in references_from_actor(record):
            references.add(reference)
            reason = forbidden_reference_reason(reference)
            if reason:
                forbidden.append({"reference": reference, "reason": reason})
    if forbidden:
        raise ContractError("Forbidden Meshy/vendor/developer/v700+ reference(s): " + json.dumps(forbidden))

    protected_after = {label: file_sha256(path) for label, path in PROTECTED_FILES.items()}
    if protected_after != protected_before:
        raise ContractError("A protected map changed during read-only extraction")
    payload = {
        "$schema": RAW_MANIFEST_SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__EXACT_V438_TRAIN_A_SOURCE_AUDIT__READ_ONLY__NOT_MATERIALIZED",
        "source_map": SOURCE_MAP,
        "source_map_sha256_before": protected_before["source_v438"],
        "source_map_sha256_after": protected_after["source_v438"],
        "source_map_saved": False,
        "scope_tag": TRAIN_SCOPE_TAG,
        "train_datum_cm": TRAIN_DATUM_CM,
        "actor_count": len(records),
        "visual_actor_count": len(visual_seed),
        "visual_seed_signature_sha256": visual_seed_signature,
        "reference_count": len(references),
        "references": sorted(references),
        "project_asset_provenance": build_project_asset_provenance(references),
        "forbidden_references": [],
        "protected_map_hashes_before": protected_before,
        "protected_map_hashes_after": protected_after,
        "actors": records,
    }
    validate_extraction_manifest(payload)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log(payload["status"])


main()
unreal.SystemLibrary.quit_editor()
