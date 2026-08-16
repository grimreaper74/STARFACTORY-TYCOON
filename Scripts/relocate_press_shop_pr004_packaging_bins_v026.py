"""Bring segregated PR-004 packaging bins into the operator's local work area."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_packaging_bins_relocation_v026.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith("LB_PR004_V026_PackagingWaste_"):
        actors.destroy_actor(actor)

band_bin = next((actor for actor in actors.get_all_level_actors()
                 if actor.get_actor_label() == "LB_INT_PR004_V009_DRESS08_BandCompactorBin"), None)
if band_bin is None:
    raise RuntimeError("Missing inherited PR-004 packaging recovery bin")

band_component = band_bin.get_component_by_class(unreal.StaticMeshComponent)
bin_mesh = band_component.get_editor_property("static_mesh") if band_component else None
if band_component is None or bin_mesh is None:
    raise RuntimeError("Inherited PR-004 recovery bin has no static mesh")

placements = [
    ("SteelBand", "STEEL BANDS", unreal.Vector(-4700.0, -1620.0, 0.0), unreal.Color(32, 36, 40, 255)),
    ("WrapCard", "WRAP + CARD", unreal.Vector(-4700.0, -1420.0, 0.0), unreal.Color(32, 36, 40, 255)),
]

created = []
for index, (stream, wording, location, colour) in enumerate(placements):
    if index == 0:
        bin_actor = band_bin
        bin_actor.set_actor_location(location, False, False)
        bin_actor.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=90.0), False)
    else:
        bin_actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, location,
                                                  unreal.Rotator(roll=0.0, pitch=0.0, yaw=90.0))
        bin_actor.set_actor_label(f"LB_PR004_V026_PackagingWaste_{stream}Bin")
        component = bin_actor.static_mesh_component
        component.set_static_mesh(bin_mesh)
        for slot in range(band_component.get_num_materials()):
            material = band_component.get_material(slot)
            if material is not None:
                component.set_material(slot, material)
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        component.set_collision_profile_name("BlockAll")
        component.set_editor_property("can_ever_affect_navigation", True)
    bin_actor.tags = [unreal.Name("LB.Asset.Candidate.v026"), unreal.Name("LB.Station.PR-004"),
                      unreal.Name(f"LB.Waste.{stream}"), unreal.Name("LB.Asset.CandidateNotPromoted")]

    text = actors.spawn_actor_from_class(unreal.TextRenderActor,
        unreal.Vector(location.x - 47.5, location.y, location.z + 67.0),
        unreal.Rotator(roll=0.0, pitch=0.0, yaw=180.0))
    text.set_actor_label(f"LB_PR004_V026_PackagingWaste_{stream}Label")
    text.tags = [unreal.Name("LB.Asset.Candidate.v026"), unreal.Name(f"LB.Waste.{stream}"),
                 unreal.Name("LB.Asset.CandidateNotPromoted")]
    text_component = text.get_editor_property("text_render")
    text_component.set_text(wording)
    text_component.set_world_size(6.8)
    text_component.set_text_render_color(colour)
    text_component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    text_component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    text_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    text_component.set_editor_property("can_ever_affect_navigation", False)
    created.append({"stream": stream, "wording": wording,
                    "location_cm": [location.x, location.y, location.z]})

if not levels.save_current_level():
    raise RuntimeError("Could not save v026 after packaging-bin relocation")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "line-boss/audit/press-shop-pr004-packaging-bins-relocation-v026/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SEGREGATED_BINS_RELOCATED_TO_PR004_OPERATOR_EDGE__VISUAL_GATE_OPEN__NOT_PROMOTED",
    "map": MAP,
    "station_center_cm": [-5050.0, -2000.0, 134.63],
    "operator_pad_bounds_cm": {"x": [-5260.0, -4840.0], "y": [-1575.0, -1405.0]},
    "transfer_lane_y_cm": [-2100.0, -1900.0],
    "placements": created,
    "operator_pad_obstructed": False,
    "transfer_lane_obstructed": False,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_PR004_PACKAGING_BINS_V026_RELOCATION_PASS")
unreal.SystemLibrary.quit_editor()
