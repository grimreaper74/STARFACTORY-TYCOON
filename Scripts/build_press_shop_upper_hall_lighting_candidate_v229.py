"""Extend the retained ambient luminaire grid over all four press trains in a fresh v229 child."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v228"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v229"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_upper_hall_lighting_build_v229.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
parent_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v228.umap"
parent_hash_before = sha256(parent_file)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

actors = actors_api.get_all_level_actors()
fixture_donor = next((actor for actor in actors if actor.get_actor_label() == "LB_ENV_V138_Luminaire_01"), None)
failures = []
if not isinstance(fixture_donor, unreal.StaticMeshActor):
    failures.append("retained ambient luminaire donor missing")
    donor_mesh = None
    donor_material = None
else:
    donor_component = fixture_donor.get_component_by_class(unreal.StaticMeshComponent)
    donor_mesh = donor_component.static_mesh
    donor_material = donor_component.get_material(0)

added_fixtures = []
added_lights = []
train_rows = {"A": -4300.0, "B": -2600.0, "C": -900.0, "D": 800.0}
for train_id, y_value in train_rows.items():
    for bay_index, x_value in enumerate((3800.0, 5400.0, 7000.0), 1):
        fixture_label = f"LB_WHOLE_V229_LUMINAIRE_TRAIN_{train_id}_{bay_index:02d}"
        if donor_mesh is not None:
            fixture = actors_api.spawn_actor_from_class(
                unreal.StaticMeshActor, unreal.Vector(x_value, y_value, 1760.0), unreal.Rotator())
            fixture.set_actor_label(fixture_label)
            fixture.set_actor_scale3d(fixture_donor.get_actor_scale3d())
            component = fixture.get_component_by_class(unreal.StaticMeshComponent)
            component.set_static_mesh(donor_mesh)
            if donor_material is not None:
                component.set_material(0, donor_material)
            component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            component.set_editor_property("cast_shadow", False)
            fixture.tags = [
                unreal.Name("LB.Environment.Luminaire"), unreal.Name("LB.Lighting.IndustrialLED.Ambient"),
                unreal.Name("LB.Integration.UpperHall.v229"), unreal.Name("LB.Asset.CandidateNotPromoted")]
            added_fixtures.append(fixture_label)

        light = actors_api.spawn_actor_from_class(
            unreal.RectLight, unreal.Vector(x_value, y_value, 1725.0), unreal.Rotator(-90.0, 0.0, 0.0))
        if light is None:
            failures.append(f"could not spawn Train {train_id} ambient bay {bay_index}")
            continue
        light_label = f"LB_WHOLE_V229_AMBIENT_TRAIN_{train_id}_{bay_index:02d}"
        light.set_actor_label(light_label)
        light.rect_light_component.set_editor_properties({
            "intensity": 13.0,
            "attenuation_radius": 2250.0,
            "source_width": 1250.0,
            "source_height": 130.0,
            "light_color": unreal.Color(218, 228, 232, 255),
            "cast_shadows": False,
        })
        light.tags = [
            unreal.Name("LB.Lighting.IndustrialLED.Ambient"),
            unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority"),
            unreal.Name("LB.Integration.UpperHall.v229"), unreal.Name("LB.Asset.CandidateNotPromoted")]
        added_lights.append(light_label)

tuned_spots = []
for actor in actors_api.get_all_level_actors():
    if isinstance(actor, unreal.SpotLight) and actor.get_actor_label().startswith("LB_WHOLE_V227_LIGHT_TRAIN_"):
        actor.spot_light_component.set_editor_properties({
            "intensity": 2350.0, "inner_cone_angle": 42.0, "outer_cone_angle": 72.0})
        tuned_spots.append(actor.get_actor_label())

sky = next((actor for actor in actors_api.get_all_level_actors()
            if actor.get_actor_label() == "LB_PRESS_V023_FrontEndSkyLight"), None)
if isinstance(sky, unreal.SkyLight):
    component = sky.get_component_by_class(unreal.SkyLightComponent)
    component.set_editor_properties({"intensity": 0.72, "cast_shadows": False})
else:
    failures.append("retained skylight missing")

exposure = next((actor for actor in actors_api.get_all_level_actors()
                 if actor.get_actor_label() == "LB_INT_FRONT_FrontEndFixedExposure"), None)
if isinstance(exposure, unreal.PostProcessVolume):
    settings = exposure.get_editor_property("settings")
    settings.set_editor_properties({"override_auto_exposure_bias": True, "auto_exposure_bias": 0.75})
    exposure.set_editor_property("settings", settings)
else:
    failures.append("retained fixed exposure volume missing")

levels.save_current_level()
parent_hash_after = sha256(parent_file)
if parent_hash_after != parent_hash_before:
    failures.append("protected v228 parent changed")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v229.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-upper-hall-lighting-build-v229/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__AMBIENT_GRID_EXTENDED_OVER_ALL_FOUR_PRESS_TRAINS__VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(map_file) if map_file.exists() else None,
    "added_luminaires": added_fixtures,
    "added_rect_lights": added_lights,
    "tuned_inherited_spots": sorted(tuned_spots),
    "skylight_intensity": 0.72,
    "fixed_exposure_bias": 0.75,
    "authority_or_machine_changes": 0,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log(f"LB_V229_UPPER_HALL_BUILD::{json.dumps(payload)}")
unreal.SystemLibrary.quit_editor()
