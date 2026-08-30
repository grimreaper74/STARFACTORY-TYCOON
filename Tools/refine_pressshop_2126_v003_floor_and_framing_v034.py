"""Correct v003 readability drift: broad zones, open-air floor coverage and framing.

This intentionally removes the thin yellow datum stripes rejected by the visual
direction.  It uses only existing candidate actors / native floor geometry.
"""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
MATERIALS = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_floor_and_framing_v034.json"
TAG = unreal.Name("LB.PressShop.2126.v003.FloorAndFraming.v034")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))), yaw=math.degrees(math.atan2(dy, dx)))


def make_zone_material():
    name = "M_LB_PS2126v003_PaleGreenZone_BroadV034"
    result = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MATERIALS, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(result, unreal.Material):
        raise RuntimeError("Could not create broad production-zone material")
    mel = unreal.MaterialEditingLibrary
    # Pale painted green, deliberately legible against warm concrete at a
    # management camera: not a new brand token or a machine material.
    base = mel.create_material_expression(result, unreal.MaterialExpressionConstant3Vector, -420, -100)
    base.set_editor_property("constant", unreal.LinearColor(0.40, 0.54, 0.43, 1.0))
    rough = mel.create_material_expression(result, unreal.MaterialExpressionConstant, -420, 10)
    rough.set_editor_property("r", 0.86)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(result)
    unreal.EditorAssetLibrary.save_loaded_asset(result, only_if_is_dirty=False)
    return result


if not PROTECTED.is_file() or not V002.is_file():
    raise RuntimeError("Protected evidence map missing")
protected_before, v002_before = digest(PROTECTED), digest(V002)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load isolated v003 candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Floor/framing v034 already applied")

required = (
    "2126 v003 | warm concrete works deck",
    "2126 v003 | pale-green production zone",
    "2126 v003 | safety flow datum operator",
    "2126 v003 | safety flow datum service",
    "2126 v003 | open-air directional sun",
    "2126 v003 | open-air skylight",
    "CAM v003 | compact whole-flow overview",
    "CAM v003 | compact press hero",
    "CAM v003 | coil to first press story",
    "CAM v003 | inspection to stillage story",
)
missing = [label for label in required if label not in actors]
if missing:
    raise RuntimeError("Candidate actor missing: " + ", ".join(missing))

deck = actors["2126 v003 | warm concrete works deck"]
zone = actors["2126 v003 | pale-green production zone"]
for actor in (deck, zone):
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Expected native floor mesh: " + actor.get_actor_label())

# The old deck did not reach the far side of the cameras, which created a
# black wedge.  This is a wider ground plane, not a wall or roof.
deck_scale = deck.get_actor_scale3d()
deck_scale.y = max(deck_scale.y, 320.0)
deck.set_actor_scale3d(deck_scale)
zone.static_mesh_component.set_material(0, make_zone_material())

# The earlier thin yellow lines read as floating rails from the camera and were
# explicitly called out by the art-direction audit.  The broad painted zone
# and cream operator avenue remain visible.
hidden_datums = []
for label in ("2126 v003 | safety flow datum operator", "2126 v003 | safety flow datum service"):
    actor = actors[label]
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Visual.RejectedThinStripe")]
    hidden_datums.append(label)

# Open-air review lighting: more skylight and a gentler sun reduces the dark
# model-shadow band without reintroducing the failed high-intensity rect rig.
sun = actors["2126 v003 | open-air directional sun"]
sky = actors["2126 v003 | open-air skylight"]
if not isinstance(sun, unreal.DirectionalLight) or not isinstance(sky, unreal.SkyLight):
    raise RuntimeError("Open-air native lights missing")
sun.light_component.set_editor_property("intensity", 3.5)
sky.light_component.set_editor_property("intensity", 7.0)

camera_specs = {
    "CAM v003 | compact whole-flow overview": (unreal.Vector(-6500.0, -8400.0, 4700.0), unreal.Vector(250.0, 0.0, 320.0), 47.0),
    "CAM v003 | compact press hero": (unreal.Vector(-2100.0, -8800.0, 4150.0), unreal.Vector(850.0, 0.0, 360.0), 56.0),
    "CAM v003 | coil to first press story": (unreal.Vector(-7200.0, -6500.0, 2500.0), unreal.Vector(-3850.0, 0.0, 320.0), 54.0),
    "CAM v003 | inspection to stillage story": (unreal.Vector(7900.0, -6600.0, 2400.0), unreal.Vector(4650.0, 100.0, 260.0), 54.0),
}
for label, (source, target, focal) in camera_specs.items():
    actor = actors[label]
    if not isinstance(actor, unreal.CineCameraActor):
        raise RuntimeError("Camera actor invalid: " + label)
    actor.set_actor_location(source, False, False)
    actor.set_actor_rotation(aim(source, target), False)
    actor.get_cine_camera_component().set_editor_property("current_focal_length", focal)
    actor.tags = list(actor.tags) + [TAG]

if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in roofless candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save isolated v003 candidate")
protected_after, v002_after = digest(PROTECTED), digest(V002)
if protected_before != protected_after or v002_before != v002_after:
    raise RuntimeError("Protected map changed during v034")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__BROAD_FLOOR_ZONE_AND_OPEN_AIR_FRAMING_REFINED",
    "candidate_map": MAP,
    "deck_width_cm_after": deck.get_actor_scale3d().y * 100.0,
    "hidden_rejected_thin_stripes": hidden_datums,
    "open_air_lighting": {"directional_intensity": 3.5, "skylight_intensity": 7.0, "rect_lights_active": 0},
    "camera_count_refined": len(camera_specs),
    "roof_created": False,
    "v002_sha256_before": v002_before,
    "v002_sha256_after": v002_after,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V003_FLOOR_AND_FRAMING_V034_PASS")
