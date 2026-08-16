"""Corrected v197 build; v196 stopped on a Vector indexing validator error."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_pr005_runtime_cage_infill_candidate_v196.py")
code = source.read_text(encoding="utf-8")
code = code.replace("Candidate_v196", "Candidate_v197")
code = code.replace("candidate_v196", "candidate_v197")
code = code.replace("V196", "V197")
code = code.replace("v196", "v197")
code = code.replace(
    'return all((a_min[i] < b_max[i] and a_max[i] > b_min[i]) for i in range(3))',
    'return (a_min.x < b_max.x and a_max.x > b_min.x and a_min.y < b_max.y and a_max.y > b_min.y and a_min.z < b_max.z and a_max.z > b_min.z)',
)
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})

