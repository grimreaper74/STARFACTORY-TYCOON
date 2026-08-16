"""Add compact PR-004 stand/operator/transfer floor zoning to v025."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004InteractiveFloorCandidate_v025"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_interactive_floor_candidate_v025.json"
MESH_PATH = "/Engine/BasicShapes/Cube"
YELLOW_PATH = "/Game/LineBoss/Materials/M_LB_SafetyYellow"
GREEN_PATH = "/Game/LineBoss/Materials/FrontEnd/MI_LB_Floor_Walkway_Green"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load prepared map: {MAP}")
mesh = lib.load_asset(MESH_PATH)
yellow = lib.load_asset(YELLOW_PATH)
green = lib.load_asset(GREEN_PATH)
if mesh is None or yellow is None or green is None:
    raise RuntimeError("Missing shared floor-zoning mesh/material assets")

created = []


def marking(label, location, size_cm, material, role):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if actor is None:
        raise RuntimeError(f"Could not spawn floor marking {label}")
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(size_cm[0] / 100.0, size_cm[1] / 100.0, size_cm[2] / 100.0))
    actor.tags = [
        unreal.Name("LB.Asset.Candidate.v025"),
        unreal.Name("LB.PR004.FloorZoning"),
        unreal.Name(role),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    component.set_editor_property("cast_shadow", False)
    created.append({
        "actor": label,
        "location_cm": list(location),
        "size_cm": list(size_cm),
        "material": material.get_path_name(),
        "role": role,
    })


# Compact 5.2 m x 6.2 m boundary around the fixed powered stand. The 10 cm
# stripes replace the former full robot/cage footprint.
marking("LB_PR004_V025_StandBoundary_N", (-5360.0, -1690.0, 9.35), (520.0, 10.0, 1.0), yellow, "LB.PR004.Zone.StandBoundary")
marking("LB_PR004_V025_StandBoundary_S", (-5360.0, -2310.0, 9.35), (520.0, 10.0, 1.0), yellow, "LB.PR004.Zone.StandBoundary")
marking("LB_PR004_V025_StandBoundary_E", (-5100.0, -2000.0, 9.35), (10.0, 620.0, 1.0), yellow, "LB.PR004.Zone.StandBoundary")
marking("LB_PR004_V025_StandBoundary_W", (-5620.0, -2000.0, 9.35), (10.0, 620.0, 1.0), yellow, "LB.PR004.Zone.StandBoundary")

# A compact non-colliding operator pad on the approach side of the stand.
marking("LB_PR004_V025_OperatorPad", (-5360.0, -1490.0, 8.85), (420.0, 170.0, 0.8), green, "LB.PR004.Zone.OperatorAccess")
marking("LB_PR004_V025_OperatorPadEdge_N", (-5360.0, -1405.0, 9.35), (420.0, 8.0, 1.0), yellow, "LB.PR004.Zone.OperatorAccessEdge")
marking("LB_PR004_V025_OperatorPadEdge_S", (-5360.0, -1575.0, 9.35), (420.0, 8.0, 1.0), yellow, "LB.PR004.Zone.OperatorAccessEdge")
marking("LB_PR004_V025_OperatorPadEdge_E", (-5150.0, -1490.0, 9.35), (8.0, 170.0, 1.0), yellow, "LB.PR004.Zone.OperatorAccessEdge")
marking("LB_PR004_V025_OperatorPadEdge_W", (-5570.0, -1490.0, 9.35), (8.0, 170.0, 1.0), yellow, "LB.PR004.Zone.OperatorAccessEdge")

# Short two-metre-wide transfer lane from PR-004 toward PR-005.
marking("LB_PR004_V025_TransferLane_N", (-4725.0, -1900.0, 9.35), (650.0, 8.0, 1.0), yellow, "LB.PR004.Zone.TransferToPR005")
marking("LB_PR004_V025_TransferLane_S", (-4725.0, -2100.0, 9.35), (650.0, 8.0, 1.0), yellow, "LB.PR004.Zone.TransferToPR005")

if len(created) != 11:
    raise RuntimeError(f"Expected 11 v025 floor marking actors, created {len(created)}")
if not levels.save_current_level():
    raise RuntimeError("Could not save v025 floor candidate")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps({
    "$schema": "line-boss/audit/press-shop-pr004-interactive-floor-candidate-v025/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "ISOLATED_LOCAL_PR004_FLOOR_ZONING_CANDIDATE__NOT_PROMOTED",
    "source_map": "/Game/LineBoss/Maps/LB_PressShop_PR004WrappedStandCandidate_v024",
    "candidate_map": MAP,
    "scope": "PR-004 local floor only; storage bays and main pedestrian/logistics routes preserved",
    "stand_boundary_outer_cm": [520.0, 620.0],
    "operator_pad_cm": [420.0, 170.0],
    "transfer_lane_width_cm": 200.0,
    "created_actor_count": len(created),
    "created_actors": created,
    "all_markings_non_colliding": True,
    "all_markings_navigation_irrelevant": True,
    "accepted_v006_preserved": True,
    "interactive_v024_preserved": True,
    "fresh_fixed_camera_visual_gate": "OPEN",
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_INTERACTIVE_FLOOR_V025_BUILD_PASS markings={len(created)}")
unreal.SystemLibrary.quit_editor()
