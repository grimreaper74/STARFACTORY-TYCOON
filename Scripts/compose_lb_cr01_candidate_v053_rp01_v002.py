"""Compose preserved CR01 v052 payload with corrected reusable RP01 v002."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_BP = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v052/Blueprints/BP_LB_CR01_CleaningAMR_v052"
PARENT_BP = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v002/Blueprints/BP_LB_RP01_MobileBase"
BP_PATH = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v053/Blueprints/BP_LB_CR01_CleaningAMR_v053"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v053_rp01_v002_composition_build.json"

asset_library = unreal.EditorAssetLibrary
bp_library = unreal.BlueprintEditorLibrary


def require(path, cls=unreal.Blueprint):
    asset = asset_library.load_asset(path)
    if asset is None or not isinstance(asset, cls):
        raise RuntimeError(f"Missing required asset {path}")
    return asset


if asset_library.does_asset_exist(BP_PATH) or asset_library.does_directory_exist("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v053"):
    raise RuntimeError("Refusing to overwrite preserved CR01 Candidate v053")
source = require(SOURCE_BP)
parent = require(PARENT_BP)
parent_class = bp_library.generated_class(parent)
if parent_class is None:
    raise RuntimeError("RP01 v002 generated class is missing")
if not asset_library.duplicate_asset(SOURCE_BP, BP_PATH):
    raise RuntimeError(f"Could not duplicate {SOURCE_BP} -> {BP_PATH}")
blueprint = require(BP_PATH)
bp_library.reparent_blueprint(blueprint, parent_class)
bp_library.compile_blueprint(blueprint)
generated_class = bp_library.generated_class(blueprint)
if generated_class is None:
    raise RuntimeError("CR01 v053 generated class missing after reparent")
default_object = unreal.get_default_object(generated_class)
default_object.set_editor_property("tags", [
    unreal.Name("LB.SupportRobot.LB-CR01"),
    unreal.Name("LB.Asset.Candidate.v053"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.RP01.ParentCandidate.v002"),
    unreal.Name("LB.Safety.FaultLatched"),
])
if not asset_library.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {BP_PATH}")

result = {
    "$schema": "line-boss/audit/lb-cr01-candidate-v053-rp01-v002-composition-build",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CORRECTED_REUSABLE_PARENT_COMPOSITION_BUILT__FRESH_RELOAD_AND_CAMERA_GATES_REQUIRED__NOT_PROMOTED",
    "preserved_payload_blueprint": SOURCE_BP,
    "corrected_parent_blueprint": PARENT_BP,
    "candidate_blueprint": BP_PATH,
    "payload_mesh_namespace": "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v052/Meshes",
    "payload_material_namespace": "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v052/Materials",
    "source_assets_modified": False,
    "accepted_press_shop_map_modified": False,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_V053_COMPOSITION_BUILD_PASS audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
