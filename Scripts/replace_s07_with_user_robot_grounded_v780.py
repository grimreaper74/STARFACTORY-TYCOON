"""Fresh grounded successor of the rejected below-floor v779 attempt."""
from pathlib import Path
root=Path(__file__).parent
code=(root/'replace_s07_with_user_robot_v779.py').read_text(encoding='utf-8')
code=code.replace('v779','v780').replace('V779','V780')
code=code.replace("unreal.Vector(8600,y+420,0)","unreal.Vector(8600,y+420,130)")
code=code.replace("'z':0}","'z':130}")
exec(compile(code,str(root/'replace_s07_with_user_robot_v779.py')+'::grounded_v780','exec'),globals(),globals())
