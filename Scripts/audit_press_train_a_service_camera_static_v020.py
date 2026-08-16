"""v020 exact-map static audit adapter with four fixed cameras."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_installed_service_static_v017.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAInstalledServiceCandidate_v017", "LB_PressTrainAServiceCameraCandidate_v020")
code = code.replace("press_train_a_installed_service_static_v017.json", "press_train_a_service_camera_static_v020.json")
code = code.replace("installed-service-static-v017", "service-camera-static-v020")
code = code.replace("PRESS_TRAIN_A_V017", "PRESS_TRAIN_A_V020")
code = code.replace("LB.Asset.Candidate.v017", "LB.Asset.Candidate.v020")
code = code.replace("v017 candidate tag", "v020 candidate tag")
code = code.replace('"cameras": (len(cameras), 3)', '"cameras": (len(cameras), 4)')
exec(compile(code, str(base) + "::v020", "exec"), globals(), globals())
