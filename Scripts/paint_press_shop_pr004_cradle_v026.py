"""Apply selective aged safety paint to the fixed PR-004 powered cradle."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
PAINT_PARENT = "/Game/LineBoss/Stations/Press/PR004/Candidate_v012/PaintSpecificMaterials/M_LB_PR004_AgedSafetyPaint_Master_v012"
PAINT = PAINT_PARENT
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_cradle_paint_v026.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary
paint = lib.load_asset(PAINT_PARENT)
if paint is None:
    raise RuntimeError(f"Missing layered PR-004 paint parent {PAINT_PARENT}")
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

rows = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith("LB_INT_PR004_V009_powered_cradle_v001_"):
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None or component.get_editor_property("static_mesh") is None:
        raise RuntimeError(f"Cradle actor has no mesh: {label}")
    changes = []
    for index, slot_name in enumerate(component.get_material_slot_names()):
        slot = str(slot_name)
        is_fixed_frame = label.endswith("_static") and "FrameCharcoal" in slot
        is_safety_paint = "SafetyYellow" in slot
        if not is_fixed_frame and not is_safety_paint:
            continue
        component.set_material(index, paint)
        changes.append({"slot_index": index, "slot_name": slot,
                        "role": "fixed_frame" if is_fixed_frame else "safety_accent"})
    rows.append({"actor": label, "changes": changes})

if len(rows) != 5 or sum(len(row["changes"]) for row in rows) != 6:
    raise RuntimeError(f"Unexpected cradle paint coverage actors={len(rows)} changes={rows}")
if not levels.save_current_level():
    raise RuntimeError("Could not save selectively painted PR-004 cradle")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "line-boss/audit/press-shop-pr004-cradle-paint-v026/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SELECTIVE_LAYERED_CRADLE_PAINT_APPLIED__VISUAL_GATE_OPEN__NOT_PROMOTED",
    "map": MAP,
    "paint_material": PAINT,
    "painted_actor_count": len(rows),
    "painted_slot_count": sum(len(row["changes"]) for row in rows),
    "preserved_unpainted_roles": ["load shoes", "rollers", "hydraulics", "chrome rods", "rubber", "fasteners", "hoses", "service plate"],
    "actors": rows,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_PR004_CRADLE_PAINT_V026_PASS")
unreal.SystemLibrary.quit_editor()
