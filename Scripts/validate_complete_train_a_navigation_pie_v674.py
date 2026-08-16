from pathlib import Path
source=Path(__file__).with_name("validate_complete_train_a_navigation_pie_v664.py").read_text(encoding="utf-8")
source=source.replace("RuntimeNav_v663","RuntimeNav_v673").replace("v664","v674").replace("V664","V674")
exec(compile(source,str(Path(__file__).with_name("validate_complete_train_a_navigation_pie_v664.py")),"exec"),globals(),globals())
