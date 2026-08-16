"""Build corrected visual successor v257 directly from technical checkpoint v255."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_support_fleet_visual_candidate_v256.py")
code = source.read_text(encoding="utf-8").replace("v256", "v257").replace("V256", "V257")
code = code.replace('"location": (-5800.0, 3500.0, 330.0)', '"location": (-5800.0, 3650.0, 280.0)')
code = code.replace('"location": (-900.0, 3500.0, 320.0)', '"location": (-900.0, 3650.0, 270.0)')
code = code.replace('"location": (-3300.0, 1000.0, 2500.0)', '"location": (-3300.0, 1000.0, 1000.0)')
code = code.replace('"target": (-3300.0, 5000.0, 30.0)', '"target": (-3300.0, 5000.0, 70.0)')
code = code.replace('"fov": 82.0', '"fov": 78.0')
code = code.replace('"auto_exposure_bias": 0.35', '"auto_exposure_bias": -0.30')
code = code.replace('"intensity": 1200.0', '"intensity": 450.0')
code = code.replace('"task_light_intensity": 1200.0', '"task_light_intensity": 450.0')
code = code.replace('"camera_exposure_bias": 0.35', '"camera_exposure_bias": -0.30')
exec(compile(code, str(source) + "::v257-corrected-visual-direct-v255", "exec"), globals(), globals())
