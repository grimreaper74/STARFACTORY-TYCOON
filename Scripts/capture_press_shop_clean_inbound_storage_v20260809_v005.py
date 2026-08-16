from pathlib import Path
code=(Path(__file__).parent/'capture_press_shop_clean_inbound_storage_v20260809_v004.py').read_text(encoding='utf-8')
code=code.replace('/Game/LineBoss/Maps/LB_PressShop_CleanInboundStorage_v20260809_v004','/Game/LineBoss/Maps/LB_PressShop_CleanInboundStorageFit_v20260809_v005')
code=code.replace('clean_inbound_storage_v20260809_v004','clean_inbound_storage_v20260809_v005')
code=code.replace('CLEAN_INBOUND_STORAGE_CAPTURE_V004','CLEAN_INBOUND_STORAGE_CAPTURE_V005')
exec(compile(code,'capture_press_shop_clean_inbound_storage_v20260809_v005_generated.py','exec'))
