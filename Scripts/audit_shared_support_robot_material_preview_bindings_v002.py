"""Fresh-reload audit of v002 swatch bindings and material parameters."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_SupportRobot_Materials_Candidate_v002"
ROOT = Path(unreal.Paths.project_dir())
OUTPUT = ROOT / "Saved/Audits/lb_support_robot_shared_material_preview_bindings_v002.json"
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mel = unreal.MaterialEditingLibrary

world = unreal.EditorLevelLibrary.get_editor_world()
current_package = world.get_outermost().get_name() if world is not None else ""
if current_package != MAP:
    raise RuntimeError(f"One-map rule violation: opened {current_package}, expected {MAP}")

rows = []
failures = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith("LB_MAT_V001_"):
        continue
    if not isinstance(actor, unreal.StaticMeshActor) or label in {"LB_MAT_V001_Floor", "LB_MAT_V001_Backdrop"}:
        continue
    component = actor.get_editor_property("static_mesh_component")
    material = component.get_material(0)
    if material is None:
        failures.append(f"{label}: missing material slot 0")
        continue
    row = {
        "actor": label,
        "material": material.get_path_name(),
        "material_class": material.get_class().get_name(),
    }
    if isinstance(material, unreal.MaterialInstanceConstant):
        colour = mel.get_material_instance_vector_parameter_value(material, "PaintColour")
        row["paint_colour_linear"] = [colour.r, colour.g, colour.b, colour.a]
        row["paint_coverage_bias"] = mel.get_material_instance_scalar_parameter_value(material, "PaintCoverageBias")
        row["dust_amount"] = mel.get_material_instance_scalar_parameter_value(material, "DustAmount")
        row["parent"] = material.get_editor_property("parent").get_path_name()
    else:
        failures.append(f"{label}: slot 0 is not a MaterialInstanceConstant")
    rows.append(row)

if len(rows) != 8:
    failures.append(f"Expected 8 swatches, found {len(rows)}")
if len({row.get("material") for row in rows}) != 8:
    failures.append("Swatches do not resolve to 8 distinct material instances")

result = {
    "$schema": "line-boss/audit/lb-support-robot-shared-material-preview-bindings-v002",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FRESH_RELOAD_BINDING_PASS__VISUAL_GATE_OPEN__NOT_PROMOTED" if not failures else "FRESH_RELOAD_BINDING_FAIL__NOT_PROMOTED",
    "map": MAP,
    "rows": sorted(rows, key=lambda row: row["actor"]),
    "failures": failures,
    "promotion_authorized": False,
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
if failures:
    unreal.log_error(f"LINE_BOSS_SUPPORT_ROBOT_MATERIAL_BINDING_V002_FAIL failures={failures}")
else:
    unreal.log(f"LINE_BOSS_SUPPORT_ROBOT_MATERIAL_BINDING_V002_PASS swatches={len(rows)} audit={OUTPUT}")
unreal.SystemLibrary.quit_editor()
