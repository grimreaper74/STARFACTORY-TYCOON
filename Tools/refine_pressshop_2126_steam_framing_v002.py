"""Refine only the fresh 2126 candidate after its first live-D3D review.

The serial v002 capture proved that the cameras work, but also exposed two
Steam-blocking composition problems: tall placeholder perimeter masts filled
the foreground, and the three review cameras were far enough away that the
real Meshy press assets read as miniatures.  This pass removes those *candidate
only* framing obstructions and retargets the cameras around the actual five
Meshy machines.  It neither loads nor writes a protected map.
"""

import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_steam_framing_v002.json"

STRUCTURE_PREFIXES = (
    "2126 | open-bay structural mast ",
    "2126 | mast safety base ",
    "2126 | open-bay longitudinal gantry rail ",
)
CAMERAS = (
    # A line-wide hero: all five real press assets take most of the frame.
    ("CAM | 2126 Steam hero overview", (-11000.0, -10500.0, 5600.0), (-500.0, 0.0, 1850.0), 33.0),
    # Operator-side frame, deliberately at people/machine scale rather than bay scale.
    ("CAM | 2126 operator line", (-8300.0, -7200.0, 3000.0), (-800.0, 0.0, 1700.0), 42.0),
    # Close proof that the draw cell itself is a repaired Meshy press, not a cube proxy.
    ("CAM | 2126 draw nexus", (-8000.0, -5200.0, 2400.0), (-4200.0, 0.0, 1550.0), 50.0),
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    flat = math.sqrt(dx * dx + dy * dy)
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(dz, flat)),
        yaw=math.degrees(math.atan2(dy, dx)),
        roll=0.0,
    )


def hide_actor(actor):
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load the fresh 2126 candidate")

actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
hidden = []
for label, actor in actors.items():
    if label.startswith(STRUCTURE_PREFIXES):
        hide_actor(actor)
        hidden.append(label)

if len(hidden) != 38:
    raise RuntimeError("Expected exactly 38 candidate-only open-bay placeholder pieces, found %d" % len(hidden))

camera_rows = []
for label, location_values, target_values, focal_length in CAMERAS:
    camera_actor = actors.get(label)
    if camera_actor is None or not isinstance(camera_actor, unreal.CineCameraActor):
        raise RuntimeError("Missing review camera: " + label)
    location = unreal.Vector(*location_values)
    target = unreal.Vector(*target_values)
    rotation = aim(location, target)
    camera_actor.set_actor_location(location, False, False)
    camera_actor.set_actor_rotation(rotation, False)
    camera_actor.get_cine_camera_component().set_editor_property("current_focal_length", focal_length)
    forward = camera_actor.get_actor_forward_vector()
    camera_rows.append({
        "label": label,
        "location_cm": list(location_values),
        "target_cm": list(target_values),
        "rotation": [rotation.pitch, rotation.yaw, rotation.roll],
        "forward": [forward.x, forward.y, forward.z],
        "focal_length_mm": focal_length,
    })

hero_location = unreal.Vector(*CAMERAS[0][1])
unreal.EditorLevelLibrary.set_level_viewport_camera_info(hero_location, aim(hero_location, unreal.Vector(*CAMERAS[0][2])))

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save refined candidate map")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed during candidate-only framing refinement")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__CANDIDATE_V002_STEAM_FRAMING_REFINED_AFTER_LIVE_D3D_REVIEW",
    "candidate_map": MAP,
    "hidden_candidate_only_placeholder_open_bay_structure": hidden,
    "removed_roof_or_wall_mesh": False,
    "cameras": camera_rows,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
    "review_finding": "The original v002 captures were structurally valid but visually rejected: masts obstructed the foreground and the actual Meshy presses read too small.",
    "scope": "fresh candidate map only; no new Meshy generation, no protected map mutation",
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_STEAM_FRAMING_V002_PASS: hidden=%d cameras=%d" % (len(hidden), len(camera_rows)))
