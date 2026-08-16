"""Adapt the proven detailed importer to PR-008 Module 08 HPU candidate v071."""
from pathlib import Path

base = Path(__file__).with_name("import_build_press_shop_pr008_module06_candidate_v069.py")
code = base.read_text(encoding="utf-8")
replacements = (
    ('RECORDS = json.loads((SOURCE / "pr008_module06_shear_manifest_v001.json")',
     'RECORDS = json.loads((SOURCE / "pr008_module08_hpu_manifest_v001.json")'),
    ('BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module05Candidate_v068"',
     'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module07Candidate_v070"'),
    ('"LB_PR008_V062_06_CutToLengthShear"', '"LB_PR008_V062_08_HydraulicPowerUnit"'),
    ('"LB.Module.PR008.06.CutToLengthShear"', '"LB.Module.PR008.08.HydraulicPowerUnit"'),
    ('text("Brand", "CAIRNWELL / MOORCROSS", (-314.0, -2000.0, 222.0), 2.7',
     'text("Brand", "CAIRNWELL / MOORCROSS", (-139.0, -1795.0, 87.0), 2.7'),
    ('text("Station", "PR-008  CUT-TO-LENGTH SHEAR", (-314.0, -2000.0, 215.0), 2.8',
     'text("Station", "PR-008  HYDRAULIC POWER UNIT", (-139.0, -1795.0, 80.0), 2.8'),
    ('camera("Module06Inspection", (-660, -1490, 430), (-255, -2000, 125), 43)',
     'camera("Module08Inspection", (-500, -1370, 310), (-95, -1795, 95), 42)'),
    ('camera("Module06Drive", (-650, -2500, 390), (-255, -2000, 135), 47)',
     'camera("Module08Drive", (220, -1390, 300), (-95, -1795, 100), 46)'),
    ('camera("Module06Elevated", (-940, -1410, 700), (-255, -2000, 130), 53)',
     'camera("Module08Elevated", (-760, -1320, 590), (-95, -1795, 92), 52)'),
    ('camera("Module06Connected", (-1650, -3150, 850), (-500, -2000, 120), 59)',
     'camera("Module08Connected", (-1650, -3150, 850), (-390, -1950, 115), 59)'),
    ('expected_min, expected_max = [-315.0, -2142.5, -60.0], [-195.0, -1857.5, 240.0]',
     'expected_min, expected_max = [-140.0, -1850.0, 0.0], [-50.0, -1740.0, 185.0]'),
    ('"shear blade beam local Z down 0-180 mm at 300 mm/s top-safe"',
     '"static bunded HPU; duty/standby pumps, filtration, instrumentation and service isolation; no authored moving actor"'),
    ('PRO_MODULE06_DETAILED_IMPORT_BLADE_PIVOT_PROCESS_SAFETY_AND_ENVELOPE_CONTAINMENT_PASS',
     'PRO_MODULE08_DETAILED_IMPORT_BUND_PUMP_FILTRATION_INSTRUMENTATION_AND_ENVELOPE_CONTAINMENT_PASS'),
)
for old, new in replacements:
    if old not in code:
        raise RuntimeError(f"Module 08 adapter source contract missing: {old}")
    code = code.replace(old, new)

code = code.replace("Module 06", "Module 08").replace("Module06", "Module08").replace("module06", "module08")
code = code.replace("v069", "v071").replace("V069", "V071")
code = code.replace(
    'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module08Candidate_v071"',
    'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module07Candidate_v070"')
code = code.replace('"module_id": "06"', '"module_id": "08"')
exec(compile(code, str(base) + "::v071-adapter", "exec"), globals(), globals())
