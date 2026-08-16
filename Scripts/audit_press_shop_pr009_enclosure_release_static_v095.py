"""Read-only v095 enclosure asset, collision, binding, identity and authority audit."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from press_shop_pr009_enclosure_release_v095_config import TARGET_MAP


ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PR009_InMap_v095/enclosure_release_static_audit.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(TARGET_MAP):
    raise RuntimeError(TARGET_MAP)

all_actors = actors_api.get_all_level_actors()
modules = [a for a in all_actors if a.get_actor_label().startswith("LB_PR009_V095_ENC_SM_CA_MW_ENC_PR009_")]
stations = [a for a in all_actors if isinstance(a, unreal.LBPR009Station)]
flows = [a for a in all_actors if isinstance(a, unreal.LBPressShopMaterialFlowController)]
failures = []
if len(modules) != 7: failures.append(f"expected 7 enclosure modules, found {len(modules)}")
if len(stations) != 1: failures.append(f"expected 1 PR-009 authority, found {len(stations)}")
if len(flows) != 1: failures.append(f"expected 1 flow controller, found {len(flows)}")

rows = []
for actor in modules:
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh = component.static_mesh if component else None
    body = mesh.get_editor_property("body_setup") if mesh else None
    aggregate = body.get_editor_property("agg_geom") if body else None
    box_count = len(aggregate.get_editor_property("box_elems")) if aggregate else 0
    collision = str(component.get_editor_property("body_instance").get_editor_property("collision_enabled")) if component else "missing"
    scale = actor.get_actor_scale3d()
    identity_scale = all(abs(value - 1.0) < 0.0001 for value in (scale.x, scale.y, scale.z))
    if not identity_scale: failures.append(f"non-identity enclosure actor scale: {actor.get_actor_label()}")
    if mesh and "/v095/Enclosure/" not in mesh.get_path_name():
        failures.append(f"module does not use isolated v095 mesh: {actor.get_actor_label()}")
    rows.append({
        "actor": actor.get_actor_label(),
        "mesh": mesh.get_path_name() if mesh else None,
        "simple_box_count": box_count,
        "collision_trace_flag": str(body.get_editor_property("collision_trace_flag")) if body else None,
        "collision_enabled": collision,
        "identity_scale": identity_scale,
        "attach_parent": component.get_attach_parent().get_name() if component and component.get_attach_parent() else None,
    })

structure = next((r for r in rows if "Structure" in r["actor"]), None)
door = next((r for r in rows if "ServiceDoor" in r["actor"]), None)
if not structure or structure["simple_box_count"] != 10: failures.append("structure does not retain exactly 10 authored boxes")
if not door or door["simple_box_count"] != 1: failures.append("service door does not retain exactly 1 authored box")
if not door or door["attach_parent"] != "PR009_ServiceDoorMover": failures.append("service door is not bound to native hinge")
if structure and "QUERY_AND_PHYSICS" not in structure["collision_enabled"]: failures.append("structure does not block query and physics")
if door and "QUERY_AND_PHYSICS" not in door["collision_enabled"]: failures.append("service door does not block query and physics")

old_guards = []
for actor in all_actors:
    if "SM_CA_MW_PR009_GuardSet_01" not in actor.get_actor_label(): continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    old_guards.append({
        "actor": actor.get_actor_label(),
        "collision_enabled": str(component.get_editor_property("body_instance").get_editor_property("collision_enabled")),
        "affects_navigation": component.get_editor_property("can_ever_affect_navigation"),
    })
if len(old_guards) != 1: failures.append(f"expected one superseded guard, found {len(old_guards)}")
elif "NO_COLLISION" not in old_guards[0]["collision_enabled"]: failures.append("superseded guard still owns collision")

text_values = []
for actor in all_actors:
    if not isinstance(actor, unreal.TextRenderActor): continue
    text_values.append({"actor": actor.get_actor_label(), "text": str(actor.text_render.get_editor_property("text"))})
line_boss_text = [row for row in text_values if "LINE BOSS" in row["text"].upper() or "LINEBOSS" in row["text"].upper()]
if line_boss_text: failures.append("Line Boss working-title branding remains in-world")
identity = [row for row in text_values if row["actor"].startswith("LB_PR009_V095_ENC_TEXT_")]
if len(identity) != 3: failures.append(f"expected three enclosure identity lines, found {len(identity)}")

payload = {
    "$schema": "cairnwell/audit/pr009-enclosure-release-static-v095/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "target_map": TARGET_MAP,
    "status": "PASS__ENCLOSURE_ASSET_COLLISION_BINDING_IDENTITY_AUTHORITY__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "modules": rows,
    "authority_count": len(stations),
    "flow_controller_count": len(flows),
    "superseded_guard": old_guards,
    "identity": identity,
    "line_boss_in_world": line_boss_text,
    "full_blank_width_cm": 180.0,
    "portal_clear_width_cm": 290.0,
    "clearance_per_side_cm": 55.0,
    "failures": failures,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"PR009_V095_ENCLOSURE_STATIC_{'PASS' if not failures else 'FAIL'} output={OUT}")
if failures:
    raise RuntimeError(failures)
