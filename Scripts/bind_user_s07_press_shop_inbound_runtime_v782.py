"""Bind the proven inbound runtime chain onto clean user-S07 map v780."""
from pathlib import Path
root=Path(__file__).parent
code=(root/'bind_clean_press_shop_inbound_runtime_v772.py').read_text(encoding='utf-8')
code=code.replace('/Game/LineBoss/Maps/LB_PressShop_Trains_InboundVisual_v770','/Game/LineBoss/Maps/LB_PressShop_Trains_Inbound_UserS07_v780')
code=code.replace('/Game/LineBoss/Maps/LB_PressShop_Trains_InboundRuntime_v772','/Game/LineBoss/Maps/LB_PressShop_Trains_Inbound_UserS07_Runtime_v782')
code=code.replace('clean_press_shop_inbound_runtime_v772.json','user_s07_press_shop_inbound_runtime_v782.json')
code=code.replace('v772','v782').replace('V772','V782')
code=code.replace('LB_PressShop_Trains_InboundRuntime_v782.umap','LB_PressShop_Trains_Inbound_UserS07_Runtime_v782.umap')
exec(compile(code,str(root/'bind_clean_press_shop_inbound_runtime_v772.py')+'::user_s07_v782','exec'),globals(),globals())
