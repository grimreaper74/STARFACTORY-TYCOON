"""Build v002 with a quieter, more integrated shared crown face."""

from pathlib import Path

base = Path(__file__).with_name("build_press_train_crown_endpoint_presentation_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("CrownEndpointPresentation_v001", "CrownEndpointPresentation_v002")
code = code.replace("CROWN_ENDPOINT_PRESENTATION_MANIFEST_v001", "CROWN_ENDPOINT_PRESENTATION_MANIFEST_v002")
code = code.replace("CrownEndpointPresentation_v001.blend", "CrownEndpointPresentation_v002.blend")
code = code.replace("crown-endpoint-presentation-v001", "crown-endpoint-presentation-v002")
code = code.replace("CROWN_ENDPOINT_PRESENTATION_V001", "CROWN_ENDPOINT_PRESENTATION_V002")
code = code.replace("_v001", "_v002")
code = code.replace(
    'box(parts, "OperatorDrivePlinth", (520, 2600, 1220), (2670, 0, 40), "CA_MW_CairnwellGreen", 55)',
    'box(parts, "OperatorDrivePlinth", (420, 2200, 900), (2640, 0, 30), "CA_MW_CairnwellGreen", 48)',
)
code = code.replace(
    'cylinder(parts, "OperatorFlywheelGuard", 1120, 420, (2930, -720, 120), "CA_MW_ServiceGrey", axis="X", vertices=32)',
    'cylinder(parts, "OperatorFlywheelGuard", 620, 280, (2890, -620, 80), "CA_MW_ServiceGrey", axis="X", vertices=28)',
)
code = code.replace(
    'box(parts, "OperatorVentBank", (210, 1050, 620), (2980, 720, 20), "CA_MW_FoundryCharcoal", 22)',
    'box(parts, "OperatorVentBank", (150, 900, 480), (2885, 580, 20), "CA_MW_FoundryCharcoal", 18)',
)
code = code.replace(
    'box(parts, f"DriveVent_{y}", (105, 160, 460), (3100, y, 20), "CA_MW_WorkedSteel", 6)',
    'box(parts, f"DriveVent_{y}", (85, 125, 330), (2980, y - 140, 20), "CA_MW_WorkedSteel", 5)',
)
exec(compile(code, str(base) + "::v002", "exec"), globals(), globals())
