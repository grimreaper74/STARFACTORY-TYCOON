"""Transiently calibrate farther elevated endpoint CCTV views on preserved v067."""

from pathlib import Path


base = Path(__file__).with_name("capture_press_train_a_endpoint_camera_calibration_v066.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v066", "Candidate_v067")
code = code.replace("CA_MW_PTA_CAM_S01DieSideFlow_v066", "CA_MW_PTA_CAM_S01FeedFlowCorrected_v067")
code = code.replace("CA_MW_PTA_CAM_S07DieSideFlow_v066", "CA_MW_PTA_CAM_S07DischargeFlowCorrected_v067")
code = code.replace('"s01_high"', '"s01_far"')
code = code.replace('"s07_high"', '"s07_far"')
code = code.replace("unreal.Vector(850.0, -720.0, 650.0)", "unreal.Vector(600.0, -1100.0, 850.0)")
code = code.replace("unreal.Vector(0.0, -120.0, 105.0)", "unreal.Vector(0.0, -250.0, 120.0)")
code = code.replace("unreal.Vector(900.0, 5450.0, 700.0)", "unreal.Vector(650.0, 6100.0, 900.0)")
code = code.replace("unreal.Vector(0.0, 4850.0, 120.0)", "unreal.Vector(0.0, 5000.0, 160.0)")
code = code.replace("press_train_a_v066_s01_high_calibration.png", "press_train_a_v067_s01_far_calibration.png")
code = code.replace("press_train_a_v066_s07_high_calibration.png", "press_train_a_v067_s07_far_calibration.png")
code = code.replace("LB_PRESS_TRAIN_A_ENDPOINT_CALIBRATION", "LB_PRESS_TRAIN_A_ENDPOINT_CALIBRATION_V067")
code = code.replace("press_train_a_v066_calibration", "press_train_a_v067_calibration")
code = code.replace("v066 transient", "v067 transient")
exec(compile(code, str(base) + "::v067", "exec"), globals(), globals())
