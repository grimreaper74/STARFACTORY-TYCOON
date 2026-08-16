"""Adapt the proven v260 PIE readiness audit to the clean south v019 fleet bank."""
from pathlib import Path
source=Path(__file__).with_name('audit_press_shop_support_fleet_dispatch_readiness_v260.py')
code=source.read_text(encoding='utf-8')
code=code.replace('/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v260','/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetNav_v20260809_v019')
code=code.replace('press_shop_support_fleet_dispatch_readiness_v260.json','clean_support_fleet_dispatch_readiness_v20260809_v019.json')
old='''BERTHS = {
    "LB-MR01-01": (-6495.0, 5160.0, 62.5),
    "LB-MR01-02": (-5095.0, 5160.0, 62.5),
    "LB-CR01-01": (-1495.0, 5160.0, 56.0),
    "LB-CR01-02": (-295.0, 5160.0, 56.0),
}'''
new='''BERTHS = {
    "LB-CR01-01": (-750.0, -4050.0, 56.0),
    "LB-CR01-02": (-250.0, -4050.0, 56.0),
    "LB-MR01-01": (250.0, -4050.0, 67.2875),
    "LB-MR01-02": (750.0, -4050.0, 67.2875),
}'''
if old not in code:raise RuntimeError('berth patch source changed')
code=code.replace(old,new)
code=code.replace('apron = (x, y - 170.0, 25.0)','apron = (x, y + 170.0, 25.0)')
code=code.replace('aisle = (x, 4200.0, 25.0)','aisle = (x, -3650.0, 25.0)')
code=code.replace('cross_aisle = (-3300.0, 4200.0, 25.0)','cross_aisle = (0.0, -3650.0, 25.0)')
exec(compile(code,str(source)+'::clean-v019','exec'),globals(),globals())
