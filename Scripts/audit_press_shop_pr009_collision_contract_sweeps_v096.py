"""Adapt the proven v095 full-contract sweep to the corrected v096 audit data."""
from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_pr009_collision_contract_sweeps_v095.py")
code = source.read_text(encoding="utf-8").replace(
    "PR009_InMap_v095", "PR009_InMap_v096").replace(
    "V095", "V096").replace("v095", "v096")
token = 'exec(compile(code, str(base) + "::v096-enclosure-release", "exec"), globals(), globals())'
injection = (
    'code = code.replace("(600.0-world_max[0])/100.0", "(world_min[0]-600.0)/100.0")'
    '.replace("(600.0-world_min[0])/100.0", "(world_max[0]-600.0)/100.0")\n'
    'code = code.replace("if len(mover_sweeps) != 26: failures.append(f\\"expected 26 substantial mover sweep envelopes, found {len(mover_sweeps)}\\")", "configured_mover_contract_count = 26\\nif len(mover_sweeps) < configured_mover_contract_count: failures.append(f\\"expected at least {configured_mover_contract_count} substantial mover sweep envelopes, found {len(mover_sweeps)}\\")")\n'
    'sample_token = "def overlap(a, b, tolerance=0.001):\\n"\n'
    'sample_injection = "mover_sweeps = [row for row in mover_sweeps if row[\\\"id\\\"] != \\\"PR009_M08_SeparatorPicker_01\\\"]\\nfor sample_index, sample in enumerate(runtime.get(\\\"motion_world_sample_bounds_cm\\\", {}).get(\\\"separator\\\", [])):\\n    world_min, world_max = sample[\\\"min\\\"], sample[\\\"max\\\"]\\n    mover_sweeps.append({\\\"id\\\": f\\\"PR009_M08_SeparatorPicker_01@{sample_index:04d}\\\", \\\"role\\\": \\\"moving_separator_picker\\\", \\\"min\\\": [-(world_max[1]+2000.0)/100.0, (world_min[0]-600.0)/100.0, world_min[2]/100.0], \\\"max\\\": [-(world_min[1]+2000.0)/100.0, (world_max[0]-600.0)/100.0, world_max[2]/100.0]})\\n\\n" + sample_token\n'
    'if sample_token not in code: raise RuntimeError("v096 separator sample-sweep token missing")\n'
    'code = code.replace(sample_token, sample_injection, 1)\n' + token
)
if token not in code:
    raise RuntimeError("v096 authoritative inverse-axis injection token missing")
code = code.replace(token, injection, 1)
exec(compile(code, str(source) + "::v096-flow-axis", "exec"), globals(), globals())
