"""Fail-fast audit for the PR-005 gameplay contract and Unreal marker layer."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_PR005_ModularValidation"
CONTRACT = Path(unreal.Paths.project_dir()) / "SourceAssets/PR005/pr005_gameplay_contract_v001.json"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/pr005_gameplay_contract_audit_v001.json"

contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)

actors = actor_system.get_all_level_actors()
by_label = {actor.get_actor_label(): actor for actor in actors}
errors = []


def label(prefix, identifier):
    return prefix + identifier.replace("-", "_").replace(" ", "_")


def require_actor(actor_label, required_tags):
    actor = by_label.get(actor_label)
    if actor is None:
        errors.append(f"missing actor {actor_label}")
        return
    actual = {str(value) for value in actor.get_editor_property("tags")}
    missing = sorted(set(required_tags) - actual)
    if missing:
        errors.append(f"{actor_label} missing tags {missing}")


require_actor("LB_PR005_TRIGGER_StationZone", ["LB.Station.Zone", "LB.Station.PR-005"])
for port in contract["ports"]:
    required = ["LB.Material.Port", f"LB.Id.{port['id']}", "LB.Station.PR-005"]
    require_actor(label("LB_PR005_PORT_", port["id"]), required)
    require_actor(label("LB_PR005_TRIGGER_", port["id"]), required + ["LB.Gameplay.BufferSensor"])
for point in contract["interaction_points"]:
    required = ["LB.Interaction.Point", f"LB.Id.{point['id']}", "LB.Station.PR-005"]
    require_actor(label("LB_PR005_IP_", point["id"]), required)
    require_actor(label("LB_PR005_TRIGGER_", point["id"]), required + ["LB.Gameplay.InteractionRange"])

mesh_actors = [
    actor for actor in actors
    if isinstance(actor, unreal.StaticMeshActor)
    and "LB.Asset.Candidate.v001" in {str(value) for value in actor.get_editor_property("tags")}
]
mover_actors = [
    actor for actor in mesh_actors
    if "LB.Motion.Mover" in {str(value) for value in actor.get_editor_property("tags")}
]
if len(mesh_actors) != 59:
    errors.append(f"expected 59 PR-005 mesh actors, found {len(mesh_actors)}")
if len(mover_actors) < 25:
    errors.append(f"expected at least 25 tagged movers, found {len(mover_actors)}")

result = {
    "status": "PASS" if not errors else "FAIL",
    "station_id": contract["station_id"],
    "contract_ports": len(contract["ports"]),
    "contract_interaction_points": len(contract["interaction_points"]),
    "contract_conditions": len(contract["commissioning_conditions"]),
    "mesh_actor_count": len(mesh_actors),
    "tagged_mover_count": len(mover_actors),
    "errors": errors,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
if errors:
    raise RuntimeError("LINE_BOSS_PR005_GAMEPLAY_CONTRACT_FAIL " + "; ".join(errors))
unreal.log(
    "LINE_BOSS_PR005_GAMEPLAY_CONTRACT_PASS "
    f"ports={result['contract_ports']} interactions={result['contract_interaction_points']} "
    f"conditions={result['contract_conditions']} meshes={len(mesh_actors)} movers={len(mover_actors)}"
)
