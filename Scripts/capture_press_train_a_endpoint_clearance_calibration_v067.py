"""Transiently hide the obsolete coarse endpoint cell to inspect the authored v067 flow kit."""

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
code = code.replace("press_train_a_v066_s01_high_calibration.png", "press_train_a_v067_s01_clear_calibration.png")
code = code.replace("press_train_a_v066_s07_high_calibration.png", "press_train_a_v067_s07_clear_calibration.png")
code = code.replace("LB_PRESS_TRAIN_A_ENDPOINT_CALIBRATION", "LB_PRESS_TRAIN_A_ENDPOINT_CLEARANCE_V067")
code = code.replace("press_train_a_v066_calibration", "press_train_a_v067_clearance_calibration")
code = code.replace("v066 transient", "v067 transient clearance")
needle = '''if camera is None:
    raise RuntimeError(calibration["camera"])
camera.set_actor_location'''
replacement = '''if camera is None:
    raise RuntimeError(calibration["camera"])
occluder_label = ("CA_MW_PTA_S01_DESTACK__LOAD" if capture_id == "s01_far"
                  else "CA_MW_PTA_S07_UNLOAD__INSPECT")
occluder = next((actor for actor in actors_api.get_all_level_actors()
                 if actor.get_actor_label() == occluder_label), None)
if occluder is None:
    raise RuntimeError(occluder_label)
occluder.set_actor_hidden_in_game(True)
component = getattr(occluder, "static_mesh_component", None)
if component is not None:
    component.set_visibility(False, True)
camera.set_actor_location'''
if needle not in code:
    raise RuntimeError("could not inject transient endpoint-occluder hide")
code = code.replace(needle, replacement)
exec(compile(code, str(base) + "::clearance-v067", "exec"), globals(), globals())
