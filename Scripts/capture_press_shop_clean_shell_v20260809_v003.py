from pathlib import Path
source=Path(__file__).with_name("capture_press_shop_clean_shell_v20260809_v001.py")
code=source.read_text(encoding="utf-8").replace("LB_PressShop_CleanShell_v20260809_v001","LB_PressShop_CleanShell_v20260809_v003").replace("clean_shell_v20260809_v001","clean_shell_v20260809_v003").replace("clean_shell_capture_v20260809_v001","clean_shell_capture_v20260809_v003").replace("CAPTURE_V001_","CAPTURE_V003_")
exec(compile(code,str(source),"exec"),globals(),globals())
