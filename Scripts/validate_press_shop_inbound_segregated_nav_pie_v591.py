from pathlib import Path
code=Path(__file__).with_name("validate_press_shop_inbound_segregated_nav_pie_v588.py").read_text(encoding="utf-8")
code=code.replace("inbound_segregated_nav_pie_v588.json","inbound_segregated_nav_pie_v591.json").replace("v588/v1","v591/v1")
code=code.replace('route(world,(-8800,-2400,25),(-6200,-2800,25))','route(world,(-7100,-3200,25),(-6200,-2800,25))')
exec(compile(code,__file__+"::v591","exec"),globals(),globals())
