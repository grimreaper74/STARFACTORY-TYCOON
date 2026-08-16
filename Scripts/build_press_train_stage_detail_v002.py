"""Build v002 stage detail with controls facing the verified CCTV side."""

from pathlib import Path


base = Path(__file__).with_name("build_press_train_stage_detail_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("StageDetail_v001", "StageDetail_v002")
code = code.replace("stage-detail-v001", "stage-detail-v002")
code = code.replace("_v001", "_v002")
code = code.replace("STAGE_DETAIL_V001", "STAGE_DETAIL_V002")
code = code.replace(
    'box(parts, "HMIHousing", (760, 260, 560), (2600, -350, 1840), "CA_MW_ServiceGrey", 35)',
    'box(parts, "HMIHousing", (260, 760, 560), (2980, 0, 1840), "CA_MW_ServiceGrey", 35)',
)
code = code.replace(
    'box(parts, "HMIScreen", (560, 35, 350), (2600, -498, 1870), "CA_MW_HMIScreen", 12)',
    'box(parts, "HMIScreen", (35, 560, 350), (3128, 0, 1870), "CA_MW_HMIScreen", 12)',
)
code = code.replace(
    'box(parts, "StageIDPlate", (610, 28, 150), (2600, -515, 2220), "CA_MW_TrainAAccent", 10)',
    'box(parts, "StageIDPlate", (28, 610, 150), (3132, 0, 2220), "CA_MW_TrainAAccent", 10)',
)
code = code.replace(
    'cylinder(parts, "EStop", 125, 95, (2600, -500, 1560), "CA_MW_EStopRed", axis="Y", vertices=28)',
    'cylinder(parts, "EStop", 125, 95, (3135, -260, 1560), "CA_MW_EStopRed", axis="X", vertices=28)',
)
code = code.replace(
    'box(parts, "VisionScreen", (610, 28, 390), (2450, 305, 1680), "CA_MW_HMIScreen", 12)',
    'box(parts, "VisionScreen", (28, 610, 390), (2892, 700, 1680), "CA_MW_HMIScreen", 12)',
)
exec(compile(code, str(base) + "::stage_detail_v002", "exec"), globals(), globals())
