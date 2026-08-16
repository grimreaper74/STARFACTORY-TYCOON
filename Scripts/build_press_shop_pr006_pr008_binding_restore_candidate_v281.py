"""Restore retained PR006-PR008 native mover attachments in a fresh v273 child."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v281"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr006_pr008_binding_restore_build_v281.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v281.umap"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def station_of(actor_class, actors):
    matches = [actor for actor in actors if isinstance(actor, actor_class)]
    if len(matches) != 1:
        raise RuntimeError(f"expected one {actor_class.__name__}, found {len(matches)}")
    return matches[0]


def bind_group(station, specification, by_label, authority_tag):
    components = {component.get_name(): component for component in station.get_components_by_class(unreal.SceneComponent)}
    records = []
    for component_name, labels in specification.items():
        component = components.get(component_name)
        if component is None:
            raise RuntimeError(f"missing component {component_name}")
        datum = by_label.get(labels[0])
        if datum is None:
            raise RuntimeError(f"missing datum actor {labels[0]}")
        component.set_world_location(datum.get_actor_location(), False, False)
        component.set_world_rotation(datum.get_actor_rotation(), False, False)
        for label in labels:
            actor = by_label.get(label)
            if actor is None:
                raise RuntimeError(f"missing presentation actor {label}")
            before_location = actor.get_actor_location()
            before_rotation = actor.get_actor_rotation()
            if isinstance(actor, unreal.StaticMeshActor):
                actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
            if not actor.attach_to_component(
                    component, unreal.Name(), unreal.AttachmentRule.KEEP_WORLD,
                    unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False):
                raise RuntimeError(f"could not attach {label} to {component_name}")
            if not actor.get_actor_location().equals(before_location, 0.01):
                raise RuntimeError(f"world location changed while binding {label}")
            if not actor.get_actor_rotation().equals(before_rotation, 0.01):
                raise RuntimeError(f"world rotation changed while binding {label}")
            tags = list(actor.tags)
            if unreal.Name(authority_tag) not in tags:
                tags.append(unreal.Name(authority_tag))
            tags.extend((unreal.Name("LB.Asset.Candidate.v281"), unreal.Name("LB.Asset.CandidateNotPromoted")))
            actor.tags = tags
            records.append({"actor": label, "component": component_name, "world_transform_preserved": True})
    return records


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
parent_hash_before = sha256(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

actors = list(actors_api.get_all_level_actors())
by_label = {actor.get_actor_label(): actor for actor in actors}

pr006 = {}
for index in range(1, 10):
    pr006[f"PR006_LowerRollMover_{index:02d}"] = [f"LB_PR006_V054_PR006_LowerRoll_{index:02d}"]
for index in range(1, 11):
    pr006[f"PR006_UpperRollMover_{index:02d}"] = [f"LB_PR006_V054_PR006_UpperRoll_{index:02d}"]
pr006["PR006_UpperCassetteMover"] = [
    "LB_PR006_V054_PR006_UpperCassette_Operator", "LB_PR006_V054_PR006_UpperCassette_Drive"]
for index, suffix in enumerate(("-1_-1", "-1_+1", "+1_-1", "+1_+1"), 1):
    pr006[f"PR006_GapCylinderMover_{index:02d}"] = [f"LB_PR006_V054_PR006_GapCylinder_{suffix}"]
for index in range(1, 4):
    pr006[f"PR006_DriveMotorMover_{index:02d}"] = [f"LB_PR006_V054_PR006_DriveMotor_{index:02d}"]

pr007 = {
    "PR007_WashHoodMover": ["LB_PR007_V055_PR007_HoodWash"],
    "PR007_WashPumpMover": ["LB_PR007_V055_PR007_WashPumpMotor"],
    "PR007_LubePumpMover": ["LB_PR007_V055_PR007_LubePumpMotor"],
    "PR007_FeedRollerMover": ["LB_PR007_V055_PR007_InfeedRollLower"],
    "PR007_WashRollerMover": ["LB_PR007_V055_PR007_WashRollLower"],
    "PR007_LubeRollerMover": ["LB_PR007_V055_PR007_LubeRollLower"],
    "PR007_OutfeedRollerMover": ["LB_PR007_V055_PR007_OutfeedRollLower"],
}

pr008 = {
    "PR008_FeedRollLowerMover": ["LB_PR008_V066_SM_CA_MW_PR008_ServoFeedRoll_Lower_01", "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedSleeve_Lower_01"],
    "PR008_FeedRollUpperMover": ["LB_PR008_V066_SM_CA_MW_PR008_ServoFeedRoll_Upper_01", "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedSleeve_Upper_01"],
    "PR008_EdgeGuideOperatorMover": ["LB_PR008_V065_SM_CA_MW_PR008_EdgeGuide_Operator"],
    "PR008_EdgeGuideDriveMover": ["LB_PR008_V065_SM_CA_MW_PR008_EdgeGuide_Drive"],
    "PR008_TelescopeStage1Mover": ["LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage1_01"],
    "PR008_TelescopeStage2Mover": ["LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage2_01"],
    "PR008_TelescopeStage3Mover": ["LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage3_01"],
    "PR008_PrePunchMover": ["LB_PR008_V068_SM_CA_MW_PR008_PrePunchSlide_01"],
    "PR008_ScrapFlapMover": ["LB_PR008_V068_SM_CA_MW_PR008_PrePunchScrapFlap_01"],
    "PR008_ServiceDoorOperatorMover": ["LB_PR008_V068_SM_CA_MW_PR008_PrePunchServiceDoor_Operator"],
    "PR008_ServiceDoorDriveMover": ["LB_PR008_V068_SM_CA_MW_PR008_PrePunchServiceDoor_Drive"],
    "PR008_GuillotineMover": ["LB_PR008_V069_SM_CA_MW_PR008_ShearBladeBeam_01"],
}

records = {
    "PR006": bind_group(station_of(unreal.LBPR006Station, actors), pr006, by_label, "LB.Authority.PR006.NativeBound"),
    "PR007": bind_group(station_of(unreal.LBPR007Station, actors), pr007, by_label, "LB.Authority.PR007.NativeBound"),
    "PR008": bind_group(station_of(unreal.LBPR008Station, actors), pr008, by_label, "LB.Authority.PR008.NativeBound"),
}

if not levels.save_current_level():
    raise RuntimeError("could not save v281")
parent_hash_after = sha256(BASE_FILE)
if parent_hash_after != parent_hash_before:
    raise RuntimeError("protected v273 parent changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-pr006-pr008-binding-restore-build-v281/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__EXACT_RETAINED_MOVER_BINDINGS_RESTORED__WORLD_TRANSFORMS_UNCHANGED__RUNTIME_GATES_REQUIRED__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(MAP_FILE),
    "binding_counts": {key: len(value) for key, value in records.items()},
    "bindings": records,
    "geometry_material_light_layout_changes": 0,
    "promotion_authorized": False,
    "failures": [],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
