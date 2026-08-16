"""Run the proven v089 PR-009 full-contract audit with the v095 enclosure as an added blocker set."""

from pathlib import Path


base = Path(__file__).with_name("audit_press_shop_pr009_collision_contract_sweeps_v089.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Saved/Audits/PR009_InMap_v089/runtime_pie_audit.json",
                    "Saved/Audits/PR009_InMap_v095/runtime_pie_audit.json")
code = code.replace("Saved/Audits/PR009_InMap_v089/collision_contract_sweep_audit.json",
                    "Saved/Audits/PR009_InMap_v095/collision_contract_sweep_audit.json")
code = code.replace("pr009-collision-contract-sweeps-v089", "pr009-collision-contract-sweeps-v095")

token = "mover_sweeps = [{\"id\": row[\"object\"], \"role\": row[\"semantic\"], \"min\": row[\"swept_min_m\"], \"max\": row[\"swept_max_m\"]} for row in sweeps]\n"
injection = """
# v095 shell boxes are authored in imported enclosure local space. PR-009 source
# local Y has the opposite sign, so the centres are converted before AABB tests.
shell_specs = [
    ((-240.0, 0.0, 177.5), (10.0, 550.0, 355.0), "north_wall"),
    ((240.0, -220.0, 177.5), (10.0, 110.0, 355.0), "south_wall_west"),
    ((240.0, 101.0, 177.5), (10.0, 348.0, 355.0), "south_wall_east"),
    ((0.0, 0.0, 350.0), (490.0, 550.0, 10.0), "roof"),
    ((0.0, -270.0, 285.0), (490.0, 10.0, 140.0), "portal_lintel_west"),
    ((0.0, 270.0, 285.0), (490.0, 10.0, 140.0), "portal_lintel_east"),
    ((-195.0, -270.0, 100.0), (100.0, 10.0, 200.0), "portal_cheek_west_north"),
    ((195.0, -270.0, 100.0), (100.0, 10.0, 200.0), "portal_cheek_west_south"),
    ((-195.0, 270.0, 100.0), (100.0, 10.0, 200.0), "portal_cheek_east_north"),
    ((195.0, 270.0, 100.0), (100.0, 10.0, 200.0), "portal_cheek_east_south"),
    ((231.5, -119.0, 170.0), (11.0, 92.0, 246.0), "service_door_closed"),
]
for center_cm, dimensions_cm, name in shell_specs:
    source_center = [center_cm[0] / 100.0, -center_cm[1] / 100.0, center_cm[2] / 100.0]
    half = [value / 200.0 for value in dimensions_cm]
    blockers.append({"id": "v095_enclosure:" + name, "role": "enclosure_shell",
                     "min": [source_center[i] - half[i] for i in range(3)],
                     "max": [source_center[i] + half[i] for i in range(3)]})

""" + token
if token not in code:
    raise RuntimeError("v095 enclosure-blocker injection token missing")
code = code.replace(token, injection, 1)
exec(compile(code, str(base) + "::v095-enclosure-release", "exec"), globals(), globals())
