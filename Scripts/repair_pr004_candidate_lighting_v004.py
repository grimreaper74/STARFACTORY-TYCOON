"""Repair only the PR-004 candidate validation lighting for fixed-camera review.

This deliberately does not promote assets or alter source FBX/Blender files.  It
replaces the under-powered v003 review fixtures with deterministic shadowless
industrial review lights and records the mutation for the visual gate.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import unreal


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CANDIDATE_VERSION = os.environ.get("LB_PR004_CANDIDATE_VERSION", "v004")
if CANDIDATE_VERSION not in {"v002", "v003", "v004"}:
    raise RuntimeError("LB_PR004_CANDIDATE_VERSION must be v002, v003 or v004")
MAP = f"/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_{CANDIDATE_VERSION}"
OUT = REPO / f"Saved/Audits/pr004_candidate_lighting_repair_v004_{CANDIDATE_VERSION}.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

all_actors = actors.get_all_level_actors()
removed = []
for actor in all_actors:
    label = actor.get_actor_label()
    if label.startswith("LB_PR004_ValidationCeiling_") or label.startswith("LB_PR004_ValidationSide_"):
        actors.destroy_actor(actor)
        removed.append(label)
    elif label in {
        "LB_PR004_ValidationDirectionalFill_v003",
        "LB_PR004_ValidationDirectionalFill_v004",
        "LB_PR004_FixedExposure_v003",
        "LB_PR004_FixedExposure_v004",
    }:
        actors.destroy_actor(actor)
        removed.append(label)

candidate_tag = unreal.Name(f"LB.PR004.ImportCandidate.Candidate_{CANDIDATE_VERSION}")
validation_tags = [
    candidate_tag,
    unreal.Name("LB.Asset.Candidate.NotPromoted"),
    unreal.Name("LB.Light.Validation"),
]

# Rect lights provide broad ceiling illumination.  Point lights at human height
# make the machine sides readable from management and close-control cameras.
rect_specs = (
    ("LB_PR004_ValidationCeiling_NW_v004", (-420, 420, 720), (0, 100, 80), 32000.0, (255, 239, 218)),
    ("LB_PR004_ValidationCeiling_NE_v004", (420, 420, 720), (0, 100, 80), 30000.0, (236, 245, 255)),
    ("LB_PR004_ValidationCeiling_SW_v004", (-420, -420, 720), (0, -100, 80), 28000.0, (236, 245, 255)),
    ("LB_PR004_ValidationCeiling_SE_v004", (420, -420, 720), (0, -100, 80), 28000.0, (255, 235, 212)),
)
created = []
for label, location, target, intensity, rgb in rect_specs:
    light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*location), unreal.Rotator())
    light.set_actor_label(label)
    light.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(light.get_actor_location(), unreal.Vector(*target)), False
    )
    light.get_editor_property("rect_light_component").set_editor_properties({
        "intensity": intensity,
        "attenuation_radius": 2200.0,
        "source_width": 520.0,
        "source_height": 320.0,
        "light_color": unreal.Color(*rgb, 255),
        "cast_shadows": False,
        "affect_global_illumination": False,
        "affect_reflection": True,
    })
    light.set_editor_property("tags", validation_tags)
    created.append(label)

point_specs = (
    ("LB_PR004_ValidationSide_NW_v004", (-760, 650, 360), 26000.0, (255, 232, 205)),
    ("LB_PR004_ValidationSide_NE_v004", (760, 650, 360), 24000.0, (225, 238, 255)),
    ("LB_PR004_ValidationSide_SW_v004", (-760, -650, 340), 24000.0, (225, 238, 255)),
    ("LB_PR004_ValidationSide_SE_v004", (760, -650, 340), 26000.0, (255, 232, 205)),
    ("LB_PR004_ValidationSide_Centre_v004", (0, 0, 520), 18000.0, (244, 244, 238)),
)
for label, location, intensity, rgb in point_specs:
    light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*location), unreal.Rotator())
    light.set_actor_label(label)
    light.get_editor_property("point_light_component").set_editor_properties({
        "intensity": intensity,
        "attenuation_radius": 1900.0,
        "light_color": unreal.Color(*rgb, 255),
        "cast_shadows": False,
        "affect_global_illumination": False,
        "affect_reflection": True,
    })
    light.set_editor_property("tags", validation_tags)
    created.append(label)

fill = actors.spawn_actor_from_class(
    unreal.DirectionalLight, unreal.Vector(0, 0, 800), unreal.Rotator(-58.0, 128.0, 0.0)
)
fill.set_actor_label("LB_PR004_ValidationDirectionalFill_v004")
fill.get_editor_property("directional_light_component").set_editor_properties({
    "intensity": 2.5,
    "light_color": unreal.Color(205, 220, 240, 255),
    "cast_shadows": False,
    "affect_global_illumination": False,
})
fill.set_editor_property("tags", validation_tags)
created.append(fill.get_actor_label())

exposure = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
exposure.set_actor_label("LB_PR004_FixedExposure_v004")
exposure.set_editor_properties({"unbound": True, "blend_weight": 1.0, "tags": validation_tags})
settings = exposure.get_editor_property("settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_MANUAL,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": 1.25,
    "override_color_saturation": True,
    "color_saturation": unreal.Vector4(1.0, 1.0, 1.0, 1.0),
})
exposure.set_editor_property("settings", settings)
created.append(exposure.get_actor_label())

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving PR-004 validation lighting v004")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "line-boss/audit/pr004-candidate-lighting-repair/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CANDIDATE_LIGHTING_REPAIRED__FRESH_VISUAL_GATE_REQUIRED",
    "map": MAP,
    "promotion_supported": False,
    "removed_validation_lights": sorted(removed),
    "created_validation_lights": created,
    "notes": [
        "No source mesh, source material, vendor pack asset or gameplay map was modified.",
        "This is validation-map lighting only and cannot satisfy the release visual gate by itself.",
    ],
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_LIGHTING_REPAIR_V004={OUT}")
