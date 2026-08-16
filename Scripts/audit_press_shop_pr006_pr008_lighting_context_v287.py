"""Compare retained donor and v287 camera/light context without modifying any map."""
import json
from pathlib import Path

import unreal


MAPS = {
    "pr006_donor": "/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v208",
    "pr007_donor": "/Game/LineBoss/Maps/LB_PressShop_PR007ReleaseArtCandidate_v209",
    "pr008_donor": "/Game/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210",
    "v287": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v287",
}
CAMERAS = {
    "LB_PR006_V208_CAM_ConnectedRelease",
    "LB_PR007_V209_CAM_ConnectedRelease",
    "LB_PR008_V210_CAM_AuthoredAnchorProcess",
}
LIGHT_CLASSES = {"RectLight", "SpotLight", "PointLight", "SkyLight", "DirectionalLight"}
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_pr006_pr008_lighting_context_v287.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def vector(value):
    return [value.x, value.y, value.z]


def read(component, names):
    result = {}
    for name in names:
        try:
            result[name] = str(component.get_editor_property(name))
        except Exception as exc:
            result[name] = f"UNREADABLE:{exc}"
    return result


records = {}
for key, map_path in MAPS.items():
    if not levels.load_level(map_path):
        raise RuntimeError(map_path)
    actors = actors_api.get_all_level_actors()
    lights = []
    cameras = []
    post_process = []
    for actor in actors:
        class_name = actor.get_class().get_name()
        label = actor.get_actor_label()
        if class_name in LIGHT_CLASSES:
            component = actor.get_component_by_class(unreal.LightComponentBase)
            lights.append({
                "label": label,
                "class": class_name,
                "location_cm": vector(actor.get_actor_location()),
                "properties": read(component, ["intensity", "attenuation_radius", "light_color", "cast_shadows", "mobility"]),
            })
        if label in CAMERAS:
            component = actor.get_component_by_class(unreal.CameraComponent)
            cameras.append({
                "label": label,
                "location_cm": vector(actor.get_actor_location()),
                "rotation": str(actor.get_actor_rotation()),
                "properties": read(component, ["field_of_view", "post_process_blend_weight"]),
                "post_process_settings": str(component.get_editor_property("post_process_settings")),
            })
        if class_name == "PostProcessVolume":
            component = actor.get_component_by_class(unreal.PostProcessComponent)
            post_process.append({
                "label": label,
                "location_cm": vector(actor.get_actor_location()),
                "enabled": str(actor.get_editor_property("enabled")),
                "unbound": str(actor.get_editor_property("unbound")),
                "priority": str(actor.get_editor_property("priority")),
                "blend_weight": str(actor.get_editor_property("blend_weight")),
                "settings": str(component.get_editor_property("settings")) if component else "NO_COMPONENT",
            })
    records[key] = {
        "map": map_path,
        "light_count": len(lights),
        "lights": sorted(lights, key=lambda row: row["label"]),
        "cameras": sorted(cameras, key=lambda row: row["label"]),
        "post_process_volumes": sorted(post_process, key=lambda row: row["label"]),
    }

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(records, indent=2), encoding="utf-8")
unreal.SystemLibrary.quit_editor()
