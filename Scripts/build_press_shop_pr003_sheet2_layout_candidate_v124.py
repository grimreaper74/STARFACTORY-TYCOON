"""Build isolated v124 PR-003 two-row-by-six layout from retained v118.

Sheet 2 fixes the 12 coil centres as six east-west positions in each of two
north-south rows. Every saddle, coil, bay marker and label moves with its slot.
PR-004, cranes, safety routes and gameplay authority remain unchanged.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004WrapResponseCandidate_v118"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124"
OUT = ROOT / "Saved/Audits/press_shop_pr003_sheet2_layout_build_v124.json"
INSPECTION = ROOT / "Saved/Audits/press_shop_pr003_layout_inspection_v118.json"

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if lib.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not create isolated v124 from {BASE}")

inspection = json.loads(INSPECTION.read_text(encoding="utf-8"))
if inspection.get("current_layout", {}).get("unique_x_count") != 3 or inspection.get("current_layout", {}).get("unique_y_count") != 4:
    raise RuntimeError("v118 3x4 source-layout contract changed")

# Sheet 2: six positions at 2.2 m pitch in each row; row centres are 6.0 m
# apart. Coordinates are mapped to the established Unreal PR-003 datum.
target_x = (-7000.0, -6780.0, -6560.0, -6340.0, -6120.0, -5900.0)
target_centres = {}
for index in range(1, 13):
    column = (index - 1) % 6
    row_y = -2300.0 if index <= 6 else -1700.0
    target_centres[f"CS-{index:02d}"] = [target_x[column], row_y, 146.0]

pattern = re.compile(r"CS-(0[1-9]|1[0-2])")
source_centres = {
    slot: values["packaged_coil_cm"]
    for slot, values in inspection["slot_centres"].items()
}
moved = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    matches = pattern.findall(label)
    if not matches:
        matches = [match for tag in actor.tags for match in pattern.findall(str(tag))]
    if not matches:
        continue
    slot = f"CS-{matches[0]}"
    source = source_centres[slot]
    target = target_centres[slot]
    delta = unreal.Vector(target[0] - source[0], target[1] - source[1], 0.0)
    before = actor.get_actor_location()
    actor.set_actor_location(before + delta, False, False)
    prior_tags = [str(value) for value in actor.tags]
    actor.tags = [unreal.Name(value) for value in dict.fromkeys(prior_tags + [
        "LB.Asset.Candidate.v124", "LB.PR003.Layout.AuthoritativeSheet2.6x2",
        f"LB.PR003.Layout.Slot.{slot}",
    ])]
    moved.append({
        "actor": label,
        "slot": slot,
        "before_cm": [round(float(before.x), 3), round(float(before.y), 3), round(float(before.z), 3)],
        "after_cm": [round(float((before + delta).x), 3), round(float((before + delta).y), 3), round(float((before + delta).z), 3)],
        "delta_cm": [round(float(delta.x), 3), round(float(delta.y), 3), 0.0],
    })


def camera(label, location, target, fov):
    value = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    value.set_actor_label(label)
    value.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        value.get_actor_location(), unreal.Vector(*target)), False)
    value.camera_component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True,
        "post_process_blend_weight": 1.0,
    })
    value.tags = [unreal.Name(value) for value in (
        "LB.Camera.Validation", "LB.Camera.Fixed.PR003Sheet2.v124",
        "LB.Asset.Candidate.v124", "LB.Asset.CandidateNotPromoted")]
    return value


cameras = [
    camera("LB_PR003_V124_CAM_Sheet2Top", (-6450.0, -2000.0, 2200.0), (-6450.0, -2000.0, 0.0), 58.0),
    camera("LB_PR003_V124_CAM_Sheet2Oblique", (-7900.0, 250.0, 1250.0), (-6450.0, -2000.0, 120.0), 54.0),
]

# Verify the actual packaged-coil centres after all cluster moves.
actual_centres = {}
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith("LB_INT_FRONT_CS-") or "PackagedMasterCoil" not in label:
        continue
    match = pattern.search(label)
    if match:
        location = actor.get_actor_location()
        actual_centres[f"CS-{match.group(1)}"] = [round(float(location.x), 3), round(float(location.y), 3), round(float(location.z), 3)]

failures = []
if len(moved) != 122:
    failures.append(f"expected 122 slot-cluster actors, moved {len(moved)}")
if actual_centres != target_centres:
    failures.append(f"packaged-coil target mismatch actual={actual_centres}")
if len({value[0] for value in actual_centres.values()}) != 6 or len({value[1] for value in actual_centres.values()}) != 2:
    failures.append("actual layout is not 6x2")
if not levels.save_current_level():
    failures.append("could not save isolated v124")

report = {
    "$schema": "cairnwell/audit/press-shop-pr003-sheet2-layout-build-v124/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_V124_AUTHORITATIVE_SHEET2_6X2_COIL_STORE_BUILT__VISUAL_AND_EXACT_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V124_SHEET2_LAYOUT_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "authoritative_reference": "Docs/References/PressShop_Revised_BareCoil_FrontEnd/v001/Sheet_2_PR001_to_PR005_Operational_Plan.png",
    "source_layout": inspection["current_layout"],
    "target_layout": {"columns": 6, "rows": 2, "x_pitch_cm": 220.0, "row_pitch_cm": 600.0, "centres": target_centres},
    "moved_actor_count": len(moved),
    "moves": moved,
    "fixed_cameras": [value.get_actor_label() for value in cameras],
    "pr004_or_pr005_geometry_changed": False,
    "collision_settings_changed": False,
    "machinery_or_gameplay_authority_changed": False,
    "v118_changed": False,
    "promotion_authorized": False,
    "press_shop_complete": False,
    "failures": failures,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "moved_actor_count": len(moved),
                  "target_layout": report["target_layout"], "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
