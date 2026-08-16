"""One-time v084 runtime repair: consolidate duplicate flow authority without visual edits."""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from press_shop_pr009_in_map_validation_config import TARGET_MAP


ROOT = Path(unreal.Paths.project_dir())
MATCH = re.search(r"_v(\d+)$", TARGET_MAP, re.IGNORECASE)
VERSION = f"v{MATCH.group(1)}" if MATCH else "unknown"
PREFIX = f"LB_PR009_V{MATCH.group(1)}_" if MATCH else "LB_PR009_"
OUT = ROOT / "Saved" / "Audits" / f"PR009_InMap_{VERSION}" / "material_flow_singleton_repair.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(TARGET_MAP):
    raise RuntimeError(f"Could not load {TARGET_MAP}")
actors = list(actors_api.get_all_level_actors())
pr008 = [actor for actor in actors if isinstance(actor, unreal.LBPR008Station)]
pr009 = [actor for actor in actors if isinstance(actor, unreal.LBPR009Station)]
flows = [actor for actor in actors if isinstance(actor, unreal.LBPressShopMaterialFlowController)]
if len(pr008) != 1 or len(pr009) != 1 or len(flows) != 2:
    raise RuntimeError(f"Repair precondition failed: PR008={len(pr008)} PR009={len(pr009)} flow={len(flows)}")

inherited = next((actor for actor in flows if "PR004_PR005" in actor.get_actor_label()), None)
duplicate = next((actor for actor in flows if actor.get_actor_label().startswith(PREFIX + "MaterialFlow_")), None)
if inherited is None or duplicate is None or inherited == duplicate:
    raise RuntimeError("Could not resolve inherited and PR-009 duplicate material-flow controllers")

inherited.bind_blank_stations(pr008[0], pr009[0])
existing_tags = list(inherited.tags)
for value in ("LB.Traceability.PR008.PR009", "LB.Asset.Candidate.v084"):
    name = unreal.Name(value)
    if name not in existing_tags:
        existing_tags.append(name)
inherited.tags = existing_tags
destroyed_label = duplicate.get_actor_label()
actors_api.destroy_actor(duplicate)
if not levels.save_current_level():
    raise RuntimeError(f"Could not save singleton repair to {TARGET_MAP}")

remaining = [actor for actor in actors_api.get_all_level_actors()
             if isinstance(actor, unreal.LBPressShopMaterialFlowController)]
payload = {
    "$schema": "cairnwell/audit/press-shop-pr009-material-flow-singleton-repair/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "target_map": TARGET_MAP,
    "status": "PASS__NOT_PROMOTED" if len(remaining) == 1 else "FAIL__NOT_PROMOTED",
    "retained_controller": inherited.get_actor_label(),
    "destroyed_duplicate": destroyed_label,
    "pr004_pr005_binding_preserved_on_retained_controller": True,
    "pr008_pr009_binding_applied_to_retained_controller": True,
    "visual_actor_changes": 0,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"CAIRNWELL_PR009_MATERIAL_FLOW_SINGLETON_REPAIR_{'PASS' if len(remaining) == 1 else 'FAIL'}")
unreal.SystemLibrary.quit_editor()
if len(remaining) != 1:
    raise RuntimeError("Material-flow singleton repair did not leave exactly one controller")
