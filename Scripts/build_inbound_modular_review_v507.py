"""Build isolated combined Unreal review for Modular_v004."""
from pathlib import Path

source = (Path(__file__).parent / "build_inbound_modular_presentation_v504.py").read_text(encoding="utf-8")
source = source.replace(
    "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryPresentation_v504",
    "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryReview_v507",
)
source = source.replace(
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v003",
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v004",
)
source = source.replace("SM_CA_MW_MOD_{name}_v003", "SM_CA_MW_MOD_{name}_v004")
source = source.replace("LB_INBOUND_V004_", "LB_INBOUND_V007_")
source = source.replace('mod("CraneBayStructure", (0, 700, 320))', 'mod("CraneBayStructure", (0, 740, 320))')
source = source.replace('mod("ReceivingSaddle", (0, 700, 47))', 'mod("ReceivingSaddle", (0, 740, 70))')
source = source.replace('mod("IdentityScanner", (240, 700, 93))', 'mod("IdentityScanner", (260, 740, 93))')
source = source.replace('mod("AGVHandoffGuides", (420, 850, 18))', 'mod("AGVHandoffGuides", (570, 820, 37))')
source = source.replace('(420, 850, 45)', '(570, 820, 45)')
source = source.replace('(420, 850, 83)', '(570, 820, 83)')
source = source.replace('(0, 700, 610)', '(0, 740, 610)')
source = source.replace('(0, 500, 625)', '(0, 540, 625)')
source = source.replace('(0, 500, 500)', '(0, 540, 500)')
source = source.replace('(0, 500, 315)', '(0, 540, 315)')
source = source.replace(
    "unreal.CameraActor, unreal.Vector(-1750, -2200, 1025), unreal.Rotator()",
    "unreal.CameraActor, unreal.Vector(-2150, -2380, 1240), unreal.Rotator()",
)
source = source.replace(
    "camera.get_actor_location(), unreal.Vector(0, 300, 205)",
    "camera.get_actor_location(), unreal.Vector(70, 310, 205)",
)
source = source.replace(
    'camera.set_actor_label("LB_CAM_InboundCoilDelivery_Presentation_v504")',
    'camera.set_actor_label("LB_CAM_InboundCoilDelivery_Review_v507")',
)
source = source.replace('{"field_of_view": 49.0,', '{"field_of_view": 55.0,')
source = source.replace(
    'unreal.log("LINE_BOSS_INBOUND_PRESENTATION_V504_BUILD_PASS")',
    'unreal.log("LINE_BOSS_INBOUND_REVIEW_V507_BUILD_PASS")',
)
exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())
