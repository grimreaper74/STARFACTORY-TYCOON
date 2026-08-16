"""Capture the isolated v093 lower service-camera experiment."""

from pathlib import Path


base = Path(__file__).with_name("capture_press_shop_pr009_service_camera_v090.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressShop_PR009ServiceCameraCandidate_v090", "LB_PressShop_PR009ServiceCameraRefinementCandidate_v093")
code = code.replace("LB_PR009_V090_PRESENT_CAM_ServiceHero", "LB_PR009_V093_PRESENT_CAM_ServiceHero")
code = code.replace(
    "v090_pr009_service_camera/press_shop_v090_pr009_service_camera_hero.png",
    "v093_pr009_service_camera_refinement/press_shop_v093_pr009_service_camera_refinement_hero.png")
code = code.replace("v090 south-west service-camera", "v093 lower south-west service-camera")
code = code.replace("PR009_V090_SERVICE_CAMERA_CAPTURE", "PR009_V093_SERVICE_CAMERA_REFINEMENT_CAPTURE")
exec(compile(code, str(base) + "::v093-service-camera-refinement-capture", "exec"), globals(), globals())
