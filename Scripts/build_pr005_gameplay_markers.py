"""Build the PR-005 gameplay contract into the Unreal validation level.

The actors created here are engine-native semantic anchors and overlap volumes.
They intentionally contain no release art.  Runtime systems and Blueprints can
discover them by stable tags instead of depending on mesh names or positions.
"""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_PR005_ModularValidation"
CONTRACT = Path(unreal.Paths.project_dir()) / "SourceAssets/PR005/pr005_gameplay_contract_v001.json"
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/pr005_gameplay_markers_v001.json"
PREFIXES = ("LB_PR005_IP_", "LB_PR005_PORT_", "LB_PR005_TRIGGER_")
MOTION_TAGS = {
    "MandrelRotationMover": "LB.Motion.MandrelRotation",
    "PayoffCoilTransferMover": "LB.Motion.CoilRotation",
    "CoilCarLiftMover": "LB.Motion.CoilCarLift",
    "CoilCarWheelMover": "LB.Motion.CoilCarTravel",
    "KeeperArmMover": "LB.Motion.KeeperArm",
    "SnubberMover": "LB.Motion.SnubberArm",
    "PeelerBladeMover": "LB.Motion.PeelerBlade",
    "PinchUpperLiftMover": "LB.Motion.PinchLift",
    "PinchUpperRotationMover": "LB.Motion.PinchRotation",
    "PinchLowerRotationMover": "LB.Motion.PinchRotation",
    "PoweredRollerBedMover": "LB.Motion.FeedRoller",
    "ThreaderTableRollMover": "LB.Motion.ThreaderRoller",
    "ThreaderMover": "LB.Motion.ThreadingTable",
    "CropClampMover": "LB.Motion.CropClamp",
    "CropShearMover": "LB.Motion.CropShear",
    "CropPieceMover": "LB.Motion.CropPiece",
    "StripTravelWitnessMover": "LB.Motion.StripTravel",
    "OperatorGateMover": "LB.Motion.OperatorGate",
    "MaintenanceSlidingGateMover": "LB.Motion.MaintenanceGate",
    "HMIRearServiceDoorMover": "LB.Motion.HMIServiceDoor",
}
CANDIDATE_ASSET_ROOT = "/Game/LineBoss/Stations/Press/PR005/Candidate_v001/"


def stable_label(prefix, identifier):
    return prefix + identifier.replace("-", "_").replace(" ", "_")


def set_tags(actor, values):
    actor.set_editor_property("tags", [unreal.Name(value) for value in values])


def merge_tags(actor, values):
    existing = [str(value) for value in actor.get_editor_property("tags")]
    set_tags(actor, list(dict.fromkeys(existing + list(values))))


def spawn_anchor(actor_system, label, location, tags):
    actor = actor_system.spawn_actor_from_class(
        unreal.TargetPoint,
        unreal.Vector(*location),
        unreal.Rotator(),
    )
    actor.set_actor_label(label)
    set_tags(actor, tags)
    return actor


def spawn_trigger(actor_system, label, location, extent, tags):
    actor = actor_system.spawn_actor_from_class(
        unreal.TriggerBox,
        unreal.Vector(*location),
        unreal.Rotator(),
    )
    actor.set_actor_label(label)
    set_tags(actor, tags)
    collision = actor.get_editor_property("collision_component")
    collision.set_box_extent(unreal.Vector(*extent), True)
    collision.set_editor_property("component_tags", [unreal.Name("LB.Gameplay.Trigger")])
    collision.set_editor_property("can_ever_affect_navigation", False)
    return actor


contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)

all_actors = actor_system.get_all_level_actors()
for actor in all_actors:
    if actor.get_actor_label().startswith(PREFIXES):
        actor_system.destroy_actor(actor)

# Give every imported PR-005 mesh a stable gameplay identity.  Runtime code can
# now bind animation and state logic by tags rather than fragile actor labels.
tagged_meshes = 0
tagged_movers = 0
for actor in all_actors:
    label = actor.get_actor_label()
    if not label.startswith("LB_PR005_") or not isinstance(actor, unreal.StaticMeshActor):
        continue
    component = actor.get_editor_property("static_mesh_component")
    mesh = component.get_editor_property("static_mesh") if component else None
    if mesh is None or not mesh.get_path_name().startswith(CANDIDATE_ASSET_ROOT):
        # Validation scenery may share the label prefix, but it is not part of
        # the imported station assembly and must never enter machine counts.
        existing = [
            str(value) for value in actor.get_editor_property("tags")
            if not str(value).startswith(("LB.Station.PR-005", "LB.Asset.Candidate", "LB.Motion."))
        ]
        set_tags(actor, existing)
        continue
    tags = ["LB.Station.PR-005", "LB.Asset.Candidate.v001"]
    for token, motion_tag in MOTION_TAGS.items():
        if token in label:
            tags.extend(["LB.Motion.Mover", motion_tag])
            tagged_movers += 1
            break
    if label.endswith("_Static"):
        tags.append("LB.Motion.Static")
    merge_tags(actor, tags)
    tagged_meshes += 1

created = []
station_id = contract["station_id"]

footprint = contract["footprint"]
created.append(spawn_trigger(
    actor_system,
    "LB_PR005_TRIGGER_StationZone",
    footprint["centre"],
    footprint["half_extent"],
    ["LB.Station.Zone", f"LB.Station.{station_id}", "LB.Streaming.Press.FrontEnd"],
))

for port in contract["ports"]:
    label = stable_label("LB_PR005_PORT_", port["id"])
    tags = [
        "LB.Material.Port",
        f"LB.Material.Port.{port['kind'].title()}",
        f"LB.Material.{port['material']}",
        f"LB.Station.{station_id}",
        f"LB.Id.{port['id']}",
    ]
    created.append(spawn_anchor(actor_system, label, port["location"], tags))
    created.append(spawn_trigger(
        actor_system,
        stable_label("LB_PR005_TRIGGER_", port["id"]),
        port["location"],
        [65.0, 65.0, 85.0],
        tags + ["LB.Gameplay.BufferSensor"],
    ))

for point in contract["interaction_points"]:
    label = stable_label("LB_PR005_IP_", point["id"])
    tags = [
        "LB.Interaction.Point",
        f"LB.Interaction.{point['kind']}",
        f"LB.Station.{station_id}",
        f"LB.Id.{point['id']}",
    ]
    for action in point.get("actions", []):
        tags.append(f"LB.Action.{action}")
    created.append(spawn_anchor(actor_system, label, point["location"], tags))
    radius = float(point.get("radius", 65.0))
    created.append(spawn_trigger(
        actor_system,
        stable_label("LB_PR005_TRIGGER_", point["id"]),
        point["location"],
        [radius, radius, 100.0],
        tags + ["LB.Gameplay.InteractionRange"],
    ))

if not levels.save_current_level():
    raise RuntimeError("Failed to save PR-005 gameplay markers")

records = []
for actor in created:
    records.append({
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location_cm": list(actor.get_actor_location().to_tuple()),
        "tags": [str(tag) for tag in actor.get_editor_property("tags")],
    })
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "station_id": station_id,
    "contract": str(CONTRACT),
    "created_actor_count": len(records),
    "tagged_mesh_count": tagged_meshes,
    "tagged_mover_count": tagged_movers,
    "actors": records,
}, indent=2), encoding="utf-8")
unreal.log(
    "LINE_BOSS_PR005_GAMEPLAY_MARKERS_PASS "
    f"actors={len(records)} meshes={tagged_meshes} movers={tagged_movers} audit={AUDIT}"
)
