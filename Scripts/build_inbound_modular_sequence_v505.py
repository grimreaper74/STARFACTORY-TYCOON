"""Build v505 from the reviewed v504 recipe with a side-on process camera."""
from pathlib import Path

source = (Path(__file__).parent / "build_inbound_modular_presentation_v504.py").read_text(encoding="utf-8")
source = source.replace(
    "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryPresentation_v504",
    "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliverySequence_v505",
)
source = source.replace("LB_INBOUND_V004_", "LB_INBOUND_V005_")
source = source.replace(
    "unreal.CameraActor, unreal.Vector(-1750, -2200, 1025), unreal.Rotator()",
    "unreal.CameraActor, unreal.Vector(-2450, 80, 1040), unreal.Rotator()",
)
source = source.replace(
    "camera.get_actor_location(), unreal.Vector(0, 300, 205)",
    "camera.get_actor_location(), unreal.Vector(0, 220, 215)",
)
source = source.replace(
    'camera.set_actor_label("LB_CAM_InboundCoilDelivery_Presentation_v504")',
    'camera.set_actor_label("LB_CAM_InboundCoilDelivery_Sequence_v505")',
)
source = source.replace(
    '{"field_of_view": 49.0,',
    '{"field_of_view": 52.0,',
)
source = source.replace(
    'unreal.log("LINE_BOSS_INBOUND_PRESENTATION_V504_BUILD_PASS")',
    'unreal.log("LINE_BOSS_INBOUND_SEQUENCE_V505_BUILD_PASS")',
)
exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())
