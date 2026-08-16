from pathlib import Path
src=Path(__file__).with_name('capture_cleaning_robot_unreal_close_v945.py').read_text(encoding='utf-8')
src=src.replace("cleaning_robot_unreal_close.png","s01_unreal_close.png").replace("LB.Capture.Cleaner.v945","LB.Capture.S01.v945").replace("unreal.Vector(470,-920,260)","unreal.Vector(720,-720,440)").replace("unreal.Vector(0,-470,65)","unreal.Vector(0,160,155)").replace("LINE_BOSS_CLEANER_UNREAL_CLOSE_V945","LINE_BOSS_S01_UNREAL_CLOSE_V945")
exec(compile(src,__file__,'exec'))
