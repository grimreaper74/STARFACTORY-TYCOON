"""Apply the isolated v238 shell tonal study to the retained v241 machine-complete parent."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v241"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v242"
WALL_MATERIAL = "/Game/LineBoss/Candidates/PressShop/ShellReadability_v238/Materials/MI_CA_MW_IndustrialGraphiteWall_v238"
ROOF_MATERIAL = "/Game/LineBoss/Candidates/PressShop/ShellReadability_v238/Materials/MI_CA_MW_IndustrialGraphiteRoof_v238"
WALL_SOURCE = "/Game/LineBoss/Candidates/PressShop/ShellReadability_v233/Materials/MI_CA_MW_DeepGraphitePerimeterWall_v233.MI_CA_MW_DeepGraphitePerimeterWall_v233"
ROOF_SOURCE = "/Game/LineBoss/Candidates/PressShop/ShellReadability_v233/Materials/MI_CA_MW_DeepGraphiteRoofLiner_v233.MI_CA_MW_DeepGraphiteRoofLiner_v233"
WALL_LABELS = {"LB_PRESS_Wall_North", "LB_PRESS_Wall_South", "LB_PRESS_Wall_West", "LB_PRESS_Wall_East"}
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_shell_tonal_calibration_build_v242.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v241.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v242.umap"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
parent_hash_before = sha256(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")
wall_material = library.load_asset(WALL_MATERIAL)
roof_material = library.load_asset(ROOF_MATERIAL)
if wall_material is None or roof_material is None:
    raise RuntimeError("retained v238 tonal-study materials are missing")

changes = []
failures = []
for actor in actors_api.get_all_level_actors():
    tags = [str(value) for value in actor.tags]
    label = actor.get_actor_label()
    scope = None
    expected = None
    replacement = None
    if label in WALL_LABELS:
        scope, expected, replacement = "primary_perimeter_wall", WALL_SOURCE, wall_material
    elif "LB.Module.FactoryRoofLiner" in tags:
        scope, expected, replacement = "complete_roof_liner_grid", ROOF_SOURCE, roof_material
    if replacement is None:
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    before = component.get_material(0)
    before_path = before.get_path_name() if before else None
    if before_path != expected:
        failures.append(f"unexpected inherited material {label}={before_path}")
        continue
    transform_before = str(actor.get_actor_transform())
    collision_before = str(component.get_collision_enabled())
    navigation_before = bool(component.get_editor_property("can_ever_affect_navigation"))
    component.set_material(0, replacement)
    actor.tags = [unreal.Name(value) for value in dict.fromkeys(tags + [
        "LB.Asset.Candidate.v242",
        "LB.VisualCorrection.ShellTonalCalibration.v242",
        "LB.Asset.CandidateNotPromoted",
    ])]
    changes.append({
        "scope": scope,
        "label": label,
        "before": before_path,
        "after": replacement.get_path_name(),
        "transform_before": transform_before,
        "transform_after": str(actor.get_actor_transform()),
        "collision_before": collision_before,
        "collision_after": str(component.get_collision_enabled()),
        "navigation_before": navigation_before,
        "navigation_after": bool(component.get_editor_property("can_ever_affect_navigation")),
    })

wall_count = sum(row["scope"] == "primary_perimeter_wall" for row in changes)
roof_count = sum(row["scope"] == "complete_roof_liner_grid" for row in changes)
if wall_count != 4:
    failures.append(f"expected four perimeter walls, changed {wall_count}")
if roof_count != 91:
    failures.append(f"expected ninety-one roof-liner panels, changed {roof_count}")
if any(row["transform_before"] != row["transform_after"] for row in changes):
    failures.append("geometry transform changed")
if any(row["collision_before"] != row["collision_after"] for row in changes):
    failures.append("collision policy changed")
if any(row["navigation_before"] != row["navigation_after"] for row in changes):
    failures.append("navigation relevance changed")
if not levels.save_current_level():
    failures.append("could not save v242")
parent_hash_after = sha256(BASE_FILE)
if parent_hash_after != parent_hash_before:
    failures.append("protected v241 parent changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-shell-tonal-calibration-build-v242/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V241_MACHINE_COMPLETE_PARENT_WITH_RESTRAINED_GRAPHITE_GREY_SHELL__FRESH_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "wall_count": wall_count,
    "roof_liner_count": roof_count,
    "material_contract": {
        "walls": wall_material.get_path_name(),
        "roof": roof_material.get_path_name(),
        "source_study": "v238 isolated tonal study; no v238 map ancestry",
        "finish": "restrained industrial graphite-grey nonmetallic shell",
        "engineering_data": "NONE_INVENTED",
    },
    "changes": sorted(changes, key=lambda row: (row["scope"], row["label"])),
    "geometry_transform_light_authority_machine_changes": 0,
    "collision_navigation_changes": 0,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
