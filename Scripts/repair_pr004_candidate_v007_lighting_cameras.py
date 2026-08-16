"""Repair Candidate_v007 review lighting and fixed-camera composition only.

This script deliberately edits the isolated validation map.  It does not touch
the permanent Press Shop or promote any PR-004 asset.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v007"
AUDIT = REPO / "Saved/Audits/pr004_candidate_v007_lighting_camera_repair.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load isolated candidate map {MAP}")

by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}

# v007 exposed a legacy slot-routing bug: LB_PR004_FW6_VCIFilm fell through to
# MachineDark.  Override the isolated candidate now and keep the base importer
# fixed for all subsequent rebuilds.
film_material = unreal.EditorAssetLibrary.load_asset(
    "/Game/LineBoss/Stations/Press/PR004/Candidate_v007/Materials/MI_LB_PR004_RemovedFilm"
)
if film_material is None:
    raise RuntimeError("Missing Candidate_v007 RemovedFilm material instance")
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    film_material, "BaseColor", unreal.LinearColor(0.18, 0.205, 0.225, 1.0)
)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(film_material, "Metallic", 0.02)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(film_material, "Roughness", 0.78)
unreal.MaterialEditingLibrary.update_material_instance(film_material)
unreal.EditorAssetLibrary.save_loaded_asset(film_material, only_if_is_dirty=False)
for actor in by_label.values():
    if isinstance(actor, unreal.StaticMeshActor) and actor.get_actor_label().endswith(("_film_web", "_wound_film")):
        actor.get_editor_property("static_mesh_component").set_material(0, film_material)


def look_at(actor, location, target):
    actor.set_actor_location(unreal.Vector(*location), False, False)
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*location), unreal.Vector(*target)),
        False,
    )


# Broad, neutral review light.  The old concentrated rig clipped stainless and
# yellow paint while swallowing the black machinery.  These are validation
# values, not approved factory lighting.
key = by_label["LB_PR004_ValidationKey"]
look_at(key, (-360.0, 60.0, 760.0), (-40.0, 20.0, 100.0))
key.get_editor_property("rect_light_component").set_editor_properties({
    "intensity": 135.0,
    "attenuation_radius": 2200.0,
    "source_width": 900.0,
    "source_height": 520.0,
    "light_color": unreal.Color(236, 240, 246, 255),
})

fill = by_label["LB_PR004_ValidationFill"]
look_at(fill, (500.0, -520.0, 620.0), (80.0, 70.0, 100.0))
fill.get_editor_property("rect_light_component").set_editor_properties({
    "intensity": 85.0,
    "attenuation_radius": 2100.0,
    "source_width": 760.0,
    "source_height": 440.0,
    "light_color": unreal.Color(220, 230, 242, 255),
})

ambient = by_label["LB_PR004_ValidationAmbient"]
ambient.set_actor_rotation(unreal.Rotator(-62.0, 145.0, 0.0), False)
ambient.get_editor_property("directional_light_component").set_editor_properties({
    "intensity": 0.20,
    "light_color": unreal.Color(205, 218, 232, 255),
    "cast_shadows": False,
})

# Low-energy cross-lighting prevents dark painted frames from collapsing into
# a single silhouette when viewed from either fixed oblique direction.
for label, location in (
    ("LB_PR004_ValidationCross_N", (0.0, 900.0, 420.0)),
    ("LB_PR004_ValidationCross_S", (0.0, -900.0, 420.0)),
    ("LB_PR004_ValidationCross_E", (780.0, 0.0, 390.0)),
    ("LB_PR004_ValidationCross_W", (-780.0, 0.0, 390.0)),
):
    cross = by_label.get(label)
    if cross is None:
        cross = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*location), unreal.Rotator())
        cross.set_actor_label(label)
    look_at(cross, location, (0.0, 0.0, 100.0))
    cross.get_editor_property("rect_light_component").set_editor_properties({
        "intensity": 70.0,
        "attenuation_radius": 1800.0,
        "source_width": 600.0,
        "source_height": 360.0,
        "light_color": unreal.Color(218, 226, 236, 255),
        "cast_shadows": False,
    })
    cross.set_editor_property("tags", [
        unreal.Name("LB.Candidate.PR004.v007"),
        unreal.Name("LB.Asset.Candidate.NotPromoted"),
        unreal.Name("LB.Light.Validation"),
    ])

post = by_label["LB_PR004_FixedExposure"]
settings = post.get_editor_property("settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0,
    "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": 0.65,
})
post.set_editor_property("settings", settings)

# Fixed validation views.  Overview cameras include the full locked envelope;
# detail cameras show mechanisms without cutting off their process context.
camera_specs = {
    "LB_PR004_CAM_Overview_SW": ((-1320, 1340, 880), (0, 0, 105), 52.0),
    "LB_PR004_CAM_Overview_NE": ((1250, -1380, 820), (0, 0, 110), 52.0),
    "LB_PR004_CAM_CradleClose": ((-850, 760, 390), (-280, 120, 125), 47.0),
    "LB_PR004_CAM_RobotTools": ((790, 610, 440), (120, -80, 120), 48.0),
    "LB_PR004_CAM_PackagingClose": ((-820, -480, 380), (-280, 120, 130), 46.0),
    "LB_PR004_CAM_FilmDewrap": ((1120, 1040, 610), (260, 245, 110), 49.0),
}

camera_records = []
for label, (location, target, fov) in camera_specs.items():
    camera = by_label[label]
    look_at(camera, location, target)
    camera.get_editor_property("camera_component").set_editor_property("field_of_view", fov)
    camera_records.append({"camera": label, "location_cm": location, "target_cm": target, "fov": fov})

top = by_label["LB_PR004_CAM_Top"]
top.set_actor_location(unreal.Vector(0.0, 0.0, 1900.0), False, False)
top.set_actor_rotation(unreal.Rotator(0.0, -90.0, -90.0), False)
top_component = top.get_editor_property("camera_component")
top_component.set_editor_properties({
    "projection_mode": unreal.CameraProjectionMode.ORTHOGRAPHIC,
    "ortho_width": 2600.0,
    "aspect_ratio": 16.0 / 9.0,
    "constrain_aspect_ratio": True,
})
camera_records.append({"camera": "LB_PR004_CAM_Top", "ortho_width_cm": 2600.0})

if not levels.save_current_level():
    raise RuntimeError("Failed to save Candidate_v007 validation-map repair")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/pr004-candidate-v007-review-rig/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "VALIDATION_RIG_REPAIRED__FRESH_SCREENSHOTS_REQUIRED__CANDIDATE_NOT_PROMOTED",
    "map": MAP,
    "scope": "isolated candidate validation lighting and fixed cameras only",
    "permanent_press_shop_modified": False,
    "promotion_supported": False,
    "lighting": {
        "key_intensity": 135.0,
        "fill_intensity": 85.0,
        "ambient_intensity": 0.20,
        "fixed_exposure_bias": 0.65,
        "cross_fill_count": 4,
    },
    "cameras": camera_records,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_PR004_V007_REVIEW_RIG_REPAIR_PASS")
unreal.SystemLibrary.quit_editor()
