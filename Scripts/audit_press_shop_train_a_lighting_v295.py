"""Read-only exact-v295 lighting, exposure and camera audit."""

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_a_lighting_exposure_audit_v295.json"
EXPECTED_SHA = "5CF8715BEE1F55EF98E1B9B713C74BF4F9C87281FE209FA190D73DA61DE94ABF"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def value(obj, name):
    try:
        result = obj.get_editor_property(name)
        if hasattr(result, "to_tuple"):
            return list(result.to_tuple())
        if isinstance(result, unreal.Color):
            return [result.r, result.g, result.b, result.a]
        if isinstance(result, unreal.LinearColor):
            return [result.r, result.g, result.b, result.a]
        if isinstance(result, unreal.Vector):
            return [result.x, result.y, result.z]
        if isinstance(result, unreal.Rotator):
            return [result.pitch, result.yaw, result.roll]
        if isinstance(result, (str, int, float, bool)) or result is None:
            return result
        return str(result)
    except Exception:
        return None


before = sha256(MAP_FILE)
if before != EXPECTED_SHA:
    raise RuntimeError(f"v295 hash drift {before}")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

lights = []
volumes = []
cameras = []
classes = Counter()
for actor in api.get_all_level_actors():
    class_name = actor.get_class().get_name()
    classes[class_name] += 1
    location = actor.get_actor_location()
    common = {
        "label": actor.get_actor_label(),
        "class": class_name,
        "location_cm": [location.x, location.y, location.z],
        "tags": [str(tag) for tag in actor.tags],
    }
    component = None
    for component_class in (unreal.PointLightComponent, unreal.SpotLightComponent, unreal.RectLightComponent, unreal.DirectionalLightComponent, unreal.SkyLightComponent):
        component = actor.get_component_by_class(component_class)
        if component is not None:
            break
    if component is not None:
        common.update({
            "component_class": component.get_class().get_name(),
            "intensity": value(component, "intensity"),
            "intensity_units": value(component, "intensity_units"),
            "attenuation_radius_cm": value(component, "attenuation_radius"),
            "source_radius_cm": value(component, "source_radius"),
            "source_length_cm": value(component, "source_length"),
            "inner_cone_angle": value(component, "inner_cone_angle"),
            "outer_cone_angle": value(component, "outer_cone_angle"),
            "temperature": value(component, "temperature"),
            "use_temperature": value(component, "use_temperature"),
            "light_color": value(component, "light_color"),
            "cast_shadows": value(component, "cast_shadows"),
            "indirect_lighting_intensity": value(component, "indirect_lighting_intensity"),
            "volumetric_scattering_intensity": value(component, "volumetric_scattering_intensity"),
        })
        lights.append(common)
    if isinstance(actor, unreal.PostProcessVolume):
        settings = actor.get_editor_property("settings")
        common.update({
            "unbound": value(actor, "unbound"),
            "blend_radius": value(actor, "blend_radius"),
            "blend_weight": value(actor, "blend_weight"),
            "priority": value(actor, "priority"),
            "exposure": {name: value(settings, name) for name in (
                "auto_exposure_method", "auto_exposure_bias", "auto_exposure_min_brightness",
                "auto_exposure_max_brightness", "auto_exposure_min_ev100", "auto_exposure_max_ev100",
                "auto_exposure_speed_up", "auto_exposure_speed_down", "auto_exposure_low_percent",
                "auto_exposure_high_percent", "local_exposure_highlight_contrast_scale",
                "local_exposure_shadow_contrast_scale", "color_saturation", "color_contrast",
                "film_slope", "film_toe", "film_shoulder", "film_black_clip", "film_white_clip",
            )},
        })
        volumes.append(common)
    if isinstance(actor, unreal.CameraActor):
        camera = actor.camera_component
        settings = value(camera, "post_process_settings")
        common.update({
            "field_of_view": value(camera, "field_of_view"),
            "post_process_blend_weight": value(camera, "post_process_blend_weight"),
            "has_post_process_settings": settings is not None,
        })
        cameras.append(common)

after = sha256(MAP_FILE)
failures = []
if after != before:
    failures.append("read-only audit changed v295")
if not lights:
    failures.append("no light actors found")
payload = {
    "$schema": "cairnwell/audit/press-shop-train-a-lighting-exposure-v295/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__READ_ONLY_EXACT_V295_LIGHTING_EXPOSURE_INVENTORY" if not failures else "FAIL__AUDIT_INVALID",
    "map": MAP,
    "map_sha256_before": before,
    "map_sha256_after": after,
    "actor_class_counts": dict(classes),
    "light_count": len(lights),
    "post_process_volume_count": len(volumes),
    "camera_count": len(cameras),
    "lights": lights,
    "post_process_volumes": volumes,
    "cameras": cameras,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({key: payload[key] for key in ("status", "light_count", "post_process_volume_count", "camera_count", "failures")}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
