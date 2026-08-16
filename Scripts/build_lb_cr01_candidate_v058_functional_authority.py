"""Create CR01 v058 as C++ authority with the accepted v056 visual assembly."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
VISUAL_BP = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v056/Blueprints/BP_LB_CR01_CleaningAMR_v056"
BP_PATH = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v058/Blueprints/BP_LB_CR01_CleaningAMR_v058"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v058_functional_authority_build.json"

assets = unreal.EditorAssetLibrary
blueprints = unreal.BlueprintEditorLibrary

if assets.does_directory_exist("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v058"):
    raise RuntimeError("Refusing to overwrite preserved CR01 Candidate v058")

authority_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBCleaningAMR")
if authority_class is None:
    raise RuntimeError("Compiled ALBCleaningAMR class is unavailable")
visual_blueprint = assets.load_asset(VISUAL_BP)
if not isinstance(visual_blueprint, unreal.Blueprint):
    raise RuntimeError(f"Missing accepted visual Blueprint {VISUAL_BP}")
visual_class = blueprints.generated_class(visual_blueprint)
if visual_class is None:
    raise RuntimeError("Accepted v056 visual generated class is unavailable")

blueprint = blueprints.create_blueprint_asset_with_parent(BP_PATH, authority_class)
if not isinstance(blueprint, unreal.Blueprint):
    raise RuntimeError(f"Could not create {BP_PATH}")
blueprints.compile_blueprint(blueprint)
generated_class = blueprints.generated_class(blueprint)
default_object = unreal.get_default_object(generated_class)
presentation_components = default_object.get_components_by_class(unreal.ChildActorComponent)
if len(presentation_components) != 1:
    raise RuntimeError(f"Expected one inherited CR01 presentation component, found {len(presentation_components)}")
presentation = presentation_components[0]
if str(presentation.get_name()) not in ("CR01Presentation", "CR01Presentation_GEN_VARIABLE"):
    raise RuntimeError(f"Unexpected presentation component {presentation.get_name()}")
presentation.set_editor_property("child_actor_class", visual_class)
presentation.set_editor_property("component_tags", [
    unreal.Name("LB.CR01.Presentation.v056"),
    unreal.Name("LB.CR01.Presentation.VisualOnly"),
])
default_object.set_editor_property("tags", [
    unreal.Name("LB.SupportRobot.LB-CR01"),
    unreal.Name("LB.Asset.Candidate.v058"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.Brand.CairnwellAutomotive"),
    unreal.Name("LB.Site.MoorcrossWorks"),
    unreal.Name("LB.CR01.Authority.ProjectModule"),
    unreal.Name("LB.CR01.Presentation.v056"),
])
blueprints.compile_blueprint(blueprint)
if not assets.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {BP_PATH}")

audit = {
    "$schema": "line-boss/audit/lb-cr01-candidate-v058-functional-authority-build",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "COMPILED_CR01_AUTHORITY_WRAPPER_BUILT__FRESH_RUNTIME_GATES_REQUIRED__NOT_PROMOTED",
    "candidate_blueprint": BP_PATH,
    "parent_class": "/Script/LineBossCarFactory.LBCleaningAMR",
    "presentation_blueprint_preserved": VISUAL_BP,
    "presentation_mount": "CR01Presentation",
    "authority_blocking_collision": "RP01_CollisionRoot",
    "presentation_blocking_proxies_disabled_at_begin_play": [
        "Collision_CR01_Base", "Collision_CR01_Upper", "Collision_CR01_Roof"
    ],
    "cleaner_fault_scope": "LIGHT_PLAYER_READABLE_STATES_ONLY",
    "runtime_navigation_gate_passed": False,
    "runtime_cleaning_deployment_gate_passed": False,
    "save_reload_gate_passed": False,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_V058_FUNCTIONAL_AUTHORITY_BUILD_PASS audit={AUDIT}")

