"""Build v129 diagnostic from retained v124 with seven non-grid task spotlights disabled."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004TaskSpotDiagnostic_v129"
OUT = ROOT / "Saved/Audits/press_shop_pr004_task_spot_diagnostic_build_v129.json"
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if lib.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved diagnostic {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not create {MAP} from {BASE}")

disabled = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith((
            "LB_PR004_V031_",
            "LB_PR004_V034_",
            "LB_PR004_V037_",
            "LB_PR004_V040_")):
        continue
    component = actor.get_component_by_class(unreal.SpotLightComponent)
    if component is None:
        continue
    disabled.append({"actor": label, "old_intensity": float(component.get_editor_property("intensity"))})
    component.set_editor_property("affects_world", False)
    component.set_editor_property("intensity", 0.0)
    actor.tags = [unreal.Name(value) for value in dict.fromkeys(
        [str(value) for value in actor.tags] +
        ["LB.Asset.Diagnostic.v129", "LB.Lighting.NonGridTaskSpotOffDiagnostic"])]

failures = []
if len(disabled) != 7:
    failures.append(f"expected seven non-grid task spots, found {len(disabled)}")
if not levels.save_current_level():
    failures.append("could not save diagnostic map")
report = {
    "$schema": "line-boss/audit/press-shop-pr004-task-spot-diagnostic-build-v129/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__SEVEN_NON_GRID_TASK_SPOTS_DISABLED__DIAGNOSTIC_ONLY" if not failures else "FAIL__V129_DIAGNOSTIC_BUILD",
    "source_map": BASE,
    "map": MAP,
    "disabled_task_spots": disabled,
    "retained_active_groups": ["two directional lights", "one skylight", "15 factory point fills", "15 v041 high-bay spotlights", "two PR005 rect lights", "emergency point lights"],
    "lineage_rule": "Diagnostic only. Never promote and never use as a parent.",
    "promotion_authorized": False,
    "failures": failures,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "disabled": len(disabled), "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
