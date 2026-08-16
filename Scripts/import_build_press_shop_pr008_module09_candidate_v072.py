"""Adapt the proven detailed importer to PR-008 Module 09 cabinet candidate v072."""
from pathlib import Path

base = Path(__file__).with_name("import_build_press_shop_pr008_module06_candidate_v069.py")
code = base.read_text(encoding="utf-8")
replacements = (
    ('RECORDS = json.loads((SOURCE / "pr008_module06_shear_manifest_v001.json")',
     'RECORDS = json.loads((SOURCE / "pr008_module09_cabinets_manifest_v001.json")'),
    ('BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module05Candidate_v068"',
     'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module08Candidate_v071"'),
    ('"LB_PR008_V062_06_CutToLengthShear"', '"LB_PR008_V062_09_ElectricalDriveCabinets"'),
    ('"LB.Module.PR008.06.CutToLengthShear"', '"LB.Module.PR008.09.ElectricalDriveCabinets"'),
    ('text("Brand", "CAIRNWELL / MOORCROSS", (-314.0, -2000.0, 222.0), 2.7',
     'text("Brand", "CAIRNWELL / MOORCROSS", (-124.5, -2218.0, 184.0), 2.7'),
    ('text("Station", "PR-008  CUT-TO-LENGTH SHEAR", (-314.0, -2000.0, 215.0), 2.8',
     'text("Station", "PR-008  ELECTRICAL / DRIVES", (-124.5, -2218.0, 177.0), 2.8'),
    ('camera("Module06Inspection", (-660, -1490, 430), (-255, -2000, 125), 43)',
     'camera("Module09Inspection", (-360, -2620, 285), (-95, -2205, 110), 42)'),
    ('camera("Module06Drive", (-650, -2500, 390), (-255, -2000, 135), 47)',
     'camera("Module09RearService", (230, -2500, 280), (-95, -2205, 110), 45)'),
    ('camera("Module06Elevated", (-940, -1410, 700), (-255, -2000, 130), 53)',
     'camera("Module09Elevated", (-520, -2720, 560), (-95, -2205, 110), 52)'),
    ('camera("Module06Connected", (-1650, -3150, 850), (-500, -2000, 120), 59)',
     'camera("Module09Connected", (-1650, -3150, 850), (-390, -2000, 115), 59)'),
    ('expected_min, expected_max = [-315.0, -2142.5, -60.0], [-195.0, -1857.5, 240.0]',
     'expected_min, expected_max = [-127.5, -2267.5, 0.0], [-62.5, -2142.5, 220.0]'),
    ('"shear blade beam local Z down 0-180 mm at 300 mm/s top-safe"',
     '"static three-section incoming-power, servo-drive and controls/UPS cabinet bank; no authored moving actor"'),
    ('PRO_MODULE06_DETAILED_IMPORT_BLADE_PIVOT_PROCESS_SAFETY_AND_ENVELOPE_CONTAINMENT_PASS',
     'PRO_MODULE09_DETAILED_IMPORT_SECTIONS_COOLING_REAR_ENTRY_SENSORS_AND_ENVELOPE_CONTAINMENT_PASS'),
)
for old, new in replacements:
    if old not in code:
        raise RuntimeError(f"Module 09 adapter source contract missing: {old}")
    code = code.replace(old, new)

# Module 09 uses a distinct light-grey electrical-enclosure coating.  Create it
# once in the shared detailed-material namespace and bind its authored slot
# explicitly instead of silently falling back to foundry charcoal.
material_setup_anchor = "materials = {\n"
if material_setup_anchor not in code:
    raise RuntimeError("Module 09 adapter could not locate shared material setup")
lightgrey_setup = '''lightgrey_path = f"{MAT}/M_CA_MW_PR008_LightGrey_v001"\nlightgrey = library.load_asset(lightgrey_path)\nif lightgrey is None:\n    lightgrey = tools.create_asset("M_CA_MW_PR008_LightGrey_v001", MAT, unreal.Material, unreal.MaterialFactoryNew())\n    editing = unreal.MaterialEditingLibrary\n    base_colour = editing.create_material_expression(lightgrey, unreal.MaterialExpressionConstant3Vector, -340, -70)\n    base_colour.set_editor_property("constant", unreal.LinearColor(0.474, 0.515, 0.553, 1.0))\n    metal = editing.create_material_expression(lightgrey, unreal.MaterialExpressionConstant, -340, 45)\n    metal.set_editor_property("r", 0.34)\n    rough = editing.create_material_expression(lightgrey, unreal.MaterialExpressionConstant, -340, 150)\n    rough.set_editor_property("r", 0.46)\n    editing.connect_material_property(base_colour, "", unreal.MaterialProperty.MP_BASE_COLOR)\n    editing.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)\n    editing.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)\n    editing.recompile_material(lightgrey)\n    library.save_loaded_asset(lightgrey, only_if_is_dirty=False)\n\n\n'''
code = code.replace(material_setup_anchor, lightgrey_setup + material_setup_anchor, 1)
choose_anchor = '    if "driveblue" in value: return materials["blue"]\n'
if choose_anchor not in code:
    raise RuntimeError("Module 09 adapter could not locate material chooser")
code = code.replace(choose_anchor, choose_anchor + '    if "lightgrey" in value: return lightgrey\n', 1)

code = code.replace("Module 06", "Module 09").replace("Module06", "Module09").replace("module06", "module09")
code = code.replace("v069", "v072").replace("V069", "V072")
code = code.replace(
    'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module09Candidate_v072"',
    'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module08Candidate_v071"')
code = code.replace('"module_id": "06"', '"module_id": "09"')
exec(compile(code, str(base) + "::v072-adapter", "exec"), globals(), globals())
