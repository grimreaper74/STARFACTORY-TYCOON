"""Build a fresh v233 child with readable whole-hall perimeter and roof liners."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v230"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v233"
DEST = "/Game/LineBoss/Candidates/PressShop/ShellReadability_v233/Materials"
MASTER = "/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/M_LB_PR004_NonmetalPBR_Master_v003"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_shell_readability_build_v233.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v230.umap"
WALL_LABELS = {"LB_PRESS_Wall_North", "LB_PRESS_Wall_South", "LB_PRESS_Wall_West", "LB_PRESS_Wall_East"}

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def make_material(name, tint, roughness, texture_influence):
    path = f"{DEST}/{name}"
    if library.does_asset_exist(path):
        raise RuntimeError(f"refusing to overwrite {path}")
    value = tools.create_asset(name, DEST, unreal.MaterialInstanceConstant,
                               unreal.MaterialInstanceConstantFactoryNew())
    if value is None:
        raise RuntimeError(f"could not create {path}")
    value.set_editor_property("parent", parent)
    mel.set_material_instance_vector_parameter_value(value, "SurfaceTint", unreal.LinearColor(*tint, 1.0))
    for key, scalar in {
        "TextureInfluence": texture_influence,
        "TextureScale": 12.0,
        "BaseRoughness": roughness,
        "RoughTextureInfluence": 0.26,
        "Metallic": 0.0,
        "NormalStrength": 0.20,
    }.items():
        mel.set_material_instance_scalar_parameter_value(value, key, scalar)
    mel.update_material_instance(value)
    library.save_loaded_asset(value, only_if_is_dirty=False)
    return value


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
parent_hash_before = sha256(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")
parent = library.load_asset(MASTER)
if parent is None:
    raise RuntimeError(f"missing nonmetal PBR master {MASTER}")
wall_material = make_material("MI_CA_MW_DeepGraphitePerimeterWall_v233", (0.16, 0.18, 0.21), 0.78, 0.14)
roof_material = make_material("MI_CA_MW_DeepGraphiteRoofLiner_v233", (0.115, 0.135, 0.16), 0.82, 0.12)

changes = []
failures = []
for actor in actors_api.get_all_level_actors():
    tags = [str(value) for value in actor.tags]
    label = actor.get_actor_label()
    scope = None
    replacement = None
    if label in WALL_LABELS:
        scope, replacement = "primary_perimeter_wall", wall_material
    elif "LB.Module.FactoryRoofLiner" in tags:
        scope, replacement = "front_end_roof_liner", roof_material
    if replacement is None:
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    before = component.get_material(0)
    before_path = before.get_path_name() if before else None
    if before_path != "/Game/LineBoss/Materials/M_LB_ShellCharcoal.M_LB_ShellCharcoal":
        failures.append(f"unexpected inherited material {label}={before_path}")
        continue
    collision_before = str(component.get_collision_enabled())
    component.set_material(0, replacement)
    actor.tags = [unreal.Name(value) for value in dict.fromkeys(tags + [
        "LB.Asset.Candidate.v233", "LB.VisualCorrection.ShellReadability.v233",
        "LB.Asset.CandidateNotPromoted",
    ])]
    changes.append({
        "scope": scope,
        "label": label,
        "before": before_path,
        "after": replacement.get_path_name(),
        "collision_before": collision_before,
        "collision_after": str(component.get_collision_enabled()),
    })

wall_count = sum(row["scope"] == "primary_perimeter_wall" for row in changes)
roof_count = sum(row["scope"] == "front_end_roof_liner" for row in changes)
if wall_count != 4:
    failures.append(f"expected four perimeter walls, changed {wall_count}")
if roof_count != 20:
    failures.append(f"expected twenty roof-liner panels, changed {roof_count}")
if any(row["collision_before"] != row["collision_after"] for row in changes):
    failures.append("collision policy changed")
if not levels.save_current_level():
    failures.append("could not save v233")
library.save_directory(DEST.rsplit("/", 1)[0], only_if_is_dirty=False, recursive=True)
parent_hash_after = sha256(BASE_FILE)
if parent_hash_after != parent_hash_before:
    failures.append("protected v230 parent changed")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v233.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-shell-readability-build-v233/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FOUR_PERIMETER_WALLS_AND_TWENTY_ROOF_LINERS_REFINISHED__FRESH_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(map_file) if map_file.exists() else None,
    "material_contract": {
        "walls": wall_material.get_path_name(),
        "roof": roof_material.get_path_name(),
        "finish": "restrained deep graphite nonmetallic industrial liner",
        "engineering_data": "NONE_INVENTED"
    },
    "wall_count": wall_count,
    "roof_liner_count": roof_count,
    "changes": sorted(changes, key=lambda row: (row["scope"], row["label"])),
    "geometry_transform_light_authority_machine_changes": 0,
    "collision_navigation_changes": 0,
    "rejected_non_parents": [
        "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v231",
        "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v232"
    ],
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
