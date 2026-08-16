"""Build v192 directly from retained v190 with stronger broad architectural fill."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_pr003_pr004_whole_hall_readability_candidate_v191.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v191", "v192").replace("V191", "V192")
code = code.replace("(0.095, 0.108, 0.118)", "(0.155, 0.170, 0.182)")
code = code.replace("(0.155, 0.165, 0.172)", "(0.205, 0.215, 0.222)")
code = code.replace("(0.115, 0.132, 0.145)", "(0.165, 0.182, 0.195)")
code = code.replace('"intensity": 9.5,', '"intensity": 18.0,')
code = code.replace('"intensity": 8.0,', '"intensity": 24.0,')
code = code.replace('"attenuation_radius": 1450.0,', '"attenuation_radius": 1850.0,')
code = code.replace(
    'add_camera("LB_ENV_V192_CAM_PR003PR004Management", (-10300.0, 1450.0, 720.0), (-5900.0, -2850.0, 470.0), 62.0)',
    'add_camera("LB_ENV_V192_CAM_PR003PR004Management", (-9950.0, 700.0, 760.0), (-6000.0, -2850.0, 470.0), 58.0)')
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
