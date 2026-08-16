"""Read-only comparison of retained v180 and cumulative v230 coil readability inputs."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAPS = {
    "v180": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v180",
    "v230": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v230",
}
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_coil_readability_delta_v230.json"
LIGHT_LABELS = {
    "LB_ENV_V140_CoilTaskRect_01", "LB_ENV_V140_CoilTaskRect_02",
    "LB_ENV_V141_CoilNorthTaskRect_01", "LB_ENV_V141_CoilNorthTaskRect_02",
}

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows = {}
for key, map_path in MAPS.items():
    if not levels.load_level(map_path):
        raise RuntimeError(map_path)
    map_row = {"lights": [], "post_process": [], "sky_lights": []}
    for actor in actors_api.get_all_level_actors():
        label = actor.get_actor_label()
        if label in LIGHT_LABELS:
            component = actor.get_component_by_class(unreal.RectLightComponent)
            rotation = actor.get_actor_rotation()
            map_row["lights"].append({
                "label": label,
                "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
                "rotation_deg": [rotation.pitch, rotation.yaw, rotation.roll],
                "hidden_editor": actor.is_hidden_ed(),
                "hidden_game": actor.get_editor_property("hidden"),
                "visible": component.get_editor_property("visible"),
                "intensity": component.get_editor_property("intensity"),
                "attenuation_radius": component.get_editor_property("attenuation_radius"),
            })
        if label == "LB_INT_FRONT_FrontEndFixedExposure":
            settings = actor.get_editor_property("settings")
            map_row["post_process"].append({
                "label": label,
                "enabled": actor.get_editor_property("enabled"),
                "unbound": actor.get_editor_property("unbound"),
                "priority": actor.get_editor_property("priority"),
                "auto_exposure_bias": settings.get_editor_property("auto_exposure_bias"),
                "override_auto_exposure_bias": settings.get_editor_property("override_auto_exposure_bias"),
            })
        if label == "LB_PRESS_V023_FrontEndSkyLight":
            component = actor.get_component_by_class(unreal.SkyLightComponent)
            map_row["sky_lights"].append({
                "label": label,
                "intensity": component.get_editor_property("intensity"),
                "visible": component.get_editor_property("visible"),
                "cast_shadows": component.get_editor_property("cast_shadows"),
            })
    rows[key] = map_row

material = unreal.EditorAssetLibrary.load_asset(
    "/Game/LineBoss/Candidates/PressShop/PR004WrapResponse_v118/Materials/MI_CA_MW_PaleSilverPolyWrap_v118")
material_parameters = {}
if material:
    for name in ("TextureInfluence", "TextureScale", "BaseRoughness", "RoughTextureInfluence", "Metallic", "NormalStrength"):
        material_parameters[name] = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(material, name)
    tint = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(material, "SurfaceTint")
    material_parameters["SurfaceTint"] = [tint.r, tint.g, tint.b, tint.a]

payload = {
    "$schema": "cairnwell/audit/press-shop-coil-readability-delta-v230/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY__NO_ASSETS_CHANGED",
    "maps": rows,
    "pale_silver_material_parameters": material_parameters,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
