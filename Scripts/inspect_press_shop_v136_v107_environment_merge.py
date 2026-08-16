"""Read-only comparison of the retained v107 hall treatment and v136 front end."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAPS = {
    "v136": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v136",
    "v107": "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107",
}
OUT = ROOT / "Saved/Audits/PressShopIntegration/v136_v107_environment_merge_inputs.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary


def component_value(actor, component_class, property_name, default=None):
    component = actor.get_component_by_class(component_class)
    return component.get_editor_property(property_name) if component else default


def inspect_map(name, path):
    if not levels.load_level(path):
        raise RuntimeError(f"could not load {path}")
    actors = actors_api.get_all_level_actors()
    lights = []
    environment = []
    key_floors = []
    for actor in actors:
        label = actor.get_actor_label()
        tags = [str(value) for value in actor.tags]
        if isinstance(actor, unreal.DirectionalLight):
            component_class = unreal.DirectionalLightComponent
        elif isinstance(actor, unreal.SkyLight):
            component_class = unreal.SkyLightComponent
        elif isinstance(actor, unreal.RectLight):
            component_class = unreal.RectLightComponent
        elif isinstance(actor, unreal.PointLight):
            component_class = unreal.PointLightComponent
        elif isinstance(actor, unreal.SpotLight):
            component_class = unreal.SpotLightComponent
        else:
            component_class = None
        if component_class is not None:
            record = {
                "label": label,
                "class": actor.get_class().get_name(),
                "tags": tags,
                "affects_world": bool(component_value(actor, component_class, "affects_world", True)),
            }
            if component_class != unreal.SkyLightComponent:
                record["intensity"] = float(component_value(actor, component_class, "intensity", 0.0))
            else:
                record["real_time_capture"] = bool(component_value(actor, component_class, "real_time_capture", False))
            lights.append(record)
        if any(tag.startswith("LB.Environment.") for tag in tags) or label.startswith("LB_ENV_V107_"):
            environment.append({"label": label, "class": actor.get_class().get_name(), "tags": tags})
        if isinstance(actor, unreal.StaticMeshActor) and (
            label.startswith("LB_INT_FRONT_Floor_") or label in {
                "LB_INT_FRONT_PedestrianRoute", "LB_ZONE_PRESS_COIL_STORE",
                "LB_ZONE_PRESS_FRONT_END", "LB_ZONE_PRESS_LOGISTICS",
                "LB_ZONE_PRESS_RECEIVING", "LB_ZONE_PRESS_SUPPORT",
                "LB_ZONE_PRESS_TOOLING", "LB_ZONE_PRESS_TRAINS",
            }
        ):
            component = actor.static_mesh_component
            key_floors.append({
                "label": label,
                "materials": [
                    component.get_material(index).get_path_name() if component.get_material(index) else None
                    for index in range(component.get_num_materials())
                ],
                "tags": tags,
            })
    return {
        "map": path,
        "actor_count": len(actors),
        "light_count": len(lights),
        "active_light_count": sum(1 for item in lights if item["affects_world"]),
        "lights": lights,
        "environment_actor_count": len(environment),
        "environment_actors": environment,
        "key_floors": key_floors,
    }


report = {
    "$schema": "cairnwell/audit/press-shop-v136-v107-environment-merge-inputs/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "maps": {name: inspect_map(name, path) for name, path in MAPS.items()},
    "required_v107_materials": {
        path: library.does_asset_exist(path) for path in (
            "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v107/Materials/M_CA_MW_SlabJoint_v105",
            "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v107/Materials/M_CA_MW_LogisticsRoute_v105",
            "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v107/Materials/M_CA_MW_RouteYellow_v105",
            "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v107/Materials/M_CA_MW_LuminaireLens_v105",
        )
    },
    "maps_changed": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({
    "v136_actor_count": report["maps"]["v136"]["actor_count"],
    "v136_light_count": report["maps"]["v136"]["light_count"],
    "v136_environment_actor_count": report["maps"]["v136"]["environment_actor_count"],
    "v107_actor_count": report["maps"]["v107"]["actor_count"],
    "v107_light_count": report["maps"]["v107"]["light_count"],
    "v107_environment_actor_count": report["maps"]["v107"]["environment_actor_count"],
    "required_v107_materials": report["required_v107_materials"],
}, indent=2))
