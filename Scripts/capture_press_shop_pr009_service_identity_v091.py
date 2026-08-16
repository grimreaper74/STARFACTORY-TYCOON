"""Capture v091 from the retained south-west service camera."""
from pathlib import Path
base = Path(__file__).with_name("capture_press_shop_pr009_service_camera_v090.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressShop_PR009ServiceCameraCandidate_v090", "LB_PressShop_PR009ServiceIdentityCandidate_v091")
code = code.replace("LB_PR009_V090_PRESENT_CAM_ServiceHero", "LB_PR009_V091_PRESENT_CAM_ServiceHero")
code = code.replace("v090_pr009_service_camera/press_shop_v090_pr009_service_camera_hero.png", "v091_pr009_service_identity/press_shop_v091_pr009_service_identity_hero.png")
code = code.replace("v090 south-west service-camera", "v091 south-facing identity")
code = code.replace("PR009_V090_SERVICE_CAMERA_CAPTURE", "PR009_V091_SERVICE_IDENTITY_CAPTURE")
exec(compile(code, str(base) + "::v091-service-identity-capture", "exec"), globals(), globals())
