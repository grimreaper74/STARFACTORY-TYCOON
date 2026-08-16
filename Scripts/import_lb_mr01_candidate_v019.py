"""Run the strict isolated Unreal importer for MR01 Candidate v019."""

from pathlib import Path

root = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
base = root / "Scripts/import_lb_mr01_candidate_v017.py"
code = base.read_text(encoding="utf-8")
for old, new in (("v017", "v019"), ("V017", "V019")):
    code = code.replace(old, new)
code = code.replace("LB_MR01_RaisedArmCandidate_v019", "LB_MR01_UnrealArmCandidate_v019")
exec(compile(code, str(base) + "::v019-strict-ten-bone-import", "exec"), globals(), globals())
