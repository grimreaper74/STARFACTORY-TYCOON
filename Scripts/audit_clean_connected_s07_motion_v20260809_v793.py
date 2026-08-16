from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math, unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Maps/LB_PressShop_CleanConnectedS07_v20260809_v791"
OUT = ROOT / "Saved/Audits/PressShopIntegration/clean_connected_s07_hierarchy_motion_v20260809_v795.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
sha = lambda: hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if OUT.exists() or sha() != EXPECTED:
    raise RuntimeError("fresh/protected invariant")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("load failed")
all_actors = actors.get_all_level_actors()
by_label = {actor.get_actor_label(): actor for actor in all_actors}
roles = ["BASE", "TURN", "LOWER", "UPPER", "WRIST", "TOOL"]
parents = {"BASE": None, "TURN": "BASE", "LOWER": "TURN", "UPPER": "LOWER", "WRIST": "UPPER", "TOOL": "WRIST"}
failures, records = [], {}

for train in "ABCD":
    train_actors = {}
    for role in roles:
        label = f"LB_CLEAN_Train{train}_S07_ConnectedRobot_{role}_v791"
        actor = by_label.get(label)
        if actor is None:
            failures.append("missing " + label)
        else:
            train_actors[role] = actor
    if len(train_actors) != 6:
        continue
    hierarchy = {}
    for role, expected_parent in parents.items():
        actual = train_actors[role].get_attach_parent_actor()
        actual_role = None
        if actual:
            actual_role = next((candidate for candidate, item in train_actors.items() if item == actual), actual.get_actor_label())
        hierarchy[role] = actual_role
        if actual_role != expected_parent:
            failures.append(f"{train} {role} parent {actual_role} expected {expected_parent}")
    base_component = train_actors["BASE"].static_mesh_component
    if base_component.get_editor_property("mobility") != unreal.ComponentMobility.STATIC:
        failures.append(f"{train} base not static")
    for role in roles[1:]:
        if train_actors[role].static_mesh_component.get_editor_property("mobility") != unreal.ComponentMobility.MOVABLE:
            failures.append(f"{train} {role} not movable")
    records[train] = {"hierarchy": hierarchy}

# Prove descendants follow an articulated parent without saving the transient pose.
train = "A"
train_actors = {role: by_label[f"LB_CLEAN_Train{train}_S07_ConnectedRobot_{role}_v791"] for role in roles}
turn = train_actors["TURN"]
original_rotation = turn.get_actor_rotation()
before = {role: train_actors[role].get_actor_rotation() for role in roles[2:]}
new_rotation = unreal.Rotator()
new_rotation.roll = original_rotation.roll
new_rotation.pitch = original_rotation.pitch
new_rotation.yaw = original_rotation.yaw + 20.0
turn.set_actor_rotation(new_rotation, False)
after = {role: train_actors[role].get_actor_rotation() for role in roles[2:]}
motion = {}
for role in roles[2:]:
    a, b = before[role], after[role]
    delta = {
        "roll": abs((b.roll - a.roll + 180.0) % 360.0 - 180.0),
        "pitch": abs((b.pitch - a.pitch + 180.0) % 360.0 - 180.0),
        "yaw": abs((b.yaw - a.yaw + 180.0) % 360.0 - 180.0),
    }
    motion[role] = delta
    if abs(delta["yaw"] - 20.0) > 0.1 or delta["roll"] > 0.1 or delta["pitch"] > 0.1:
        failures.append(f"Train A {role} rotation propagation {delta} expected yaw 20")
turn.set_actor_rotation(original_rotation, False)
restored_tool = train_actors["TOOL"].get_actor_rotation()
tool_restore_error = abs((restored_tool.yaw - before["TOOL"].yaw + 180.0) % 360.0 - 180.0)
if tool_restore_error > 0.1:
    failures.append(f"tool restore error {tool_restore_error:.4f} deg")
if sha() != EXPECTED:
    failures.append("protected v438 changed")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FOUR_SIX_PART_S07_HIERARCHIES__DESCENDANT_ROTATIONS_FOLLOW_TURNTABLE__POSE_RESTORED_NOT_SAVED" if not failures else "FAIL__S07_HIERARCHY_MOTION_V795",
    "map": MAP, "train_records": records, "train_a_transient_rotation_deg": motion,
    "tool_restore_error_deg": tool_restore_error, "failures": failures,
    "protected_sha256": sha(), "meshy_credits_used": 0,
}, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_CLEAN_CONNECTED_S07_HIERARCHY_MOTION_V795_PASS")
