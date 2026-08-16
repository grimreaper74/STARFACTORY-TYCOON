"""Adapt the proven detailed importer to PR-008 Module 10 compact-HMI candidate v073."""
from pathlib import Path

base = Path(__file__).with_name("import_build_press_shop_pr008_module06_candidate_v069.py")
code = base.read_text(encoding="utf-8")
replacements = (
    ('RECORDS = json.loads((SOURCE / "pr008_module06_shear_manifest_v001.json")',
     'RECORDS = json.loads((SOURCE / "pr008_module10_hmi_manifest_v001.json")'),
    ('BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module05Candidate_v068"',
     'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module09Candidate_v072"'),
    ('"LB_PR008_V062_06_CutToLengthShear"', '"LB_PR008_V062_10_CompactHMI"'),
    ('"LB.Module.PR008.06.CutToLengthShear"', '"LB.Module.PR008.10.CompactHMI"'),
    ('text("Brand", "CAIRNWELL / MOORCROSS", (-314.0, -2000.0, 222.0), 2.7',
     'text("Brand", "CAIRNWELL / MOORCROSS", (-185.0, -2281.2, 109.0), 2.7'),
    ('text("Station", "PR-008  CUT-TO-LENGTH SHEAR", (-314.0, -2000.0, 215.0), 2.8',
     'text("Station", "PR-008  SERVO BLANKING HMI", (-185.0, -2281.2, 102.0), 2.8'),
    ('camera("Module06Inspection", (-660, -1490, 430), (-255, -2000, 125), 43)',
     'camera("Module10Operator", (-185, -2650, 220), (-185, -2252, 112), 42)'),
    ('camera("Module06Drive", (-650, -2500, 390), (-255, -2000, 135), 47)',
     'camera("Module10Inspection", (-520, -2550, 300), (-185, -2252, 112), 45)'),
    ('camera("Module06Elevated", (-940, -1410, 700), (-255, -2000, 130), 53)',
     'camera("Module10Elevated", (-520, -2720, 520), (-185, -2252, 108), 52)'),
    ('camera("Module06Connected", (-1650, -3150, 850), (-500, -2000, 120), 59)',
     'camera("Module10Connected", (-1650, -3150, 850), (-390, -2000, 115), 59)'),
    ('expected_min, expected_max = [-315.0, -2142.5, -60.0], [-195.0, -1857.5, 240.0]',
     'expected_min, expected_max = [-208.0, -2282.0, 46.0], [-162.0, -2222.0, 174.0]'),
    ('"shear blade beam local Z down 0-180 mm at 300 mm/s top-safe"',
     '"static compact 15-17 inch operator HMI with separate touch, local controls and outward E-stop interaction surfaces"'),
    ('PRO_MODULE06_DETAILED_IMPORT_BLADE_PIVOT_PROCESS_SAFETY_AND_ENVELOPE_CONTAINMENT_PASS',
     'PRO_MODULE10_DETAILED_IMPORT_TOUCH_CONTROLS_ESTOP_SERVICES_AND_ENVELOPE_CONTAINMENT_PASS'),
)
for old, new in replacements:
    if old not in code:
        raise RuntimeError(f"Module 10 adapter source contract missing: {old}")
    code = code.replace(old, new)

material_setup_anchor = "materials = {\n"
if material_setup_anchor not in code:
    raise RuntimeError("Module 10 adapter could not locate shared material setup")
lightgrey_setup = '''lightgrey_path = f"{MAT}/M_CA_MW_PR008_LightGrey_v001"\nlightgrey = library.load_asset(lightgrey_path)\nif lightgrey is None:\n    raise RuntimeError("Module 10 requires the retained Module 09 light-grey cabinet material")\n\n\n'''
code = code.replace(material_setup_anchor, lightgrey_setup + material_setup_anchor, 1)
choose_anchor = '    if "driveblue" in value: return materials["blue"]\n'
if choose_anchor not in code:
    raise RuntimeError("Module 10 adapter could not locate material chooser")
code = code.replace(choose_anchor, choose_anchor + '    if "lightgrey" in value: return lightgrey\n', 1)

# TextRender faces local +X by default. Module 10's operator face is local +X,
# transformed to world -Y by the authoritative -90-degree station yaw.
code = code.replace('unreal.Rotator(yaw=180)', 'unreal.Rotator(yaw=-90)')
code = code.replace("Module 06", "Module 10").replace("Module06", "Module10").replace("module06", "module10")
code = code.replace("v069", "v073").replace("V069", "V073")
code = code.replace(
    'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module10Candidate_v073"',
    'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module09Candidate_v072"')
code = code.replace('"module_id": "06"', '"module_id": "10"')
exec(compile(code, str(base) + "::v073-adapter", "exec"), globals(), globals())
