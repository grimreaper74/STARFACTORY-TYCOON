"""Analytical full-contract sweep audit against PR-009 guarded-cell envelopes."""
import json
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
binding_path = root / "SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002/PR009_Audits/v002/PR009_SK_BINDING_MANIFEST_v002.json"
runtime_path = root / "Saved/Audits/PR009_InMap_v089/runtime_pie_audit.json"
build_path = root / "Saved/Audits/PR009_InMap_v089/release_collision_build.json"
out = root / "Saved/Audits/PR009_InMap_v089/collision_contract_sweep_audit.json"
binding = json.loads(binding_path.read_text(encoding="utf-8"))
runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
build = json.loads(build_path.read_text(encoding="utf-8"))
rows = {row["semantic"]: row for group in binding["groups"] for row in group["objects"] if row["semantic"] in {
    "moving_gantry_bridge","moving_cross_slide","moving_z_carriage","moving_lift_table",
    "moving_side_jogger","moving_end_jogger","moving_separator_picker"}}
all_rows = [row for group in binding["groups"] for row in group["objects"]]

CELL = {"x_m": [-2.60, 2.60], "y_m": [-3.80, 3.80], "z_m": [0.0, 3.30]}

def swept(name, translations):
    row = next(record for record in all_rows if record["object_name"] == name)
    center = row["source_world"]["location_m"]
    half = [value / 2000.0 for value in row["dimensions_mm"]]
    centers = [[center[i] + offset[i] for i in range(3)] for offset in translations]
    minimum = [min(value[i] - half[i] for value in centers) for i in range(3)]
    maximum = [max(value[i] + half[i] for value in centers) for i in range(3)]
    inside = (minimum[0] >= CELL["x_m"][0] and maximum[0] <= CELL["x_m"][1]
              and minimum[1] >= CELL["y_m"][0] and maximum[1] <= CELL["y_m"][1]
              and minimum[2] >= CELL["z_m"][0] and maximum[2] <= CELL["z_m"][1])
    return {"object": name, "semantic": row["semantic"], "source_contract": row["pivot"]["contract"],
            "swept_min_m": minimum, "swept_max_m": maximum, "inside_guarded_cell_envelope": inside}

sweeps = [
    # M02's 0..2800 mm is the total axis range inside the 3100 mm-long
    # module envelope, not an additional +2800 mm from the authored midpoint.
    # The source midpoint is local Y=-0.30 m, hence endpoint offsets +/-1.40 m.
    swept("PR009_M02_GantryBridge_01", [(0,-1.4,0),(0,1.4,0)]),
    swept("PR009_M03_GantryCrossSlide_01", [(-0.4,-1.4,0),(0.4,1.4,0)]),
    swept("PR009_M04_GantryZ_Carriage_01", [(-0.4,-1.4,0),(0.4,1.4,-1.3)]),
    swept("PR009_M05_LiftTable_01", [(0,0,0),(0,0,1.2)]),
    swept("PR009_M06_SideJogger_L", [(-0.3,0,0),(0.3,0,0)]),
    swept("PR009_M06_SideJogger_R", [(-0.3,0,0),(0.3,0,0)]),
    swept("PR009_M07_EndJogger_01", [(0,0,0),(0,0.35,0)]),
]
roller_rows = [row for row in all_rows if row["semantic"] in {"moving_roller","moving_output_roller"}]
roller_rotation_safe = all(row["dimensions_mm"][1] <= 181 and row["dimensions_mm"][2] <= 181 for row in roller_rows)
motion = runtime.get("motion_checks", {})
separator_runtime = {"object":"PR009_M08_SeparatorPicker_01","contract":"recipe",
                     "runtime_recipe_motion_proven":motion.get("separator") is True,
                     "runtime_max_location_delta_cm":runtime.get("motion_max_location_delta_cm",{}).get("separator"),
                     "runtime_max_rotation_delta_degrees":runtime.get("motion_max_rotation_delta_degrees",{}).get("separator")}

def aabb_from_row(row):
    center = row["source_world"]["location_m"]
    half = [value / 2000.0 for value in row["dimensions_mm"]]
    return {"min": [center[i]-half[i] for i in range(3)], "max": [center[i]+half[i] for i in range(3)]}

blockers = []
for group in build["static_groups"]:
    if "BLOCKALL" not in group["collision_profile"].upper():
        continue
    for primitive in group["primitives"]:
        cx, cy, cz = primitive["center_cm"]
        dx, dy, dz = primitive["dimensions_cm"]
        center = [cx/100.0, -cy/100.0, cz/100.0]
        half = [dx/200.0, dy/200.0, dz/200.0]
        blockers.append({"id": f"static:{group['group']}:{primitive['source']}", "role": group["group"],
                         "min": [center[i]-half[i] for i in range(3)], "max": [center[i]+half[i] for i in range(3)]})
