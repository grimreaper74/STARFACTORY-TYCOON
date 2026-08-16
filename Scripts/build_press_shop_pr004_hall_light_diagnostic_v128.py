"""Build isolated all-light-off diagnostic v128 directly from retained v124."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004HallLightDiagnostic_v128"
OUT = ROOT / "Saved/Audits/press_shop_pr004_hall_light_diagnostic_build_v128.json"
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if lib.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved diagnostic {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not create {MAP} from {BASE}")

disabled = []
component_classes = (
    unreal.PointLightComponent,
    unreal.SpotLightComponent,
    unreal.RectLightComponent,
    unreal.DirectionalLightComponent,
    unreal.SkyLightComponent,
)
for actor in actors_api.get_all_level_actors():
    component = None
    for component_class in component_classes:
        component = actor.get_component_by_class(component_class)
        if component is not None:
            break
    if component is None:
        continue
    disabled.append({
        "actor": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "old_intensity": float(component.get_editor_property("intensity")),
        "old_affects_world": bool(component.get_editor_property("affects_world")),
    })
    component.set_editor_property("affects_world", False)
    component.set_editor_property("intensity", 0.0)
    actor.tags = [unreal.Name(value) for value in dict.fromkeys(
        [str(value) for value in actor.tags] +
        ["LB.Asset.Diagnostic.v128", "LB.Lighting.AllOffDiagnostic"])]

failures = []
if len(disabled) != 46:
    failures.append(f"expected 46 lights, found {len(disabled)}")
if not levels.save_current_level():
    failures.append("could not save diagnostic map")

report = {
    "$schema": "line-boss/audit/press-shop-pr004-hall-light-diagnostic-build-v128/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_ALL_LIGHT_OFF_DIAGNOSTIC_BUILT__NEVER_PROMOTABLE" if not failures else "FAIL__V128_DIAGNOSTIC_BUILD",
    "source_map": BASE,
    "map": MAP,
    "disabled_lights": disabled,
    "purpose": "Determine whether the fixed support-fleet wall/ceiling pools survive with every authored light disabled.",
    "lineage_rule": "Diagnostic only. Never promote and never use as a parent.",
    "promotion_authorized": False,
    "failures": failures,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "disabled": len(disabled), "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
