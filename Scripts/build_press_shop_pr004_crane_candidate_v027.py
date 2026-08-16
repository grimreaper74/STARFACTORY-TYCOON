"""Bind the installed modular 40 t crane to native PR-004 transfer authority."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneRuntimeCandidate_v027"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_crane_candidate_v027.json"
SOURCE_LABEL = "LB_INT_FRONT_CS-10_PackagedMasterCoil_v024"
CONTROLLER_LABEL = "LB_PR004_V027_40T_CraneController"
CRANE_TAG = unreal.Name("LB.Crane.40T")
SOURCE_TAG = unreal.Name("LB.CoilSlot.CS-10")
SOURCE_ATTACHMENT_TAG = unreal.Name("LB.CoilSlot.CS-10.Attachment")

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not lib.does_asset_exist(MAP):
    raise RuntimeError(
        f"Missing prepared map {MAP}; run prepare_press_shop_pr004_crane_candidate_v027.py in a clean process first")
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
source_coil = by_label.get(SOURCE_LABEL)
if source_coil is None:
    raise RuntimeError(f"Missing packaged source coil {SOURCE_LABEL}")
source_tags = list(source_coil.tags)
for tag in (SOURCE_TAG, unreal.Name("LB.PR003.Inventory.Authoritative"),
            unreal.Name("LB.Asset.Candidate.v027"), unreal.Name("LB.Asset.CandidateNotPromoted")):
    if tag not in source_tags:
        source_tags.append(tag)
source_coil.tags = source_tags
source_component = source_coil.get_component_by_class(unreal.StaticMeshComponent)
if source_component is None:
    raise RuntimeError("Selected CS-10 packaged coil has no StaticMeshComponent")
source_component.set_mobility(unreal.ComponentMobility.MOVABLE)

for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label() == CONTROLLER_LABEL:
        actors.destroy_actor(actor)

controller = actors.spawn_actor_from_class(
    unreal.LBBridgeCraneController, unreal.Vector(-5050.0, -2000.0, 20.0), unreal.Rotator())
if controller is None:
    raise RuntimeError("Could not spawn native 40 t crane controller")
controller.set_actor_label(CONTROLLER_LABEL)
controller.tags = [
    unreal.Name("LB.Asset.Candidate.v027"), unreal.Name("LB.PR004.Crane.Authority"),
    CRANE_TAG, unreal.Name("LB.Asset.CandidateNotPromoted"),
]
controller.set_editor_property("crane_tag", CRANE_TAG)
controller.set_editor_property("source_coil_tag", SOURCE_TAG)
controller.set_editor_property("source_attachment_tag", SOURCE_ATTACHMENT_TAG)
controller.set_editor_property("configured_coil_id", "MCX-U-CS10-0001")

# The packaged label is three separate non-colliding actors in v026: paper
# backing plus two live text layers. Bind all three to the coil so a crane pick
# never leaves its Cairnwell identity floating in the storage bay.
source_location = source_coil.get_actor_location()
source_attachments = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    location = actor.get_actor_location()
    is_backing = label == f"LB_COIL_LABEL_V026_{SOURCE_LABEL}"
    is_near_label_text = (
        label.startswith("LB_COIL_TEXT_V026_")
        and abs(location.x - source_location.x) < 5.0
        and abs(location.y - (source_location.y + 77.25)) < 5.0
        and abs(location.z - (source_location.z + 29.0)) < 20.0
    )
    if not (is_backing or is_near_label_text):
        continue
    tags = list(actor.tags)
    for tag in (SOURCE_ATTACHMENT_TAG, unreal.Name("LB.Asset.Candidate.v027"),
                unreal.Name("LB.Asset.CandidateNotPromoted")):
        if tag not in tags:
            tags.append(tag)
    actor.tags = tags
    attachment_component = actor.get_component_by_class(unreal.PrimitiveComponent)
    if attachment_component is not None:
        attachment_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    source_attachments.append(label)
if len(source_attachments) != 3:
    raise RuntimeError(f"Expected backing plus two text attachments for CS-10, found {source_attachments}")

motion_rows = []
for actor in actors.get_all_level_actors():
    if CRANE_TAG not in actor.tags:
        continue
    motion_tags = [str(tag) for tag in actor.tags if str(tag).startswith("LB.Motion.")]
    if not motion_tags:
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is not None:
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
    location = actor.get_actor_location()
    motion_rows.append({
        "label": actor.get_actor_label(),
        "motion_tags": motion_tags,
        "location_cm": [location.x, location.y, location.z],
        "mobility": str(component.get_editor_property("mobility")) if component is not None else None,
    })

required_motion = {
    "LB.Motion.CraneBridge", "LB.Motion.CraneTrolley", "LB.Motion.Hoist", "LB.Motion.CHook"
}
present_motion = {tag for row in motion_rows for tag in row["motion_tags"]}
missing_motion = sorted(required_motion - present_motion)
if missing_motion:
    raise RuntimeError(f"40 t crane motion modules missing: {missing_motion}")

if not levels.save_current_level():
    raise RuntimeError("Could not save v027 crane candidate")

station = next((actor for actor in actors.get_all_level_actors()
                if isinstance(actor, unreal.LBPR004Station)), None)
if station is None:
    raise RuntimeError("Missing native PR-004 station")
station_location = station.get_actor_location()

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-crane-candidate-v027/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "NATIVE_CRANE_AUTHORITY_BOUND__RUNTIME_AND_VISUAL_GATES_OPEN__NOT_PROMOTED",
    "base_map": BASE,
    "map": MAP,
    "controller": CONTROLLER_LABEL,
    "source_coil": {
        "label": SOURCE_LABEL,
        "tag": str(SOURCE_TAG),
        "location_cm": [source_location.x, source_location.y, source_location.z],
        "packaged": True,
        "mobility": str(source_component.get_editor_property("mobility")),
        "attachment_actors": sorted(source_attachments),
    },
    "drop_station_location_cm": [station_location.x, station_location.y, station_location.z],
    "motion_actor_count": len(motion_rows),
    "motion_actors": sorted(motion_rows, key=lambda row: row["label"]),
    "required_motion_tags": sorted(required_motion),
    "missing_motion_tags": missing_motion,
    "configured_coil_id": "MCX-U-CS10-0001",
    "runtime_gate": "OPEN",
    "visual_gate": "OPEN",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_CRANE_V027_BUILD_PASS actors={len(motion_rows)} output={OUT}")
