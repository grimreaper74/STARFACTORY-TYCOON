"""Build PR-004 Candidate_v008 around the revised 22 m x 12 m Pro authority."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE_MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v007"
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v008"
AUDIT = ROOT / "Saved/Audits/pr004_authoritative_layout_candidate_v008.json"
PREFIX = "LB_PR004_PERIMETER_"

DEST = "/Game/LineBoss/IndustrialKit/Safety/Barrier_v002"
ASSETS = {
    100.0: "SM_LB_GuardPanel_1000x2400_v002",
    140.0: "SM_LB_GuardPanel_1400x2400_v002",
    200.0: "SM_LB_GuardPanel_2000x2400_v002",
}
POST = "SM_LB_GuardPost_2500_v002"
PERSON_GATE = "SM_LB_InterlockedGate_1400x2400_v002"
TRANSFER_GATE = "SM_LB_InterlockedSlidingGate_2400x2400_v002"
INTERLOCK = "SM_LB_GuardInterlockBox_v002"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asset_subsystem = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)

# Level duplication must happen in a separate editor session from loading the
# duplicate; UE 5.8 can retain the newly created UWorld and fail its world-leak
# guard if both operations occur in one commandlet.  The prior preparation
# session creates MAP.  This assembly session only loads and edits it.
if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
    raise RuntimeError(f"Prepared duplicate is missing: {MAP}")
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}

# Remove the obsolete v007 perimeter and the former HMI placement.  The source
# actors remain available in v007 as rejected evidence.
for actor in list(actors.get_all_level_actors()):
    label = actor.get_actor_label()
    if label.startswith(PREFIX) or label.startswith("LB_PR004_HMI04_"):
        actors.destroy_actor(actor)
    elif "LB_PR004_film_dewrap_v004_" in label:
        # Full film handling is outside the approved bare-coil baseline.
        actors.destroy_actor(actor)


def move_group(prefix: str, delta: tuple[float, float, float]):
    moved = []
    for actor in actors.get_all_level_actors():
        if not actor.get_actor_label().startswith(prefix):
            continue
        old = actor.get_actor_location()
        actor.set_actor_location(unreal.Vector(old.x + delta[0], old.y + delta[1], old.z + delta[2]), False, False)
        moved.append(actor.get_actor_label())
    return moved


# Sheet 3 local coordinates use cell centre as (0,0): cradle at (-680,0),
# robot at (0,0), rack north/rear.  Preserve authored internal pivots by moving
# complete actor groups rather than rebuilding their joint transforms.
packaging_moved = move_group("LB_PR004_packaging_v004_", (-400.0, -120.0, 0.0))
robot_moved = move_group("LB_PR004_robot_v002_", (40.0, -70.0, 0.0))

by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
rack_targets = {
    "LB_PR004_robot_v002_tool_rack": ((0.0, 470.0, 0.0), 0.0),
    "LB_PR004_robot_v002_band_tool": ((-135.0, 437.0, 108.0), 0.0),
    "LB_PR004_robot_v002_wrap_tool": ((-45.0, 437.0, 108.0), 0.0),
    "LB_PR004_robot_v002_edge_tool": ((45.0, 437.0, 108.0), 0.0),
    "LB_PR004_robot_v002_inspection_tool": ((135.0, 437.0, 108.0), 0.0),
}
for label, (location, yaw) in rack_targets.items():
    actor = by_label.get(label)
    if actor is None:
        raise RuntimeError(f"Missing rack actor {label}")
    actor.set_actor_location(unreal.Vector(*location), False, False)
    actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, yaw), False)

# Existing validation floor is expanded to cover the revised envelope.  The
# precise building-floor material and markings remain a later visual gate.
for actor in actors.get_all_level_actors():
    if actor.get_actor_label() in ("LB_PR004_AB_Floor", "LB_PR004_Floor", "LB_PR004_ValidationFloor"):
        actor.set_actor_scale3d(unreal.Vector(22.8, 12.8, 0.1))

meshes = {}
for name in [*ASSETS.values(), POST, PERSON_GATE, TRANSFER_GATE, INTERLOCK]:
    mesh = unreal.load_asset(f"{DEST}/{name}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing imported safety module {name}")
    meshes[name] = mesh

spawned = []
post_points = set()
panel_index = 0


def tags(*values):
    return [unreal.Name("LB.PR004.Candidate_v008"), unreal.Name("LB.Asset.Candidate.NotPromoted"), *(unreal.Name(v) for v in values)]


def spawn(name, mesh_name, location, yaw, role, movable=False):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(0.0, 0.0, yaw))
    actor.set_actor_label(PREFIX + name)
    actor.static_mesh_component.set_static_mesh(meshes[mesh_name])
    actor.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE if movable else unreal.ComponentMobility.STATIC)
    actor.set_editor_property("tags", tags(role))
    spawned.append({"actor": actor.get_actor_label(), "location_cm": list(location), "yaw_deg": yaw, "role": role})
    return actor


def tile_horizontal(start_x, end_x, y, lengths, side):
    global panel_index
    cursor = start_x
    post_points.add((cursor, y))
    for length in lengths:
        panel_index += 1
        spawn(f"Panel_{side}_{panel_index:02d}", ASSETS[length], (cursor + length / 2.0, y, 0.0), 0.0, "LB.Safety.Perimeter.Panel")
        cursor += length
        post_points.add((cursor, y))
    if abs(cursor - end_x) > 0.01:
        raise RuntimeError(f"Horizontal tiling mismatch {side}: {cursor} != {end_x}")


def tile_vertical(x, start_y, end_y, lengths, side):
    global panel_index
    cursor = start_y
    post_points.add((x, cursor))
    for length in lengths:
        panel_index += 1
        spawn(f"Panel_{side}_{panel_index:02d}", ASSETS[length], (x, cursor + length / 2.0, 0.0), 90.0, "LB.Safety.Perimeter.Panel")
        cursor += length
        post_points.add((x, cursor))
    if abs(cursor - end_y) > 0.01:
        raise RuntimeError(f"Vertical tiling mismatch {side}: {cursor} != {end_y}")


# Sheet 3: 22 x 12 m cell. Transfer openings are centred on the west/east
# material-flow axis. The 1.4 m operator gate is on the south edge pending the
# final gate coordinate confirmation from the dimension table.
tile_horizontal(-1100.0, 1100.0, 600.0, [200.0] * 11, "N")
tile_horizontal(-1100.0, -180.0, -600.0, [140.0] * 3 + [100.0] * 5, "S_W")
tile_horizontal(-40.0, 1100.0, -600.0, [200.0] * 5 + [140.0], "S_E")
tile_vertical(-1100.0, -600.0, -120.0, [200.0, 140.0, 140.0], "W_S")
tile_vertical(-1100.0, 120.0, 600.0, [140.0, 140.0, 200.0], "W_N")
tile_vertical(1100.0, -600.0, -120.0, [200.0, 140.0, 140.0], "E_S")
tile_vertical(1100.0, 120.0, 600.0, [140.0, 140.0, 200.0], "E_N")

post_points.update({(-180.0, -600.0), (-40.0, -600.0), (-1100.0, -120.0), (-1100.0, 120.0), (1100.0, -120.0), (1100.0, 120.0)})
for index, (x, y) in enumerate(sorted(post_points), 1):
    spawn(f"Post_{index:02d}", POST, (x, y, 0.0), 0.0, "LB.Safety.Perimeter.Post")

spawn("Gate_Operator", PERSON_GATE, (-180.0, -600.0, 0.0), 0.0, "LB.Safety.Gate.Operator.Interlocked", True)
spawn("Gate_CraneTransfer", TRANSFER_GATE, (-1100.0, -120.0, 0.0), 90.0, "LB.Safety.Gate.CraneTransfer.Interlocked", True)
spawn("Gate_PR005Transfer", TRANSFER_GATE, (1100.0, -120.0, 0.0), 90.0, "LB.Safety.Gate.PR005Transfer.Interlocked", True)
spawn("Interlock_Operator", INTERLOCK, (-40.0, -600.0, 0.0), 0.0, "LB.Safety.Interlock.Operator")
spawn("Interlock_CraneTransfer", INTERLOCK, (-1100.0, 120.0, 0.0), 90.0, "LB.Safety.Interlock.CraneTransfer")
spawn("Interlock_PR005Transfer", INTERLOCK, (1100.0, 120.0, 0.0), -90.0, "LB.Safety.Interlock.PR005Transfer")

if not levels.save_current_level():
    raise RuntimeError("Could not save Candidate_v008")

tool_distances = {}
for label, (location, _yaw) in rack_targets.items():
    if label.endswith("tool_rack"):
        continue
    tool_distances[label] = round(math.dist((0.0, 0.0, 72.0), location), 3)

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/pr004-authoritative-layout-candidate-v008/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CANDIDATE_LAYOUT_ASSEMBLY_PASS__VISUAL_COLLISION_AND_RUNTIME_GATES_REQUIRED",
    "authority": "Docs/References/PressShop_Revised_BareCoil_FrontEnd/v001/Sheet_3_Revised_PR004_Cell.png",
    "map": MAP,
    "cell_envelope_cm": [2200.0, 1200.0, 370.0],
    "local_origin": "cell centre; +X east/material flow, +Y north",
    "fixed_centres_cm": {"coil_cradle": [-680.0, 0.0, 60.0], "robot_base": [0.0, 0.0, 0.0], "tool_rack": [0.0, 470.0, 0.0]},
    "moved_actor_counts": {"packaging_cradle_group": len(packaging_moved), "robot_group": len(robot_moved)},
    "tool_pivot_distances_cm": tool_distances,
    "perimeter": {"panels": panel_index, "posts": len(post_points), "gates": 3, "actors": spawned},
    "removed_from_baseline": ["full film dewrapper", "plastic compactor", "rigid wrapping shell"],
    "remaining_required_assets": ["steel-band compactor/bin", "face cameras", "bore/ID camera", "top camera", "inspection lighting", "south HMI/operator zone", "LOTO and E-stops", "ready/hold lights"],
    "remaining_gates": ["fixed-camera comparison", "simple release collision", "gate/interlock motion", "robot docking and swept collision", "navigation obstacle build", "runtime inspection/destrapping sequence"],
    "promotion_supported": False,
}, indent=2), encoding="utf-8")

unreal.log(f"LINE_BOSS_PR004_AUTHORITATIVE_LAYOUT_V008_PASS panels={panel_index} posts={len(post_points)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
