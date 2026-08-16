"""Build camera/light-only v004 successor of the exact local-origin v003 assembly."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR005ExteriorEnclosureAssemblyCandidate_v003"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005ExteriorEnclosureLightingCandidate_v004"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr005_exterior_enclosure_lighting_build_v004.json"
BASE_PACKAGE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR005ExteriorEnclosureAssemblyCandidate_v003.umap"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


base_hash_before = sha256(BASE_PACKAGE)
if library.does_asset_exist(MAP):
    raise RuntimeError(MAP)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not clone {BASE}")
common = ["LB.Asset.Candidate.v004", "LB.Asset.CandidateNotPromoted", "LB.PR005.ExteriorEnclosure.LightingStudy"]

internal = []
for x in (-180.0, 180.0):
    for y in (-300.0, 0.0, 300.0):
        light = actors_api.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x, y, 315.0), unreal.Rotator(-90.0, 0.0, 0.0))
        light.set_actor_label(f"LB_PR005_V004_InternalLinearLED_{len(internal)+1:02d}")
        light.get_component_by_class(unreal.RectLightComponent).set_editor_properties({
            "intensity": 95.0, "source_width": 330.0, "source_height": 70.0,
            "attenuation_radius": 620.0, "cast_shadows": False,
            "light_color": unreal.Color(220, 229, 230, 255),
        })
        light.tags = [unreal.Name(value) for value in common + ["LB.Environment.Light.InternalTask"]]
        internal.append(light)

fills = []
for label, location, target in (
        ("OperatorFill", (-470.0, -360.0, 210.0), (-100.0, -80.0, 140.0)),
        ("UtilitiesFill", (470.0, 330.0, 220.0), (100.0, 50.0, 140.0)),
        ("OutletFill", (0.0, -570.0, 180.0), (0.0, -300.0, 110.0))):
    loc = unreal.Vector(*location)
    light = actors_api.spawn_actor_from_class(unreal.RectLight, loc, unreal.MathLibrary.find_look_at_rotation(loc, unreal.Vector(*target)))
    light.set_actor_label("LB_PR005_V004_" + label)
    light.get_component_by_class(unreal.RectLightComponent).set_editor_properties({
        "intensity": 58.0, "source_width": 300.0, "source_height": 260.0,
        "attenuation_radius": 760.0, "cast_shadows": False,
        "light_color": unreal.Color(214, 224, 226, 255),
    })
    light.tags = [unreal.Name(value) for value in common + ["LB.Environment.Light.ServiceFill"]]
    fills.append(light)


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label("LB_PR005_V004_CAM_" + label)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    actor.tags = [unreal.Name(value) for value in common + ["LB.Camera.Validation", "LB.Camera.Fixed.PR005Lighting.v004"]]
    return actor


cameras = [
    camera("OperatorThreeQuarter", (-820.0, 820.0, 390.0), (0.0, 0.0, 145.0), 46.0),
    camera("ProcessGlazing", (-720.0, -690.0, 235.0), (0.0, -250.0, 115.0), 44.0),
    camera("MaintenanceSide", (850.0, 620.0, 300.0), (80.0, 20.0, 140.0), 48.0),
    camera("ElevatedFlow", (-780.0, 880.0, 650.0), (0.0, 0.0, 120.0), 52.0),
]
failures = []
if len(internal) != 6 or len(fills) != 3 or len(cameras) != 4:
    failures.append("unexpected light/camera count")
if not levels.save_current_level():
    failures.append("could not save v004")
base_hash_after = sha256(BASE_PACKAGE)
if base_hash_after != base_hash_before:
    failures.append("protected v003 map changed")
report = {
    "$schema": "cairnwell/audit/press-shop-pr005-exterior-enclosure-lighting-build-v004/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__INTERNAL_LINEAR_LED_AND_SERVICE_FILL_LIGHTING_BUILT__VISUAL_GATE_REQUIRED__NOT_INTEGRATED_NOT_PROMOTED" if not failures else "FAIL__PR005_V004_LIGHTING_BUILD__NOT_INTEGRATED_NOT_PROMOTED",
    "source_map": BASE, "map": MAP,
    "internal_task_lights": [actor.get_actor_label() for actor in internal],
    "service_fill_lights": [actor.get_actor_label() for actor in fills],
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "geometry_materials_pivots_or_runtime_authority_changed": False,
    "world_placement": "LOCAL_ORIGIN_STUDY_ONLY__TBC_NOT_INVENTED",
    "promotion_authorized": False, "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
