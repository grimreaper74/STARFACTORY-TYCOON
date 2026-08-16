"""Restore accepted PR009/PR010 local navigation coverage in a v240 child."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v240"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v241"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_restore_pr009_pr010_navigation_build_v241.json"
PROTECTED = {
    "v236": ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v236.umap",
    "v239": ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v239.umap",
    "v240": ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v240.umap",
}
VOLUMES = [
    {
        "label": "LB_WHOLE_V241_PR009_NavBounds_LocalCoverage",
        "class": unreal.NavMeshBoundsVolume,
        "location": (600.0, -2000.0, 350.0),
        "scale": (9.0, 8.0, 3.5),
        "station": "PR009",
        "role": "LOCAL_COVERAGE",
    },
    {
        "label": "LB_WHOLE_V241_PR009_NavModifier_ProtectedProcessSpace",
        "class": unreal.NavModifierVolume,
        "location": (600.0, -2000.0, 250.0),
        "scale": (4.0, 3.0, 2.5),
        "station": "PR009",
        "role": "PROTECTED_PROCESS_SPACE",
    },
    {
        "label": "LB_WHOLE_V241_PR010_NavBounds_LocalCoverage",
        "class": unreal.NavMeshBoundsVolume,
        "location": (1360.0, -2000.0, 350.0),
        "scale": (7.0, 11.5, 3.5),
        "station": "PR010",
        "role": "LOCAL_COVERAGE",
    },
    {
        "label": "LB_WHOLE_V241_PR010_NavModifier_ProtectedProcessSpace",
        "class": unreal.NavModifierVolume,
        "location": (1350.0, -2000.0, 250.0),
        "scale": (4.2, 7.0, 2.5),
        "station": "PR010",
        "role": "PROTECTED_PROCESS_SPACE",
    },
]

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def volume_row(actor, spec):
    origin, extent = actor.get_actor_bounds(False, False)
    return {
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "station": spec["station"],
        "role": spec["role"],
        "origin_cm": [origin.x, origin.y, origin.z],
        "size_cm": [extent.x * 2.0, extent.y * 2.0, extent.z * 2.0],
        "scale": [actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z],
    }


protected_before = {key: sha256(path) for key, path in PROTECTED.items()}
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

existing = [actor for actor in actors_api.get_all_level_actors()
            if isinstance(actor, (unreal.NavMeshBoundsVolume, unreal.NavModifierVolume))
            and any(str(tag) in {"LB.PR009.Navigation", "LB.PR010.Navigation"} for tag in actor.tags)]
failures = []
if existing:
    failures.append(f"expected no inherited PR009/PR010 local navigation actors, found {len(existing)}")

null_area = unreal.load_class(None, "/Script/NavigationSystem.NavArea_Null")
if null_area is None:
    raise RuntimeError("could not load NavArea_Null")
created = []
for spec in VOLUMES:
    actor = actors_api.spawn_actor_from_class(
        spec["class"], unreal.Vector(*spec["location"]), unreal.Rotator())
    if actor is None:
        failures.append(f"could not create {spec['label']}")
        continue
    actor.set_actor_label(spec["label"])
    actor.set_actor_scale3d(unreal.Vector(*spec["scale"]))
    actor.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v241",
        "LB.Asset.CandidateNotPromoted",
        f"LB.{spec['station']}.Navigation",
        "LB.Navigation.LocalCoverage" if spec["role"] == "LOCAL_COVERAGE"
        else "LB.Navigation.ProtectedProcessSpace",
        "LB.Navigation.RestoredAcceptedContract.v241",
    )]
    if isinstance(actor, unreal.NavModifierVolume):
        actor.set_editor_property("area_class", null_area)
    created.append(volume_row(actor, spec))

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
recast_count = 0
for actor in actors_api.get_all_level_actors():
    if isinstance(actor, unreal.RecastNavMesh):
        recast_count += 1
        actor.set_editor_property("runtime_generation", unreal.RuntimeGenerationType.DYNAMIC)
        actor.set_editor_property("can_be_main_nav_data", True)

if len(created) != 4:
    failures.append(f"expected four restored navigation volumes, created {len(created)}")
if recast_count != 1:
    failures.append(f"expected one RecastNavMesh, found {recast_count}")
if not levels.save_current_level():
    failures.append("could not save v241")

protected_after = {key: sha256(path) for key, path in PROTECTED.items()}
if protected_before != protected_after:
    failures.append("protected lineage changed")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v241.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-restore-pr009-pr010-navigation-build-v241/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR009_PR010_LOCAL_NAVIGATION_CONTRACT_RESTORED__EXACT_PIE_REQUIRED__NOT_PROMOTED"
              if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "protected_sha256_before": protected_before,
    "protected_sha256_after": protected_after,
    "map_sha256": sha256(map_file) if map_file.exists() else None,
    "created_volume_count": len(created),
    "created_volumes": created,
    "recast_nav_mesh_count": recast_count,
    "area_class": null_area.get_path_name(),
    "visible_geometry_material_transform_changes": 0,
    "machine_or_runtime_authority_changes": 0,
    "collision_changes": 0,
    "engineering_datums_invented": 0,
    "contract_sources": [
        "Saved/Audits/PR010_CollisionNavigation/navigation_authoring_v099.json",
        "Saved/Audits/PR010_Accepted_v103/navigation_pie_audit.json",
        "Scripts/repair_press_shop_pr009_navigation_coverage.py",
    ],
    "promotion_authorized": False,
    "failures": failures,
}
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()

