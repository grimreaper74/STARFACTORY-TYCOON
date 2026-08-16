"""Restore retained PR006-PR008 donor task lighting on direct-child v288."""
import hashlib
import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288"
DONORS = {
    "PR006": "/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v208",
    "PR007": "/Game/LineBoss/Maps/LB_PressShop_PR007ReleaseArtCandidate_v209",
    "PR008": "/Game/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210",
}
PREFIXES = {
    "PR006": ("LB_PR006_V054_DriveTaskLight", "LB_PR006_V054_OperatorTaskLight"),
    "PR007": ("LB_PR007_V055_OperatorTask", "LB_PR007_V055_ServiceTask"),
    "PR008": ("LB_PR008_V079_LIGHT_",),
}
AUTHORITATIVE = {
    "LB_PR006_V054_DriveTaskLight": {"intensity": 850.0, "attenuation_radius": 1750.0,
        "light_color": unreal.Color(202, 225, 244, 255), "source_radius": 65.0,
        "soft_source_radius": 120.0, "inner_cone_angle": 30.0, "outer_cone_angle": 58.0},
    "LB_PR006_V054_OperatorTaskLight": {"intensity": 1050.0, "attenuation_radius": 1750.0,
        "light_color": unreal.Color(244, 233, 224, 255), "source_radius": 65.0,
        "soft_source_radius": 120.0, "inner_cone_angle": 30.0, "outer_cone_angle": 58.0},
    "LB_PR007_V055_OperatorTask": {"intensity": 1000.0, "attenuation_radius": 1750.0,
        "light_color": unreal.Color(244, 233, 224, 255), "source_radius": 65.0,
        "soft_source_radius": 120.0, "inner_cone_angle": 30.0, "outer_cone_angle": 58.0},
    "LB_PR007_V055_ServiceTask": {"intensity": 800.0, "attenuation_radius": 1750.0,
        "light_color": unreal.Color(202, 225, 244, 255), "source_radius": 65.0,
        "soft_source_radius": 120.0, "inner_cone_angle": 30.0, "outer_cone_angle": 58.0},
    "LB_PR008_V079_LIGHT_Overhead_West": {"light_color": unreal.Color(246, 238, 224, 255)},
    "LB_PR008_V079_LIGHT_Overhead_Centre": {"light_color": unreal.Color(246, 238, 224, 255)},
    "LB_PR008_V079_LIGHT_Overhead_East": {"light_color": unreal.Color(246, 238, 224, 255)},
    "LB_PR008_V079_LIGHT_OperatorFill": {"light_color": unreal.Color(241, 232, 218, 255)},
    "LB_PR008_V079_LIGHT_DischargeFill": {"light_color": unreal.Color(207, 226, 242, 255)},
}
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr006_pr008_retained_lighting_build_v288.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273.umap"
TARGET_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288.umap"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


protected_before = sha256(BASE_FILE)
rows = []
for family, donor in DONORS.items():
    if not levels.load_level(donor):
        raise RuntimeError(donor)
    for actor in actors_api.get_all_level_actors():
        label = actor.get_actor_label()
        if not any(label.startswith(prefix) for prefix in PREFIXES[family]):
            continue
        class_name = actor.get_class().get_name()
        if class_name not in {"RectLight", "SpotLight", "PointLight"}:
            continue
        component = actor.get_component_by_class(unreal.LightComponentBase)
        transform = actor.get_actor_transform()
        properties = {}
        names = ["intensity", "attenuation_radius", "light_color", "cast_shadows"]
        if class_name == "RectLight":
            names += ["source_width", "source_height", "barn_door_angle", "barn_door_length"]
        elif class_name == "SpotLight":
            names += ["inner_cone_angle", "outer_cone_angle", "source_radius", "soft_source_radius"]
        for name in names:
            try:
                properties[name] = component.get_editor_property(name)
            except Exception:
                pass
        rows.append({
            "family": family,
            "label": label,
            "class": class_name,
            "actor_class": actor.get_class(),
            "location": transform.translation,
            "rotation": transform.rotation.rotator(),
            "scale": transform.scale3d,
            "properties": properties,
        })

if not levels.load_level(MAP):
    raise RuntimeError(MAP)
target_by_label = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
changed = []
spawned = []
for row in rows:
    actor = target_by_label.get(row["label"])
    if actor is None:
        actor = actors_api.spawn_actor_from_class(row["actor_class"], row["location"], row["rotation"])
        if actor is None:
            raise RuntimeError(f"could not spawn {row['label']}")
        actor.set_actor_label(row["label"])
        actor.set_actor_scale3d(row["scale"])
        actor.tags = [unreal.Name(f"LB.Station.{row['family']}"), unreal.Name("LB.Lighting.Task"),
                      unreal.Name("LB.Integration.RetainedLighting.v288"), unreal.Name("LB.Asset.CandidateNotPromoted")]
        spawned.append(row["label"])
    component = actor.get_component_by_class(unreal.LightComponentBase)
    row["properties"].update(AUTHORITATIVE.get(row["label"], {}))
    for name, value in row["properties"].items():
        component.set_editor_property(name, value)
    actor.root_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    changed.append({"label": row["label"], "intensity": str(row["properties"].get("intensity"))})

if not levels.save_current_level():
    raise RuntimeError("could not save v288 lighting calibration")
protected_after = sha256(BASE_FILE)
if protected_before != protected_after:
    raise RuntimeError("protected v273 changed")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "line-boss/audit/press-shop-pr006-pr008-retained-lighting-build-v288/v1",
    "status": "PASS__RETAINED_DONOR_TASK_LIGHTING_RESTORED__VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED",
    "base": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273",
    "map": MAP,
    "protected_v273_sha256_before": protected_before,
    "protected_v273_sha256_after": protected_after,
    "target_v288_sha256": sha256(TARGET_FILE),
    "changed": changed,
    "spawned": spawned,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.SystemLibrary.quit_editor()
