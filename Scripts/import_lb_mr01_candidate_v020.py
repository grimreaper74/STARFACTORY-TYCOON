"""Run the strict isolated Unreal importer for MR01 Candidate v020."""

from pathlib import Path

root = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
base = root / "Scripts/import_lb_mr01_candidate_v017.py"
code = base.read_text(encoding="utf-8")
for old, new in (("v017", "v020"), ("V017", "V020")):
    code = code.replace(old, new)
code = code.replace("LB_MR01_RaisedArmCandidate_v020", "LB_MR01_ConnectedLiftCandidate_v020")
exec(compile(code, str(base) + "::v020-connected-lift-import", "exec"), globals(), globals())
