"""Create CR01 v061 C++ authority around the v060 scrubber presentation."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
VISUAL_BP = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v060/Blueprints/BP_LB_CR01_CleaningAMR_v060"
BP_PATH = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v061/Blueprints/BP_LB_CR01_CleaningAMR_v061"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v061_functional_authority_build.json"

assets = unreal.EditorAssetLibrary
blueprints = unreal.BlueprintEditorLibrary

if assets.does_directory_exist("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v061"):
    raise RuntimeError("Refusing to overwrite preserved CR01 Candidate v061")

authority_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBCleaningAMR")
visual_blueprint = assets.load_asset(VISUAL_BP)
if authority_class is None or not isinstance(visual_blueprint, unreal.Blueprint):
    raise RuntimeError("CR01 v061 authority or v060 presentation dependency is unavailable")
visual_class = blueprints.generated_class(visual_blueprint)
if visual_class is None:
    raise RuntimeError("CR01 v060 presentation class is unavailable")

blueprint = blueprints.create_blueprint_asset_with_parent(BP_PATH, authority_class)
if not isinstance(blueprint, unreal.Blueprint):
    raise RuntimeError(f"Could not create {BP_PATH}")
blueprints.compile_blueprint(blueprint)
generated_class = blueprints.generated_class(blueprint)
default_object = unreal.get_default_object(generated_class)
mounts = default_object.get_components_by_class(unreal.ChildActorComponent)
if len(mounts) != 1:
    raise RuntimeError(f"Expected one inherited presentation mount, found {len(mounts)}")
mounts[0].set_editor_property("child_actor_class", visual_class)
mounts[0].set_editor_property("component_tags", [
    unreal.Name("LB.CR01.Presentation.v060"),
    unreal.Name("LB.CR01.Presentation.VisualOnly"),
])
default_object.set_editor_property("tags", [
    unreal.Name("LB.SupportRobot.LB-CR01"),
    unreal.Name("LB.Asset.Candidate.v061"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.Brand.CairnwellAutomotive"),
    unreal.Name("LB.Site.MoorcrossWorks"),
    unreal.Name("LB.CR01.Authority.ProjectModule"),
    unreal.Name("LB.CR01.Presentation.v060"),
    unreal.Name("LB.CR01.LightSupportStatesOnly"),
])
blueprints.compile_blueprint(blueprint)
if not assets.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {BP_PATH}")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/lb-cr01-candidate-v061-functional-authority-build",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "COMPILED_AUTHORITY_WRAPPER_WITH_V060_SCRUBBER_PRESENTATION__RUNTIME_REGRESSION_REQUIRED__NOT_PROMOTED",
    "candidate_blueprint": BP_PATH,
    "parent_class": "/Script/LineBossCarFactory.LBCleaningAMR",
    "presentation_blueprint_preserved": VISUAL_BP,
    "presentation_mount": "CR01Presentation",
    "fault_scope": "LIGHT_PLAYER_READABLE_SUPPORT_STATES_ONLY",
    "promotion_authorized": False,
}, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_V061_FUNCTIONAL_AUTHORITY_BUILD_PASS audit={AUDIT}")
