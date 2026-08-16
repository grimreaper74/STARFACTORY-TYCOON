"""Add practical low-speed swept movement to the CR01 reusable candidate."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_BP = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v056/Blueprints/BP_LB_CR01_CleaningAMR_v056"
BP_PATH = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v057/Blueprints/BP_LB_CR01_CleaningAMR_v057"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v057_movement_build.json"

assets = unreal.EditorAssetLibrary
bp_library = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_library = unreal.SubobjectDataBlueprintFunctionLibrary


def require(path, cls=None):
    asset = assets.load_asset(path)
    if asset is None or (cls is not None and not isinstance(asset, cls)):
        raise RuntimeError(f"Missing required asset {path}")
    return asset


if assets.does_directory_exist("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v057"):
    raise RuntimeError("Refusing to overwrite preserved CR01 Candidate v057")
if not assets.duplicate_asset(SOURCE_BP, BP_PATH):
    raise RuntimeError(f"Could not duplicate {SOURCE_BP} -> {BP_PATH}")
blueprint = require(BP_PATH, unreal.Blueprint)

handles = {}
objects = {}
for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    name = str(data_library.get_variable_name(data))
    obj = data_library.get_object_for_blueprint(data, blueprint) or data_library.get_object(data)
    if name and name != "None" and name not in handles:
        handles[name] = handle
        objects[name] = obj

if "CR01FloatingMovement" in handles:
    raise RuntimeError("CR01FloatingMovement already exists")
root_handles = []
for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    if data_library.is_default_scene_root(data):
        root_handles.append(handle)
if len(root_handles) != 1:
    raise RuntimeError(f"Expected one DefaultSceneRoot, found {len(root_handles)}")
collision = objects.get("Collision_CR01_Base")
if not isinstance(collision, unreal.PrimitiveComponent):
    raise RuntimeError("Missing blocking Collision_CR01_Base movement target")

result = subsystem.add_new_subobject(params=unreal.AddNewSubobjectParams(
    parent_handle=root_handles[0],
    new_class=unreal.FloatingPawnMovement,
    blueprint_context=blueprint,
    conform_transform_to_parent=False,
    skip_mark_blueprint_modified=False,
))
movement_handle = result[0]
if not data_library.is_handle_valid(movement_handle):
    raise RuntimeError(f"Could not add CR01 movement component: {result[1] if len(result) > 1 else ''}")
subsystem.rename_subobject(handle=movement_handle, new_name=unreal.Text("CR01FloatingMovement"))
data = subsystem.k2_find_subobject_data_from_handle(movement_handle)
movement = data_library.get_object_for_blueprint(data, blueprint) or data_library.get_object(data)
if not isinstance(movement, unreal.FloatingPawnMovement):
    raise RuntimeError("Could not resolve CR01FloatingMovement template")

movement.set_editor_properties({
    "max_speed": 120.0,
    "acceleration": 80.0,
    "deceleration": 120.0,
    "turning_boost": 4.0,
})
# Blueprint templates are not live Pawn-owned components, so calling
# SetUpdatedComponent here triggers the engine's runtime-owner ensure.  Persist
# the archetype reference instead; a fresh spawned-instance audit must prove
# that Unreal remaps it to the Pawn-owned collision instance before acceptance.
movement.set_editor_property("updated_component", collision)
movement.set_editor_property("component_tags", [
    unreal.Name("LB.CR01.Movement.LowSpeedAMR"),
    unreal.Name("LB.CR01.Navigation.RuntimeProofRequired"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
])

bp_library.compile_blueprint(blueprint)
generated_class = bp_library.generated_class(blueprint)
if generated_class is None:
    raise RuntimeError("CR01 v057 generated class missing")
unreal.get_default_object(generated_class).set_editor_property("tags", [
    unreal.Name("LB.SupportRobot.LB-CR01"),
    unreal.Name("LB.Asset.Candidate.v057"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.RP01.ParentCandidate.v003"),
    unreal.Name("LB.Brand.CairnwellAutomotive"),
    unreal.Name("LB.Site.MoorcrossWorks"),
    unreal.Name("LB.CR01.Movement.LowSpeedAMR"),
])
bp_library.compile_blueprint(blueprint)
if not assets.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {BP_PATH}")

audit = {
    "$schema": "line-boss/audit/lb-cr01-candidate-v057-movement-build",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "LOW_SPEED_SWEPT_MOVEMENT_COMPONENT_BUILT__FRESH_RELOAD_NAVIGATION_RUNTIME_GATE_REQUIRED__NOT_PROMOTED",
    "source_blueprint_preserved": SOURCE_BP,
    "candidate_blueprint": BP_PATH,
    "movement_component": "CR01FloatingMovement",
    "updated_component": "Collision_CR01_Base",
    "max_speed_cm_s": 120.0,
    "acceleration_cm_s2": 80.0,
    "deceleration_cm_s2": 120.0,
    "turning_boost": 4.0,
    "blocking_collision_proxies_inherited": 3,
    "cleaning_query_proxies_inherited": 5,
    "deep_fault_system_added": False,
    "runtime_navigation_gate_passed": False,
    "promotion_authorized": False
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_V057_MOVEMENT_BUILD_PASS audit={AUDIT}")
