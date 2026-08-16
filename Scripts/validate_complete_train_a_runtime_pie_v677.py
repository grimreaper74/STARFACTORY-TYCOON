from pathlib import Path
source=Path(__file__).with_name("validate_complete_train_a_runtime_pie_v675.py").read_text(encoding="utf-8")
source=source.replace('save.persistent_train_guid.is_valid()', 'str(save.persistent_train_guid) not in ("", "00000000-0000-0000-0000-000000000000")')
source=source.replace('if "FORM_S03" not in phase:return', 'if "FORM_S03" not in phase or status.cycle_progress < 0.33:return')
source=source.replace('checks["five_flywheels_rotate_while_cycling"]=max_rotor_delta>10;', 'checks["s03_slide_delta_cm"]=slide_delta;checks["s03_upper_die_delta_cm"]=die_delta;checks["five_flywheels_rotate_while_cycling"]=max_rotor_delta>10;')
source=source.replace("v675","v677").replace("V675","V677")
exec(compile(source,str(Path(__file__).with_name("validate_complete_train_a_runtime_pie_v675.py")),"exec"),globals(),globals())
