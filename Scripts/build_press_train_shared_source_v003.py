"""Build corrected CCTV-side open-bay shared press-train source v003.

The Unreal flow-axis correction uses 180 degrees yaw, so source +X becomes the
negative-X fixed-camera side.  This version moves the open process facade to +X
and the closed die-change/service facade to -X before that assembly rotation.
"""

from pathlib import Path

base = Path(__file__).with_name("build_press_train_shared_source_v002.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Presentation_v002", "Presentation_v003")
code = code.replace("_v002", "_v003")
code = code.replace("SOURCE_V002", "SOURCE_V003")
code = code.replace("camera_x = -half_x + 130", "camera_x = half_x - 130")
code = code.replace("(-half_x + 660, 0, 1280)", "(half_x - 660, 0, 1280)")
code = code.replace("(-half_x + 115, 0, 2350)", "(half_x - 115, 0, 2350)")
code = code.replace("(-half_x + 115, 0, 1870)", "(half_x - 115, 0, 1870)")
code = code.replace("(-half_x + 115, 0, 1420)", "(half_x - 115, 0, 1420)")
code = code.replace("(-half_x + 115, rail_y, 1800)", "(half_x - 115, rail_y, 1800)")
code = code.replace("(-half_x + 130, -half_y + 1250, 2700)", "(half_x - 130, -half_y + 1250, 2700)")
code = code.replace("(-half_x + 80, -half_y + 1250, 2820)", "(half_x - 80, -half_y + 1250, 2820)")
code = code.replace("(-half_x + 80, -half_y + 1250, 2420)", "(half_x - 80, -half_y + 1250, 2420)")
code = code.replace("service_x = half_x - 130", "service_x = -half_x + 130")
code = code.replace("(half_x - 145, -900, 1450)", "(-half_x + 145, -900, 1450)")
code = code.replace("(half_x - 19, -900, 1850)", "(-half_x + 19, -900, 1850)")
code = code.replace("(half_x - 55, -900, 2580)", "(-half_x + 55, -900, 2580)")
exec(compile(code, str(base) + "::presentation_v003", "exec"), globals(), globals())
