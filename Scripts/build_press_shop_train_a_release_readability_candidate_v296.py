"""Build a visual-only v295 child with balanced Train A release-readability lighting."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAReleaseReadabilityCandidate_v296"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAReleaseReadabilityCandidate_v296.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_a_release_readability_build_v296.json"

CAMERAS = [
    ("LB_V296_CAM_TrainAOperator", (5000, -5700, 650), (4000, -4742, 500), 47),
    ("LB_V296_CAM_TrainAFabrication", (3500, -5600, 600), (4100, -4742, 500), 44),
    ("LB_V296_CAM_TrainAOverview", (7200, -6200, 1300), (3850, -4742, 520), 48),
]
FILLS = [
    ("LB_V296_LIGHT_TrainAOperatorFill_01", (2600, -5480, 820), (2750, -4742, 520)),
    ("LB_V296_LIGHT_TrainAOperatorFill_02", (4000, -5480, 820), (4100, -4742, 520)),
    ("LB_V296_LIGHT_TrainAOperatorFill_03", (5400, -5480, 820), (5350, -4742, 520)),
]

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite preserved v296")
base_hash = sha(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh v295 child failed")

removed = []
for actor in list(api.get_all_level_actors()):
    if actor.get_actor_label().startswith(("LB_V295_CAM_TrainA", "LB_V295_LIGHT_TrainA_TaskFill_")):
        removed.append(actor.get_actor_label())
        api.destroy_actor(actor)

recalibrated = []
for actor in api.get_all_level_actors():
    if actor.get_actor_label().startswith("LB_WHOLE_V227_LIGHT_TRAIN_A"):
        component = actor.get_component_by_class(unreal.LightComponent)
        if component is not None:
            before = float(component.get_editor_property("intensity"))
            component.set_editor_property("intensity", 950.0)
            recalibrated.append({"label": actor.get_actor_label(), "before": before, "after": 950.0})

lights = []
for label, location, target in FILLS:
    light = api.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*location), unreal.Rotator())
    if light is None:
        raise RuntimeError(f"could not spawn {label}")
    light.set_actor_label(label)
    light.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(light.get_actor_location(), unreal.Vector(*target)), False
    )
    component = light.get_component_by_class(unreal.RectLightComponent)
    component.set_mobility(unreal.ComponentMobility.MOVABLE)
    component.set_editor_properties({
        "intensity": 115.0,
        "attenuation_radius": 1250.0,
        "source_width": 720.0,
        "source_height": 360.0,
        "light_color": unreal.Color(205, 218, 226, 255),
        "cast_shadows": False,
    })
    light.tags = [
        unreal.Name("LB.Lighting.IndustrialLED.TrainAOperatorFill"),
        unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority"),
        unreal.Name("LB.Asset.Candidate.v296"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    lights.append(label)

cameras = []
for label, location, target, fov in CAMERAS:
    camera = api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    if camera is None:
        raise RuntimeError(f"could not spawn {label}")
    camera.set_actor_label(label)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False
    )
    component = camera.camera_component
    component.set_editor_properties({
        "field_of_view": float(fov),
        "aspect_ratio": 16 / 9,
        "constrain_aspect_ratio": True,
        "post_process_blend_weight": 1.0,
    })
    settings = component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": -0.55,
    })
    component.set_editor_property("post_process_settings", settings)
    camera.tags = [
        unreal.Name("LB.Camera.Validation"),
        unreal.Name("LB.Camera.Fixed.TrainAReleaseReadability.v296"),
        unreal.Name("LB.Asset.Candidate.v296"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    cameras.append(label)

shell = next((a for a in api.get_all_level_actors() if a.get_actor_label() == "LB_V295_PTA_FABRICATED_SHELL_V015"), None)
failures = []
if shell is None:
    failures.append("v295 shell missing")
elif str(shell.static_mesh_component.get_collision_profile_name()) != "NoCollision" or shell.static_mesh_component.get_editor_property("can_ever_affect_navigation"):
    failures.append("shell collision/navigation changed")
if len(recalibrated) != 2:
    failures.append(f"expected two inherited Train A spotlights, found {len(recalibrated)}")
if len(lights) != 3 or len(cameras) != 3:
    failures.append(f"visual actor count invalid lights={len(lights)} cameras={len(cameras)}")
if not levels.save_current_level():
    failures.append("save failed")
if sha(BASE_FILE) != base_hash:
    failures.append("protected v295 changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-train-a-release-readability-build-v296/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__VISUAL_ONLY_BALANCED_TRAIN_A_CHILD__FRESH_CAPTURE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V296_NOT_A_PARENT",
    "base": BASE,
    "map": MAP,
    "base_sha256": base_hash,
    "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None,
    "removed_v295_diagnostic_actors": removed,
    "recalibrated_inherited_spotlights": recalibrated,
    "added_rect_fills": lights,
    "added_fixed_cameras": cameras,
    "camera_exposure_bias": -0.55,
    "unchanged_contracts": ["machine geometry", "machine transforms", "collision", "navigation", "runtime authority", "motion bindings", "save authority"],
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
