"""Independent file/contract audit for low-profile DockCouplingEvidence_v002."""

from pathlib import Path


base = Path(__file__).with_name("audit_press_train_dock_coupling_evidence_source_v001.py")
code = base.read_text(encoding="utf-8").replace("v001", "v002").replace("V001", "V002")
code = code.replace(
    '"CA_MW_ServiceGrey", "CA_MW_WorkedSteel", "CA_MW_DarkRubber",\n'
    '    "CA_MW_TrainAAccent", "CA_MW_StateGreen", "CA_MW_LabelWhite",',
    '"CA_MW_WorkedSteel", "CA_MW_DarkRubber",\n'
    '    "CA_MW_TrainAAccent", "CA_MW_StateGreen",',
)
exec(compile(code, str(base) + "::v002", "exec"), globals(), globals())
