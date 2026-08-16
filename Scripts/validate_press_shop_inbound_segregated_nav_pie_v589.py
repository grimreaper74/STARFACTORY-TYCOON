from pathlib import Path
code=Path(__file__).with_name("validate_press_shop_inbound_segregated_nav_pie_v588.py").read_text(encoding="utf-8")
code=code.replace("inbound_segregated_nav_pie_v588.json","inbound_segregated_nav_pie_v589.json").replace("v588/v1","v589/v1")
code=code.replace('((-8800,-2400,25),(-6200,-2800,25))','((-7400,-3000,25),(-6200,-2800,25))')
exec(compile(code,__file__+"::v589","exec"),globals(),globals())
