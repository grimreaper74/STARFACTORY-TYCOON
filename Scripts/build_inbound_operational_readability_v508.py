"""Build isolated v508 operational-readability review from v004 assets."""
from pathlib import Path
import unreal

source = (Path(__file__).parent / "build_inbound_modular_presentation_v504.py").read_text(encoding="utf-8")
source = source.replace(
    "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryPresentation_v504",
    "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryOperationalReadability_v508",
)
source = source.replace(
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v003",
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v004",
)
source = source.replace("SM_CA_MW_MOD_{name}_v003", "SM_CA_MW_MOD_{name}_v004")
source = source.replace("LB_INBOUND_V004_", "LB_INBOUND_V008_")
source = source.replace('mod("CraneBayStructure", (0, 700, 320))', 'mod("CraneBayStructure", (0, 740, 320))')
source = source.replace('mod("ReceivingSaddle", (0, 700, 47))', 'mod("ReceivingSaddle", (0, 740, 70))')
source = source.replace('mod("IdentityScanner", (240, 700, 93))', 'mod("IdentityScanner", (260, 740, 93))')
source = source.replace('mod("AGVHandoffGuides", (420, 850, 18))', 'mod("AGVHandoffGuides", (650, 410, 37))')
source = source.replace('(420, 850, 45)', '(650, 410, 45)')
source = source.replace('(420, 850, 83)', '(650, 410, 83)')
source = source.replace('(0, 700, 610)', '(0, 740, 610)')
source = source.replace('(0, 500, 625)', '(0, 540, 625)')
source = source.replace('(0, 500, 500)', '(0, 540, 500)')
source = source.replace('(0, 500, 315)', '(0, 540, 315)')
source = source.replace(
    "for crane_actor in (girder, trolley, hoist, hook):\n    for index in range(crane_actor.static_mesh_component.get_num_materials()):\n        crane_actor.static_mesh_component.set_material(index, yellow)\n",
    "# Preserve the retained crane assets' authored material separation.\n",
)
source = source.replace(
    "unreal.CameraActor, unreal.Vector(-1750, -2200, 1025), unreal.Rotator()",
    "unreal.CameraActor, unreal.Vector(-2050, -2300, 1160), unreal.Rotator()",
)
source = source.replace(
    "camera.get_actor_location(), unreal.Vector(0, 300, 205)",
    "camera.get_actor_location(), unreal.Vector(85, 260, 190)",
)
source = source.replace(
    'camera.set_actor_label("LB_CAM_InboundCoilDelivery_Presentation_v504")',
    'camera.set_actor_label("LB_CAM_InboundCoilDelivery_OperationalReadability_v508")',
)
source = source.replace('{"field_of_view": 49.0,', '{"field_of_view": 53.0,')
source = source.replace(
    'unreal.log("LINE_BOSS_INBOUND_PRESENTATION_V504_BUILD_PASS")',
    'unreal.log("LINE_BOSS_INBOUND_OPERATIONAL_READABILITY_V508_BASE_PASS")',
)
exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())

# Make the purpose of the handoff vehicle explicit with the retained Press Shop coil.
loaded_coil = add(
    "LB_INBOUND_V008_AGV_LoadedCoil",
    "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005",
    (650, 410, 185),
    rot=(0, 0, 0),
    tags=("LB.Material.Coil", "LB.Vehicle.CoilAGV.Payload"),
)
loaded_coil.tags.append(unreal.Name("LB.State.ValidationLoaded"))
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v508 after loaded Coil AGV")
unreal.log("LINE_BOSS_INBOUND_OPERATIONAL_READABILITY_V508_BUILD_PASS")
