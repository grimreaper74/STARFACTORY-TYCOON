"""Refit PR-004 to the 11.5 x 12 m bay fixed by revised master Sheets 1-2."""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v009"
OUT = PROJECT / "Saved/Audits/pr004_v009_master_bay_refit.json"
PERIMETER = "LB_PR004_PERIMETER_"
ROOT = "/Game/LineBoss/IndustrialKit/Safety/Barrier_v002"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def move_prefix(prefix, dx=0, dy=0, dz=0):
    count = 0
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label().startswith(prefix):
            p = actor.get_actor_location()
            actor.set_actor_location(unreal.Vector(p.x + dx, p.y + dy, p.z + dz), False, False)
            count += 1
    return count


def spawn(label, mesh, location, yaw=0, role="LB.Safety.Perimeter"):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(0, 0, yaw))
    actor.set_actor_label(PERIMETER + label)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    actor.set_editor_property("tags", [unreal.Name("LB.PR004.Candidate_v009"), unreal.Name(role), unreal.Name("LB.Asset.Candidate.NotPromoted")])
    return actor


try:
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")

    for actor in list(actors.get_all_level_actors()):
        if actor.get_actor_label().startswith(PERIMETER):
            actors.destroy_actor(actor)

    # Refit equipment without scaling any machine geometry.
    moved = {
        "cradle": move_prefix("LB_PR004_powered_cradle_v001_", dx=370),
        "coil": move_prefix("LB_PR004_packaging_v004_PR004-PACK-BARE-COIL-v004", dx=370),
        "robot": move_prefix("LB_PR004_robot_v002_", dx=140),
    }

    by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
    dressing_targets = {
        "LB_PR004_DRESS08_FaceInspectionMast_S": (-310, -360, 0),
        "LB_PR004_DRESS08_FaceInspectionMast_N": (-310, 360, 0),
        "LB_PR004_DRESS08_BandCompactorBin": (400, 380, 0),
        "LB_PR004_DRESS08_InspectionServiceCabinet": (480, 180, 0),
        "LB_PR004_DRESS08_EStop_WestTransfer": (-480, -210, 0),
        "LB_PR004_DRESS08_EStop_EastTransfer": (480, -210, 0),
        "LB_PR004_DRESS08_EStop_Operator": (-180, -520, 0),
    }
    for label, location in dressing_targets.items():
        actor = by_label.get(label)
        if actor:
            actor.set_actor_location(unreal.Vector(*location), False, False)

    # Reframe evidence cameras for the map-fit envelope.
    camera_targets = {
        "LB_PR004_CAM_Overview_SW": ((-1050, -1350, 950), (0, 0, 80)),
        "LB_PR004_CAM_Overview_NE": ((1050, 1300, 900), (0, 0, 80)),
        "LB_PR004_CAM_Top": ((0, 0, 2100), (0, 0, 0)),
        "LB_PR004_CAM_CradleClose": ((-850, -420, 430), (-310, 0, 105)),
        "LB_PR004_CAM_PackagingClose": ((-850, 360, 420), (-310, 0, 105)),
        "LB_PR004_CAM_RobotTools": ((560, 0, 500), (140, 430, 110)),
        "LB_PR004_CAM_FilmDewrap": ((850, -420, 450), (430, 0, 100)),
    }
    for label, (location, target) in camera_targets.items():
        camera = by_label.get(label)
        if camera:
            start = unreal.Vector(*location)
            camera.set_actor_location(start, False, False)
            camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(start, unreal.Vector(*target)), False)

    for actor in actors.get_all_level_actors():
        if actor.get_actor_label() in ("LB_PR004_AB_Floor", "LB_PR004_Floor", "LB_PR004_ValidationFloor"):
            actor.set_actor_scale3d(unreal.Vector(12.0, 12.8, 0.1))

    panel100 = unreal.load_asset(f"{ROOT}/SM_LB_GuardPanel_1000x2400_v002")
    panel140 = unreal.load_asset(f"{ROOT}/SM_LB_GuardPanel_1400x2400_v002")
    panel200 = unreal.load_asset(f"{ROOT}/SM_LB_GuardPanel_2000x2400_v002")
    post = unreal.load_asset(f"{ROOT}/SM_LB_GuardPost_2500_v002")
    person_gate = unreal.load_asset(f"{ROOT}/SM_LB_InterlockedGate_1400x2400_v002")
    transfer_gate = unreal.load_asset(f"{ROOT}/SM_LB_InterlockedSlidingGate_2400x2400_v002")
    interlock = unreal.load_asset(f"{ROOT}/SM_LB_GuardInterlockBox_v002")
    if not all((panel100, panel140, panel200, post, person_gate, transfer_gate, interlock)):
        raise RuntimeError("Missing v002 barrier modules")

    # 11.5 m east-west bay, 12 m north-south. Transfer openings are 2.4 m.
    for side, y in (("N", 600),):
        for index in range(11):
            spawn(f"Panel_{side}_{index+1:02}", panel100, (-525 + index * 100, y, 0))
    for index, x in enumerate((-525, -425, -325, -225, -125, 125, 225, 325, 425, 525), 1):
        spawn(f"Panel_S_{index:02}", panel100, (x, -600, 0))
    for side, x in (("W", -575), ("E", 575)):
        for index, y in enumerate((-500, -330, -190, 190, 330, 500), 1):
            mesh = panel200 if abs(y) == 500 else panel140
            spawn(f"Panel_{side}_{index:02}", mesh, (x, y, 0), 90)

    points = set()
    for x in (-575, -75, 75, 575):
        points.add((x, -600))
    for x in range(-575, 576, 100):
        points.add((x, 600))
    for x in (-575, 575):
        for y in (-600, -400, -260, -120, 120, 260, 400, 600):
            points.add((x, y))
    for index, (x, y) in enumerate(sorted(points), 1):
        spawn(f"Post_{index:02}", post, (x, y, 0), role="LB.Safety.Perimeter.Post")

    spawn("Gate_Operator", person_gate, (-75, -600, 0), role="LB.Safety.Gate.Operator.Interlocked")
    spawn("Gate_WestTransfer", transfer_gate, (-575, -120, 0), 90, "LB.Safety.Gate.WestTransfer.Interlocked")
    spawn("Gate_EastTransfer", transfer_gate, (575, -120, 0), 90, "LB.Safety.Gate.EastTransfer.Interlocked")
    spawn("Interlock_Operator", interlock, (75, -600, 0), role="LB.Safety.Interlock.Operator")
    spawn("Interlock_West", interlock, (-575, 120, 0), 90, "LB.Safety.Interlock.WestTransfer")
    spawn("Interlock_East", interlock, (575, 120, 0), -90, "LB.Safety.Interlock.EastTransfer")

    if not levels.save_current_level():
        raise RuntimeError("Failed to save PR-004 v009 refit")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "$schema": "line-boss/audit/pr004-v009-master-bay-refit/v1",
        "map": MAP,
        "status": "MAP_FIT_CANDIDATE_PASS__VISUAL_AND_RUNTIME_GATES_REQUIRED",
        "authority": {
            "envelope": "Revised Sheets 1-2 fixed master plan",
            "equipment_arrangement": "Revised Sheet 3",
            "resolved_conflict": "22 m Sheet 3 envelope refitted to 11.5 m master-plan bay without scaling machinery",
        },
        "cell_envelope_cm": [1150, 1200],
        "centres_cm": {"cradle": [-310, 0], "robot": [140, 0], "rack": [140, 470]},
        "moved_counts": moved,
        "promotion_supported": False,
    }, indent=2), encoding="utf-8")
    unreal.log(f"LINE_BOSS_PR004_V009_MASTER_BAY_REFIT_PASS audit={OUT}")
finally:
    unreal.SystemLibrary.quit_editor()
