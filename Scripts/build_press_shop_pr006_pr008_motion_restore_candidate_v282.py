"""Restore omitted retained PR006-PR008 moving subassemblies in a fresh v273 child."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v282"
DONORS = {
    "PR006": "/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v208",
    "PR007": "/Game/LineBoss/Maps/LB_PressShop_PR007ReleaseArtCandidate_v209",
    "PR008": "/Game/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210",
}
PREFIXES = {
    "PR006": ("PR006_LowerRollMover", "PR006_UpperRollMover", "PR006_UpperCassetteMover", "PR006_GapCylinderMover", "PR006_DriveMotorMover"),
    "PR007": ("PR007_WashHoodMover", "PR007_WashPumpMover", "PR007_LubePumpMover", "PR007_FeedRollerMover", "PR007_WashRollerMover", "PR007_LubeRollerMover", "PR007_OutfeedRollerMover"),
    "PR008": ("PR008_FeedRollLowerMover", "PR008_FeedRollUpperMover", "PR008_EdgeGuideOperatorMover", "PR008_EdgeGuideDriveMover", "PR008_TelescopeStage1Mover", "PR008_TelescopeStage2Mover", "PR008_TelescopeStage3Mover", "PR008_PrePunchMover", "PR008_ScrapFlapMover", "PR008_ServiceDoorOperatorMover", "PR008_ServiceDoorDriveMover", "PR008_GuillotineMover"),
}
STATION_CLASSES = {"PR006": unreal.LBPR006Station, "PR007": unreal.LBPR007Station, "PR008": unreal.LBPR008Station}
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr006_pr008_motion_restore_build_v282.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v282.umap"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def vec(v):
    return [float(v.x), float(v.y), float(v.z)]


def rot(v):
    return [float(v.pitch), float(v.yaw), float(v.roll)]


def mover_name(actor):
    parent = actor.root_component.get_attach_parent() if actor.root_component else None
    return parent.get_name() if parent else None


protected = {"base": BASE_FILE}
for family, donor in DONORS.items():
    protected[family] = ROOT / ("Content" + donor.removeprefix("/Game").replace("/", "\\") + ".umap")
protected_before = {key: sha256(path) for key, path in protected.items()}

records = {}
for family, donor in DONORS.items():
    if not levels.load_level(donor):
        raise RuntimeError(donor)
    rows = []
    for actor in actors_api.get_all_level_actors():
        if not isinstance(actor, unreal.StaticMeshActor):
            continue
        tags = [str(tag) for tag in actor.tags]
        parent = mover_name(actor)
        parent_component = actor.root_component.get_attach_parent() if actor.root_component else None
        is_attached_mover = parent and parent.startswith(PREFIXES[family])
        is_pr008_direct = family == "PR008" and any(tag in tags for tag in (
            "LB.Presentation.PR008.LoopRoll", "LB.Presentation.PR008.DischargeRoll",
            "LB.HMI.PR008.TouchSurface", "LB.HMI.PR008.LocalControls", "LB.HMI.PR008.EStop"))
        if not is_attached_mover and not is_pr008_direct:
            continue
        component = actor.static_mesh_component
        mesh = component.static_mesh
        if mesh is None:
            raise RuntimeError(f"missing mesh {family}:{actor.get_actor_label()}")
        rows.append({
            "label": actor.get_actor_label(), "parent_component": parent if is_attached_mover else None,
            "parent_location": vec(parent_component.get_world_location()) if is_attached_mover else None,
            "parent_rotation": rot(parent_component.get_world_rotation()) if is_attached_mover else None,
            "mesh": mesh.get_path_name(), "materials": [
                component.get_material(index).get_path_name() if component.get_material(index) else None
                for index in range(component.get_num_materials())],
            "location": vec(actor.get_actor_location()), "rotation": rot(actor.get_actor_rotation()),
            "scale": vec(actor.get_actor_scale3d()), "tags": tags,
            "collision_enabled": component.get_collision_enabled(),
            "collision_profile": component.get_collision_profile_name(),
            "affects_navigation": bool(component.get_editor_property("can_ever_affect_navigation")),
            "cast_shadow": bool(component.get_editor_property("cast_shadow")),
        })
    records[family] = rows

if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

target_actors = list(actors_api.get_all_level_actors())
stations = {}
for family, actor_class in STATION_CLASSES.items():
    matches = [actor for actor in target_actors if isinstance(actor, actor_class)]
    if len(matches) != 1:
        raise RuntimeError(f"expected one {family} authority, found {len(matches)}")
    stations[family] = matches[0]

spawned = {}
for family, rows in records.items():
    components = {component.get_name(): component for component in stations[family].get_components_by_class(unreal.SceneComponent)}
    spawned[family] = []
    component_datums = {}
    for row in rows:
        parent = row["parent_component"]
        if parent and parent not in component_datums:
            component_datums[parent] = (row["parent_location"], row["parent_rotation"])
    for component_name, (location, rotation) in component_datums.items():
        component = components.get(component_name)
        if component is None:
            raise RuntimeError(f"missing target component {family}:{component_name}")
        component.set_world_location(unreal.Vector(*location), False, False)
        component.set_world_rotation(unreal.Rotator(rotation[2], rotation[0], rotation[1]), False, False)
    for row in rows:
        actor = actors_api.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(*row["location"]),
            unreal.Rotator(row["rotation"][2], row["rotation"][0], row["rotation"][1]),
        )
        if actor is None:
            raise RuntimeError(f"could not restore {family}:{row['label']}")
        actor.set_actor_label(row["label"])
        actor.set_actor_scale3d(unreal.Vector(*row["scale"]))
        component = actor.static_mesh_component
        mesh = library.load_asset(row["mesh"])
        if mesh is None:
            raise RuntimeError(f"missing retained asset {row['mesh']}")
        component.set_static_mesh(mesh)
        for index, material_path in enumerate(row["materials"]):
            if material_path:
                material = library.load_asset(material_path)
                if material is None:
                    raise RuntimeError(f"missing retained material {material_path}")
                component.set_material(index, material)
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        component.set_collision_enabled(row["collision_enabled"])
        component.set_collision_profile_name(row["collision_profile"])
        component.set_editor_property("can_ever_affect_navigation", row["affects_navigation"])
        component.set_editor_property("cast_shadow", row["cast_shadow"])
        actor.tags = [unreal.Name(tag) for tag in row["tags"]] + [
            unreal.Name("LB.Integration.MotionRestore.v282"), unreal.Name("LB.Asset.Candidate.v282"),
            unreal.Name("LB.Asset.CandidateNotPromoted")]
        if row["parent_component"]:
            parent_component = components[row["parent_component"]]
            if not actor.attach_to_component(
                    parent_component, unreal.Name(), unreal.AttachmentRule.KEEP_WORLD,
                    unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False):
                raise RuntimeError(f"could not bind {row['label']} to {row['parent_component']}")
        spawned[family].append({"label": row["label"], "parent_component": row["parent_component"], "mesh": row["mesh"]})

if not levels.save_current_level():
    raise RuntimeError("could not save v282")
protected_after = {key: sha256(path) for key, path in protected.items()}
failures = []
if protected_before != protected_after:
    failures.append("protected parent or donor changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-pr006-pr008-motion-restore-build-v282/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__RETAINED_MOVING_SUBASSEMBLIES_RESTORED__EXACT_RUNTIME_COLLISION_NAVIGATION_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE, "map": MAP, "donors": DONORS,
    "protected_hashes_before": protected_before, "protected_hashes_after": protected_after,
    "map_hash": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "spawned_counts": {family: len(rows) for family, rows in spawned.items()},
    "spawned": spawned,
    "existing_release_art_removed": 0,
    "promotion_authorized": False, "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
