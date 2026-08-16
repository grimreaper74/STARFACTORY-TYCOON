"""Run the isolated Unreal importer for ten-bone MR01 Candidate v018."""

from pathlib import Path

root = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
base = root / "Scripts/import_lb_mr01_candidate_v017.py"
code = base.read_text(encoding="utf-8")
for old, new in (("v017", "v018"), ("V017", "V018")):
    code = code.replace(old, new)
code = code.replace("LB_MR01_RaisedArmCandidate_v018", "LB_MR01_UnrealArmCandidate_v018")
exec(compile(code, str(base) + "::v018-ten-bone-import", "exec"), globals(), globals())
