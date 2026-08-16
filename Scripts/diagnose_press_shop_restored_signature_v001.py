"""Read-only row-level diagnosis of v438/restored canonical signature drift."""
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
OUT = ROOT / "Saved/Audits/PressShopRestoration/FullFactoryRestored_v001/signature_diagnostic_v001.json"
SOURCE_SHA = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def raw_numbers(values):
    return [round(float(value), 4) for value in values]


def normalized_numbers(values):
    result = []
    for value in values:
        rounded = round(float(value), 4)
        result.append(0.0 if abs(rounded) < 0.00005 else rounded)
    return result


def normalized_object_path(path):
    for map_path in (SOURCE_MAP, RESTORED_MAP):
        asset_name = map_path.rsplit("/", 1)[-1]
        prefix = f"{map_path}.{asset_name}"
        if path.startswith(prefix):
            return "<DUPLICATED_WORLD>" + path[len(prefix):]
    return path


def rows_for_loaded_map():
    rows = []
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        visuals = []
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = component.static_mesh
            material_paths = []
            for index in range(component.get_num_materials()):
                material = component.get_material(index)
                material_paths.append(material.get_path_name() if material else "")
            visuals.append({
                "mesh": mesh.get_path_name().split(".", 1)[0] if mesh else "",
                "materials": material_paths,
            })
        visuals.sort(key=lambda value: json.dumps(value, sort_keys=True, separators=(",", ":")))
        rows.append({
            "label": actor.get_actor_label(),
            "class": actor.get_class().get_name(),
            "tags": sorted(str(tag) for tag in actor.tags),
            "location_cm": raw_numbers(actor.get_actor_location().to_tuple()),
            "rotation_deg": raw_numbers(actor.get_actor_rotation().to_tuple()),
            "scale": raw_numbers(actor.get_actor_scale3d().to_tuple()),
            "visual_components": visuals,
        })
    return rows


def project(row, normalize_numbers=False, normalize_paths=False, omit_materials=False):
    result = json.loads(json.dumps(row))
    if normalize_numbers:
        for key in ("location_cm", "rotation_deg", "scale"):
            result[key] = normalized_numbers(result[key])
    for component in result["visual_components"]:
        if omit_materials:
            component.pop("materials", None)
        elif normalize_paths:
            component["materials"] = [normalized_object_path(path) for path in component["materials"]]
    result["visual_components"].sort(key=lambda value: json.dumps(value, sort_keys=True, separators=(",", ":")))
    return result


def encoded(row):
    return json.dumps(row, sort_keys=True, separators=(",", ":"))


def comparison(source_rows, restored_rows, **projection):
    source = Counter(encoded(project(row, **projection)) for row in source_rows)
    restored = Counter(encoded(project(row, **projection)) for row in restored_rows)
    source_only = list((source - restored).elements())
    restored_only = list((restored - source).elements())
    source_blob = "\n".join(sorted(source.elements())).encode("utf-8")
    restored_blob = "\n".join(sorted(restored.elements())).encode("utf-8")
    return {
        "equal": source == restored,
        "source_signature_sha256": hashlib.sha256(source_blob).hexdigest().upper(),
        "restored_signature_sha256": hashlib.sha256(restored_blob).hexdigest().upper(),
        "source_only_count": len(source_only),
        "restored_only_count": len(restored_only),
        "source_only_sample": [json.loads(value) for value in source_only[:12]],
        "restored_only_sample": [json.loads(value) for value in restored_only[:12]],
    }


def main():
    if sha256(SOURCE_FILE) != SOURCE_SHA:
        raise RuntimeError("protected v438 hash drift")
    restored_sha_before = sha256(RESTORED_FILE)

    unreal.EditorLoadingAndSavingUtils.load_map(RESTORED_MAP)
    restored_rows = rows_for_loaded_map()
    unreal.collect_garbage()
    unreal.EditorLoadingAndSavingUtils.load_map(SOURCE_MAP)
    source_rows = rows_for_loaded_map()

    payload = {
        "$schema": "cairnwell/audit/press-shop-restored-signature-diagnostic-v001/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "READ_ONLY_DIAGNOSTIC",
        "source_actor_count": len(source_rows),
        "restored_actor_count": len(restored_rows),
        "comparisons": {
            "raw_validator_fields": comparison(source_rows, restored_rows),
            "signed_zero_normalized": comparison(source_rows, restored_rows, normalize_numbers=True),
            "world_path_normalized": comparison(source_rows, restored_rows, normalize_paths=True),
            "signed_zero_and_world_path_normalized": comparison(
                source_rows, restored_rows, normalize_numbers=True, normalize_paths=True
            ),
            "structural_without_materials": comparison(
                source_rows, restored_rows, normalize_numbers=True, omit_materials=True
            ),
        },
        "source_sha256_after": sha256(SOURCE_FILE),
        "restored_sha256_before": restored_sha_before,
        "restored_sha256_after": sha256(RESTORED_FILE),
        "map_saved": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log(json.dumps(payload, indent=2))


main()
unreal.SystemLibrary.quit_editor()
