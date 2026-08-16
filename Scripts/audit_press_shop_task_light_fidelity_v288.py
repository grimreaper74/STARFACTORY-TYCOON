"""Read-only exact task-light fidelity comparison for retained donors and v288."""
import json
from pathlib import Path
import unreal

MAPS = {
    "pr006_donor": "/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v208",
    "pr007_donor": "/Game/LineBoss/Maps/LB_PressShop_PR007ReleaseArtCandidate_v209",
    "pr008_donor": "/Game/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210",
    "v288": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288",
}
TOKENS = ("PR006_V054_DriveTaskLight", "PR006_V054_OperatorTaskLight",
          "PR007_V055_OperatorTask", "PR007_V055_ServiceTask", "PR008_V079_LIGHT_")
PROPS = ("intensity", "attenuation_radius", "light_color", "cast_shadows", "affects_world",
         "visible", "hidden_in_game", "indirect_lighting_intensity", "volumetric_scattering_intensity",
         "intensity_units", "use_inverse_squared_falloff", "use_temperature", "temperature",
         "source_radius", "soft_source_radius", "source_width", "source_height",
         "inner_cone_angle", "outer_cone_angle")
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_task_light_fidelity_v288.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
result = {}
for key, map_path in MAPS.items():
    if not levels.load_level(map_path):
        raise RuntimeError(map_path)
    rows = []
    for actor in actors_api.get_all_level_actors():
        label = actor.get_actor_label()
        if not any(token in label for token in TOKENS):
            continue
        component = actor.get_component_by_class(unreal.LightComponentBase)
        transform = actor.get_actor_transform()
        values = {}
        for prop in PROPS:
            try:
                values[prop] = str(component.get_editor_property(prop))
            except Exception as exc:
                values[prop] = f"UNREADABLE:{exc}"
        try:
            mobility = str(component.get_mobility())
        except Exception as exc:
            mobility = f"UNREADABLE:{exc}"
        rows.append({"label": label, "class": actor.get_class().get_name(),
                     "location": str(transform.translation), "rotation": str(transform.rotation.rotator()),
                     "scale": str(transform.scale3d), "mobility": mobility, "properties": values})
    result[key] = sorted(rows, key=lambda row: row["label"])
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.SystemLibrary.quit_editor()