for fixed in build["fixed_chassis_collision_actors"]:
    record = next(row for row in all_rows if row["object_name"].replace(".", "_") in fixed["actor"])
    box = aabb_from_row(record)
    blockers.append({"id": f"fixed:{record['object_name']}", "role": fixed["role"], **box})

mover_sweeps = [{"id": row["object"], "role": row["semantic"], "min": row["swept_min_m"], "max": row["swept_max_m"]} for row in sweeps]
for row in roller_rows:
    mover_sweeps.append({"id": row["object_name"], "role": row["semantic"], **aabb_from_row(row)})
runtime_separator_bounds = runtime.get("motion_world_swept_bounds_cm", {}).get("separator")
if runtime_separator_bounds:
    world_min, world_max = runtime_separator_bounds["min"], runtime_separator_bounds["max"]
    mover_sweeps.append({"id": "PR009_M08_SeparatorPicker_01", "role": "moving_separator_picker",
                         "min": [-(world_max[1]+2000.0)/100.0, (600.0-world_max[0])/100.0, world_min[2]/100.0],
                         "max": [-(world_min[1]+2000.0)/100.0, (600.0-world_min[0])/100.0, world_max[2]/100.0]})

def overlap(a, b, tolerance=0.001):
    depths = [min(a["max"][i], b["max"][i]) - max(a["min"][i], b["min"][i]) for i in range(3)]
    return depths, all(value > tolerance for value in depths)

def allowed_contact(mover, blocker):
    mid, bid = mover["id"], blocker["id"]
    if "GantryBridge" in mid and ("GantryColumn" in bid or blocker["role"] == "gantry_rail"):
        return "bridge-to-column/rail engineered support interface"
    if "LiftTable" in mid and blocker["role"] == "lift_pit_frame":
        return "lowered lift nested in pit support frame"
    if "InfeedRoll" in mid and blocker["role"] == "infeed_frame":
        return "roller bearing/support contact at frame rail"
    if "OutputRoll" in mid and blocker["role"] == "output_frame":
        return "roller bearing/support contact at output frame rail"
    if "OutputRoll" in mid and blocker["role"] == "drive_guard" and max(0.0, min(mover["max"][0], blocker["max"][0]) - max(mover["min"][0], blocker["min"][0])) <= 0.011:
        return "10 mm roller shaft/end intrusion into guarded drive interface"
    return None

allowed_contacts, unexpected_overlaps = [], []
for mover in mover_sweeps:
    for blocker in blockers:
        depths, intersects = overlap(mover, blocker)
        if not intersects:
            continue
        row = {"mover": mover["id"], "mover_role": mover["role"], "blocker": blocker["id"],
               "blocker_role": blocker["role"], "intersection_depth_m": depths}
        reason = allowed_contact(mover, blocker)
        if reason:
            row["allowed_reason"] = reason; allowed_contacts.append(row)
        else:
            unexpected_overlaps.append(row)
failures = []
if not all(row["inside_guarded_cell_envelope"] for row in sweeps): failures.append("one or more full contract sweeps leave guarded envelope")
if not roller_rotation_safe or not motion.get("infeed_rollers") or not motion.get("output_rollers"): failures.append("roller continuous-rotation envelope not proven")
if not separator_runtime["runtime_recipe_motion_proven"]: failures.append("separator recipe sweep not proven in PIE")
if not all(motion.get(key) for key in ("gantry_bridge","gantry_cross_slide","gantry_z","lift","side_jogger","end_jogger")): failures.append("native PIE motion proof incomplete")
if len(mover_sweeps) != 26: failures.append(f"expected 26 substantial mover sweep envelopes, found {len(mover_sweeps)}")
if unexpected_overlaps: failures.append(f"{len(unexpected_overlaps)} unapproved mover-vs-blocking-primitive overlaps")
payload = {"$schema":"cairnwell/audit/pr009-collision-contract-sweeps-v089/v1","generated_utc":datetime.now(timezone.utc).isoformat(),
           "status":"PASS__FULL_CONTRACT_AND_CONFIGURED_RECIPE_SWEEPS__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
           "guarded_cell_source_envelope":CELL,"linear_contract_sweeps":sweeps,
           "roller_count":len(roller_rows),"continuous_rotary_aabb_invariant":roller_rotation_safe,
           "separator_configured_recipe_sweep":separator_runtime,
           "blocking_primitive_count":len(blockers),"mover_sweep_count":len(mover_sweeps),
           "allowed_engineered_contacts":allowed_contacts,"unexpected_blocking_overlaps":unexpected_overlaps,
           "axis_authority": {"station_local_x":"across strip/lane","station_local_y":"material flow","gantry_range_interpretation":"2800 mm total travel centred on authored source midpoint"},
           "collision_semantics":"Selected movers are QueryOnly OverlapAllDynamic sensing envelopes; physical fixed/chassis collision is audited separately.",
           "failures":failures,"promotion_authorized":False}
out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,indent=2),encoding="utf-8")
print(json.dumps({"status":payload["status"],"output":str(out)},indent=2))
raise SystemExit(0 if not failures else 1)
