"""Match retained bound donor movers to existing v273 actors by mesh and transform."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
TARGET = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273"
DONORS = {
    "PR006": "/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v208",
    "PR007": "/Game/LineBoss/Maps/LB_PressShop_PR007ReleaseArtCandidate_v209",
    "PR008": "/Game/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210",
}
EXPECTED = {
    "PR006": {"PR006_LowerRollMover", "PR006_UpperRollMover", "PR006_UpperCassetteMover", "PR006_GapCylinderMover", "PR006_DriveMotorMover"},
    "PR007": {"PR007_WashHoodMover", "PR007_WashPumpMover", "PR007_LubePumpMover", "PR007_FeedRollerMover", "PR007_WashRollerMover", "PR007_LubeRollerMover", "PR007_OutfeedRollerMover"},
    "PR008": {"PR008_FeedRollLowerMover", "PR008_FeedRollUpperMover", "PR008_EdgeGuideOperatorMover", "PR008_EdgeGuideDriveMover", "PR008_TelescopeStage1Mover", "PR008_TelescopeStage2Mover", "PR008_TelescopeStage3Mover", "PR008_PrePunchMover", "PR008_ScrapFlapMover", "PR008_ServiceDoorOperatorMover", "PR008_ServiceDoorDriveMover", "PR008_GuillotineMover"},
}
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr006_pr008_donor_mover_matches_v273.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def vec(v):
    return [float(v.x), float(v.y), float(v.z)]


def rot(v):
    return [float(v.pitch), float(v.yaw), float(v.roll)]


def mover_name(actor):
    root = actor.root_component
    parent = root.get_attach_parent() if root else None
    return parent.get_name() if parent else None


donor_records = {}
for family, map_path in DONORS.items():
    if not levels.load_level(map_path):
        raise RuntimeError(map_path)
    rows = []
    for actor in actors_api.get_all_level_actors():
        if not isinstance(actor, unreal.StaticMeshActor):
            continue
        parent = mover_name(actor)
        if not parent or not any(parent.startswith(prefix) for prefix in EXPECTED[family]):
            continue
        mesh = actor.static_mesh_component.static_mesh
        rows.append({
            "label": actor.get_actor_label(), "parent_component": parent,
            "mesh": mesh.get_path_name() if mesh else None,
            "location": vec(actor.get_actor_location()), "rotation": rot(actor.get_actor_rotation()),
            "scale": vec(actor.get_actor_scale3d()),
        })
    donor_records[family] = rows

if not levels.load_level(TARGET):
    raise RuntimeError(TARGET)
target_actors = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.StaticMeshActor)]
target_rows = []
for actor in target_actors:
    mesh = actor.static_mesh_component.static_mesh
    target_rows.append({
        "actor": actor, "label": actor.get_actor_label(), "mesh": mesh.get_path_name() if mesh else None,
        "location": vec(actor.get_actor_location()), "rotation": rot(actor.get_actor_rotation()), "scale": vec(actor.get_actor_scale3d()),
        "parent_component": mover_name(actor),
    })

results = {}
for family, donors in donor_records.items():
    family_rows = []
    for donor in donors:
        matches = []
        for target in target_rows:
            if target["mesh"] != donor["mesh"]:
                continue
            distance = sum((a - b) ** 2 for a, b in zip(target["location"], donor["location"])) ** 0.5
            if distance <= 0.1:
                matches.append({key: value for key, value in target.items() if key != "actor"} | {"location_error_cm": distance})
        family_rows.append({"donor": donor, "exact_target_matches": matches})
    results[family] = family_rows

payload = {
    "$schema": "cairnwell/audit/press-shop-pr006-pr008-donor-mover-matches-v273/v1",
    "target": TARGET, "donors": DONORS, "results": results,
    "summary": {family: {
        "donor_movers": len(rows),
        "unique_exact_matches": sum(1 for row in rows if len(row["exact_target_matches"]) == 1),
        "missing": sum(1 for row in rows if not row["exact_target_matches"]),
        "ambiguous": sum(1 for row in rows if len(row["exact_target_matches"]) > 1),
    } for family, rows in results.items()},
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.SystemLibrary.quit_editor()
