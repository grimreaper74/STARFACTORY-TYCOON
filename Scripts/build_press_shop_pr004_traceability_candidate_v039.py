"""Put live heat/lot/barcode data onto the existing secondary coil panels."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004TraceabilityCandidate_v039"
PAPER = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v026/M_LB_CoilLabelPaper_v026"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_traceability_candidate_v039.json"
PREFIXES = ("LB_COIL_TRACE_V039_", "LB_COIL_BARCODE_V039_", "LB_COIL_TRACE_PANEL_V039_")
ATTACHMENT_TAG = unreal.Name("LB.CoilSlot.CS-10.Attachment")
COMMON_TAGS = [
    unreal.Name("LB.Asset.Candidate.v039"),
    unreal.Name("LB.Material.PackagedCoilTraceability"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
]

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIXES) or actor.get_actor_label().startswith("LB_PR004_V039_CAM_"):
        actors.destroy_actor(actor)

plane = lib.load_asset("/Engine/BasicShapes/Plane")
paper = lib.load_asset(PAPER)
if plane is None or paper is None:
    raise RuntimeError(f"Missing trace panel dependencies plane={plane} paper={paper}")


def trace_values(label, ordinal):
    if "CS-10" in label:
        return "HT-CW26-08417", "LOT-MCXU-260804-A", "503184064100010"
    slot_match = re.search(r"CS-(\d+)", label)
    if slot_match:
        number = int(slot_match.group(1))
        return f"HT-CW26-{8400 + number:05d}", f"LOT-MCXU-260804-{number:02d}", f"5031840641{number:05d}"
    if "PR001" in label:
        return "HT-CW26-08391", "LOT-RCV-260804-01", "503184063900001"
    if "PR002" in label:
        return "HT-CW26-08396", "LOT-QA-260804-01", "503184063960001"
    return f"HT-CW26-{8500 + ordinal:05d}", f"LOT-MCXU-260804-{ordinal:02d}", f"5031840642{ordinal:05d}"


def configure_text(actor, text, size, color):
    component = actor.get_editor_property("text_render")
    component.set_mobility(unreal.ComponentMobility.MOVABLE)
    component.set_text(text)
    component.set_world_size(size)
    component.set_text_render_color(color)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    component.set_editor_property("cast_shadow", False)


packages = []
station = None
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label == "LB_INT_PR004_V024_InteractiveUnpackageStation":
        station = actor
    if (label.endswith("_PackagedMasterCoil_v024")
            and unreal.Name("LB.Material.PackagedCoil") in list(actor.tags)):
        packages.append(actor)

packages.sort(key=lambda item: item.get_actor_label())
created = []
for ordinal, package in enumerate(packages, 1):
    label = package.get_actor_label()
    heat_id, lot_id, barcode = trace_values(label, ordinal)
    origin = package.get_actor_location()
    # This overlays the small blank physical panel already authored on the wrap.
    panel_location = unreal.Vector(origin.x - 27.0, origin.y + 75.3, origin.z - 36.0)
    panel = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, panel_location, unreal.Rotator(roll=90.0, pitch=0.0, yaw=0.0))
    panel.set_actor_label(f"LB_COIL_TRACE_PANEL_V039_{label}")
    panel.set_actor_scale3d(unreal.Vector(0.24, 0.15, 1.0))
    panel.tags = list(COMMON_TAGS)
    panel.static_mesh_component.set_static_mesh(plane)
    panel.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    panel.static_mesh_component.set_material(0, paper)
    panel.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    panel.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    panel.static_mesh_component.set_editor_property("cast_shadow", False)

    trace = actors.spawn_actor_from_class(
        unreal.TextRenderActor,
        unreal.Vector(panel_location.x, panel_location.y + 0.45, panel_location.z + 3.0),
        unreal.Rotator(roll=0.0, pitch=0.0, yaw=90.0))
    trace.set_actor_label(f"LB_COIL_TRACE_V039_{label}")
    trace.tags = list(COMMON_TAGS)
    configure_text(trace, f"HEAT {heat_id}\nLOT  {lot_id}", 2.20, unreal.Color(30, 34, 38, 255))

    barcode_actor = actors.spawn_actor_from_class(
        unreal.TextRenderActor,
        unreal.Vector(panel_location.x, panel_location.y + 0.46, panel_location.z - 4.5),
        unreal.Rotator(roll=0.0, pitch=0.0, yaw=90.0))
    barcode_actor.set_actor_label(f"LB_COIL_BARCODE_V039_{label}")
    barcode_actor.tags = list(COMMON_TAGS)
    configure_text(barcode_actor, f"|||| ||| ||||  {barcode}", 1.35, unreal.Color(18, 20, 22, 255))

    if "CS-10" in label:
        for item in (panel, trace, barcode_actor):
            item.tags = list(item.tags) + [ATTACHMENT_TAG]
    created.extend((panel, trace, barcode_actor))

if station is None:
    raise RuntimeError("Missing native PR-004 station")

scene_components = {component.get_name(): component for component in station.get_components_by_class(unreal.SceneComponent)}
wrapped = scene_components.get("PR004_WrappedCoilVisual")
native_panel = scene_components.get("PR004_WrappedCoilTraceLabelVisual")
native_trace = scene_components.get("PR004_WrappedCoilTraceText")
native_barcode = scene_components.get("PR004_WrappedCoilBarcodeText")
if any(component is None for component in (wrapped, native_panel, native_trace, native_barcode)):
    raise RuntimeError(f"Missing native traceability components: {sorted(scene_components)}")

origin = wrapped.get_world_location()
panel_location = unreal.Vector(origin.x - 27.0, origin.y + 75.3, origin.z - 36.0)
native_panel.set_static_mesh(plane)
native_panel.set_material(0, paper)
native_panel.set_world_location(panel_location, False, False)
native_panel.set_world_rotation(unreal.Rotator(roll=90.0, pitch=0.0, yaw=0.0), False, False)
native_panel.set_world_scale3d(unreal.Vector(0.24, 0.15, 1.0))
native_panel.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
native_panel.set_editor_property("can_ever_affect_navigation", False)
native_panel.set_editor_property("cast_shadow", False)
native_trace.set_world_location(unreal.Vector(panel_location.x, panel_location.y + 0.45, panel_location.z + 3.0), False, False)
native_trace.set_world_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=90.0), False, False)
native_trace.set_world_scale3d(unreal.Vector(1.0, 1.0, 1.0))
native_trace.set_world_size(2.20)
native_barcode.set_world_location(unreal.Vector(panel_location.x, panel_location.y + 0.46, panel_location.z - 4.5), False, False)
native_barcode.set_world_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=90.0), False, False)
native_barcode.set_world_scale3d(unreal.Vector(1.0, 1.0, 1.0))
native_barcode.set_world_size(1.35)


def add_camera(label, location, target, fov):
    rotation = unreal.MathLibrary.find_look_at_rotation(location, target)
    camera = actors.spawn_actor_from_class(unreal.CameraActor, location, rotation)
    camera.set_actor_label(label)
    camera.tags = list(COMMON_TAGS) + [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.Traceability.v039")]
    camera.camera_component.set_field_of_view(fov)
    return camera


# Deposited panel close-up and a wider context shot are both fixed and repeatable.
add_camera("LB_PR004_V039_CAM_TraceDeposit",
           unreal.Vector(-4600.0, -1450.0, 255.0),
           unreal.Vector(-5077.0, -1924.7, 101.0), 34.0)

source_camera = next((actor for actor in actors.get_all_level_actors()
                      if actor.get_actor_label() == "LB_PR004_V035_CAM_CHookPurposeBuilt"), None)
if source_camera is None:
    raise RuntimeError("Missing retained C-hook fixed camera")
carry_camera = actors.spawn_actor_from_class(
    unreal.CameraActor, source_camera.get_actor_location(), source_camera.get_actor_rotation())
carry_camera.set_actor_label("LB_PR004_V039_CAM_TraceCarry")
carry_camera.tags = list(COMMON_TAGS) + [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.Traceability.v039")]
carry_camera.camera_component.set_field_of_view(30.0)

if len(packages) != 14 or len(created) != 42:
    raise RuntimeError(f"Unexpected trace inventory packages={len(packages)} actors={len(created)}")
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-traceability-candidate-v039/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "LIVE_SECONDARY_TRACEABILITY_PANEL_BUILT__TECHNICAL_AND_VISUAL_REGATES_REQUIRED__NOT_PROMOTED",
    "source_map": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v038",
    "candidate_map": MAP,
    "external_packaged_coils": len(packages),
    "external_trace_actors": len(created),
    "native_components": [native_panel.get_name(), native_trace.get_name(), native_barcode.get_name()],
    "cs10_traceability": {
        "heat_id": "HT-CW26-08417", "supplier_lot_id": "LOT-MCXU-260804-A",
        "barcode": "503184064100010", "moving_attachment_actor_count": 6,
    },
    "accepted_v006_preserved": True,
    "rejected_v007_v010_untouched": True,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_TRACEABILITY_V039_BUILD_PASS packages={len(packages)} actors={len(created)}")
unreal.SystemLibrary.quit_editor()
