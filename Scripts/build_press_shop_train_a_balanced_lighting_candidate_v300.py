"""Measured direct-v295 Train A lighting/exposure successor.

Values are derived from the exact v295 audit. This changes presentation only:
one post-process volume, eight inherited Train A lights, the fixed v016 shell,
and three validation cameras. Runtime/collision/navigation remain untouched.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300"
SHELL_ASSET = "/Game/LineBoss/Candidates/PressTrains/TrainA/FabricatedShell_v041/SM_CA_MW_PTA_PresentationShell_v016"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_a_balanced_lighting_build_v300.json"
EXPECTED_BASE_SHA = "5CF8715BEE1F55EF98E1B9B713C74BF4F9C87281FE209FA190D73DA61DE94ABF"

LIGHT_TARGETS = {
    "LB_WHOLE_V227_LIGHT_TRAIN_A_WEST": 1200.0,
    "LB_WHOLE_V227_LIGHT_TRAIN_A_EAST": 1200.0,
    "LB_V295_LIGHT_TrainA_TaskFill_01": 245.0,
    "LB_V295_LIGHT_TrainA_TaskFill_02": 245.0,
    "LB_V295_LIGHT_TrainA_TaskFill_03": 245.0,
    "LB_WHOLE_V229_AMBIENT_TRAIN_A_01": 24.0,
    "LB_WHOLE_V229_AMBIENT_TRAIN_A_02": 24.0,
    "LB_WHOLE_V229_AMBIENT_TRAIN_A_03": 24.0,
}

CAMERAS = [
    ("LB_V300_CAM_TrainAOperatorInsideGrid", (5750.0, -5260.0, 480.0), (4350.0, -4700.0, 430.0), 56.0),
    ("LB_V300_CAM_TrainAFabricationInsideGrid", (5750.0, -4880.0, 610.0), (4230.0, -4700.0, 515.0), 60.0),
    ("LB_V300_CAM_TrainAHighInsideGrid", (5790.0, -5350.0, 1320.0), (4300.0, -4550.0, 480.0), 64.0),
]

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if library.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite preserved v300")
if sha256(BASE_FILE) != EXPECTED_BASE_SHA:
    raise RuntimeError("protected v295 hash drift")
mesh = library.load_asset(SHELL_ASSET)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(SHELL_ASSET)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh direct-v295 child failed")

actors = api.get_all_level_actors()
by_label = {actor.get_actor_label(): actor for actor in actors}
shell = by_label.get("LB_V295_PTA_FABRICATED_SHELL_V015")
if shell is None or not shell.static_mesh_component.set_static_mesh(mesh):
    raise RuntimeError("v016 shell replacement failed")
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    shell.static_mesh_component.set_material(index, slot.material_interface)
shell.set_actor_label("LB_V300_PTA_SEGMENTED_BALANCED_SHELL")
shell.tags = [unreal.Name("LB.Asset.Candidate.v300") if str(tag) == "LB.Asset.Candidate.v295" else tag for tag in shell.tags]
shell.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"), True)
shell.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
shell.static_mesh_component.set_editor_property("generate_overlap_events", False)
shell.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)

light_changes = []
for label, target in LIGHT_TARGETS.items():
    actor = by_label.get(label)
    if actor is None:
        raise RuntimeError(f"missing measured light {label}")
    component = actor.get_component_by_class(unreal.LightComponent)
    if component is None:
        raise RuntimeError(f"missing light component {label}")
    before = float(component.get_editor_property("intensity"))
    component.set_editor_property("intensity", target)
    light_changes.append({"label": label, "before": before, "after": target})

ppv = by_label.get("LB_INT_FRONT_FrontEndFixedExposure")
if not isinstance(ppv, unreal.PostProcessVolume):
    raise RuntimeError("measured global post-process volume missing")
settings = ppv.get_editor_property("settings")
exposure_before = {}
exposure_after = {
    "auto_exposure_bias": 0.25,
    "auto_exposure_min_brightness": 0.45,
    "auto_exposure_max_brightness": 2.20,
    "auto_exposure_speed_up": 2.0,
    "auto_exposure_speed_down": 1.0,
    "local_exposure_highlight_contrast_scale": 0.72,
    "local_exposure_shadow_contrast_scale": 0.78,
    "film_slope": 0.76,
    "film_toe": 0.43,
    "film_shoulder": 0.38,
    "film_white_clip": 0.0,
}
for name, target in exposure_after.items():
    exposure_before[name] = float(settings.get_editor_property(name))
    settings.set_editor_property(name, target)
ppv.set_editor_property("settings", settings)

camera_labels = []
for label, location, target, fov in CAMERAS:
    camera = api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    if camera is None:
        raise RuntimeError(label)
    camera.set_actor_label(label)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0/9.0, "constrain_aspect_ratio": True})
    camera.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.TrainA.v300"), unreal.Name("LB.Asset.Candidate.v300"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    camera_labels.append(label)

train_count = sum(1 for actor in api.get_all_level_actors() if "LB.PressTrain.Installed.TRAIN_A" in {str(tag) for tag in actor.tags})
origin, extent = shell.get_actor_bounds(False, False)
bounds = {"min_cm": [origin.x-extent.x, origin.y-extent.y, origin.z-extent.z], "max_cm": [origin.x+extent.x, origin.y+extent.y, origin.z+extent.z]}
failures = []
if train_count != 338:
    failures.append(f"Train A contract changed: {train_count}")
if len(light_changes) != 8:
    failures.append(f"light change count {len(light_changes)}")
if len(camera_labels) != 3:
    failures.append(f"camera count {len(camera_labels)}")
if str(shell.static_mesh_component.get_collision_profile_name()) != "NoCollision" or shell.static_mesh_component.get_editor_property("can_ever_affect_navigation"):
    failures.append("shell collision/navigation changed")
if not levels.save_current_level():
    failures.append("save failed")
if sha256(BASE_FILE) != EXPECTED_BASE_SHA:
    failures.append("protected v295 changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-train-a-balanced-lighting-build-v300/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__MEASURED_TRAIN_A_LIGHTING_EXPOSURE_SUCCESSOR__VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V300_NOT_A_PARENT",
    "base": BASE,
    "map": MAP,
    "base_sha256": EXPECTED_BASE_SHA,
    "map_sha256": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "source_audit": "Saved/Audits/PressShopIntegration/press_shop_train_a_lighting_exposure_audit_v295.json",
    "train_a_actor_count": train_count,
    "shell_asset": SHELL_ASSET,
    "shell_world_bounds": bounds,
    "light_changes": light_changes,
    "exposure_before": exposure_before,
    "exposure_after": exposure_after,
    "evidence_cameras": camera_labels,
    "unchanged_contracts": ["runtime actors", "transforms", "collision", "navigation", "station authority", "motion bindings", "control-room orchestration", "save authority"],
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
