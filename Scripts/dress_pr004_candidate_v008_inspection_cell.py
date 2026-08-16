"""Add reusable inspection, safety and band-recovery dressing to PR-004 v008."""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v008"
ROOT = "/Game/LineBoss/IndustrialKit/PressShop/FrontEndDressing"
PREFIX = "LB_PR004_DRESS08_"
OUT = PROJECT / "Saved/Audits/pr004_v008_inspection_dressing.json"

MODULES = [
    ("FaceInspectionMast_S", "SM_LB_InspectionMast_3000_v001", (-680, -360, 0), 0, "LB.Sensor.FaceInspection.South"),
    ("FaceInspectionMast_N", "SM_LB_InspectionMast_3000_v001", (-680, 360, 0), 180, "LB.Sensor.FaceInspection.North"),
    ("BandCompactorBin", "SM_LB_PackagingRecoveryBin_v001", (700, 380, 0), 180, "LB.Waste.SteelBand.CompactorBin"),
    ("InspectionServiceCabinet", "SM_LB_ServiceCabinet_1800_v001", (880, 360, 0), 180, "LB.Utilities.InspectionCabinet"),
    ("EStop_WestTransfer", "SM_LB_EStopPedestal_1300_v001", (-980, -210, 0), 90, "LB.Safety.EStop.WestTransfer"),
    ("EStop_EastTransfer", "SM_LB_EStopPedestal_1300_v001", (980, -210, 0), -90, "LB.Safety.EStop.EastTransfer"),
    ("EStop_Operator", "SM_LB_EStopPedestal_1300_v001", (-260, -520, 0), 0, "LB.Safety.EStop.Operator"),
]

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

try:
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")
    for actor in list(actors.get_all_level_actors()):
        if actor.get_actor_label().startswith(PREFIX):
            actors.destroy_actor(actor)

    spawned = []
    for name, asset_name, location, yaw, role in MODULES:
        mesh = unreal.load_asset(f"{ROOT}/{asset_name}")
        if not isinstance(mesh, unreal.StaticMesh):
            raise RuntimeError(f"Missing dressing mesh {asset_name}")
        actor = actors.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(0, 0, yaw)
        )
        actor.set_actor_label(PREFIX + name)
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        actor.set_editor_property("tags", [
            unreal.Name("LB.PR004.Candidate_v008"), unreal.Name(role),
            unreal.Name("LB.Asset.Candidate.NotPromoted"),
        ])
        spawned.append({"label": actor.get_actor_label(), "asset": mesh.get_path_name(), "role": role, "location_cm": list(location)})

    if not levels.save_current_level():
        raise RuntimeError("Failed to save dressed PR-004 v008")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "$schema": "line-boss/audit/pr004-v008-inspection-dressing/v1",
        "map": MAP,
        "status": "CANDIDATE_DRESSING_PASS__VISUAL_AND_RUNTIME_REVIEW_REQUIRED",
        "modules": spawned,
        "limitations": [
            "recovery bin is a reusable visual module; powered band-compaction internals remain required",
            "inspection masts require runtime camera/light bindings",
            "E-stops require safety-permissive bindings",
        ],
        "promotion_supported": False,
    }, indent=2), encoding="utf-8")
    unreal.log(f"LINE_BOSS_PR004_V008_DRESSING_PASS modules={len(spawned)} audit={OUT}")
finally:
    unreal.SystemLibrary.quit_editor()
