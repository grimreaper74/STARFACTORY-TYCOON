from pathlib import Path
source=Path(__file__).with_name("validate_complete_train_a_runtime_pie_v675.py").read_text(encoding="utf-8")
source=source.replace('save.persistent_train_guid.is_valid()', 'str(save.persistent_train_guid) not in ("", "00000000-0000-0000-0000-000000000000")')
source=source.replace("v675","v676").replace("V675","V676")
exec(compile(source,str(Path(__file__).with_name("validate_complete_train_a_runtime_pie_v675.py")),"exec"),globals(),globals())
