"""Adapt the proven Module 06 importer to detailed PR-008 Module 07 candidate v070."""
from pathlib import Path

base = Path(__file__).with_name("import_build_press_shop_pr008_module06_candidate_v069.py")
code = base.read_text(encoding="utf-8")
replacements = (
    ('RECORDS = json.loads((SOURCE / "pr008_module06_shear_manifest_v001.json")',
     'RECORDS = json.loads((SOURCE / "pr008_module07_discharge_manifest_v001.json")'),
    ('BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module05Candidate_v068"',
     'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module06Candidate_v069"'),
    ('"LB_PR008_V062_06_CutToLengthShear"', '"LB_PR008_V062_07_DischargeRollers"'),
    ('"LB.Module.PR008.06.CutToLengthShear"', '"LB.Module.PR008.07.DischargeRollers"'),
    ('text("Brand", "CAIRNWELL / MOORCROSS", (-314.0, -2000.0, 222.0), 2.7',
     'text("Brand", "CAIRNWELL / MOORCROSS", (-122.0, -1868.0, 136.0), 2.7'),
    ('text("Station", "PR-008  CUT-TO-LENGTH SHEAR", (-314.0, -2000.0, 215.0), 2.8',
     'text("Station", "PR-008  DISCHARGE ROLLERS", (-122.0, -1868.0, 129.0), 2.8'),
    ('unreal.Rotator(yaw=180)', 'unreal.Rotator(yaw=90)'),
    ('camera("Module06Inspection", (-660, -1490, 430), (-255, -2000, 125), 43)',
     'camera("Module07Inspection", (-470, -1480, 330), (-105, -2000, 100), 43)'),
    ('camera("Module06Drive", (-650, -2500, 390), (-255, -2000, 135), 47)',
     'camera("Module07Drive", (-450, -2500, 310), (-105, -2000, 100), 47)'),
    ('camera("Module06Elevated", (-940, -1410, 700), (-255, -2000, 130), 53)',
     'camera("Module07Elevated", (-720, -1410, 570), (-105, -2000, 95), 53)'),
    ('camera("Module06Connected", (-1650, -3150, 850), (-500, -2000, 120), 59)',
     'camera("Module07Connected", (-1650, -3150, 850), (-430, -2000, 115), 59)'),
    ('expected_min, expected_max = [-315.0, -2142.5, -60.0], [-195.0, -1857.5, 240.0]',
     'expected_min, expected_max = [-192.5, -2132.5, 30.0], [-17.5, -1867.5, 150.0]'),
    ('"shear blade beam local Z down 0-180 mm at 300 mm/s top-safe"',
     '"seven discharge rollers local-X rotary continuous at 0-60 m/min stop/brake-safe"'),
    ('PRO_MODULE06_DETAILED_IMPORT_BLADE_PIVOT_PROCESS_SAFETY_AND_ENVELOPE_CONTAINMENT_PASS',
     'PRO_MODULE07_DETAILED_IMPORT_ROLLER_PIVOTS_HANDOFF_SAFETY_AND_ENVELOPE_CONTAINMENT_PASS'),
)
for old, new in replacements:
    if old not in code:
        raise RuntimeError(f"Module 07 adapter source contract missing: {old}")
    code = code.replace(old, new)

code = code.replace("Module 06", "Module 07").replace("Module06", "Module07").replace("module06", "module07")
code = code.replace("v069", "v070").replace("V069", "V070")
code = code.replace(
    'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module07Candidate_v070"',
    'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module06Candidate_v069"')
code = code.replace('"module_id": "06"', '"module_id": "07"')
exec(compile(code, str(base) + "::v070-adapter", "exec"), globals(), globals())
