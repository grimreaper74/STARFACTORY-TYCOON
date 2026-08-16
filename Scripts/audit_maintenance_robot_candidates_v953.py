"""Audit a maintenance-robot Blender candidate and emit labelled JSON."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
label=args[0] if args else Path(bpy.data.filepath).stem
out=Path(r'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressShopRobots')/f'maintenance_robot_{label}_v953.json'; out.parent.mkdir(parents=True,exist_ok=True)
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]; lo=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts))); hi=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
images=[]
for i in bpy.data.images:
    if i.name=='Render Result':continue
    images.append({'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file),'size':list(i.size)})
rows=[{'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'dimensions':[round(v,6) for v in o.dimensions],'materials':[m.name if m else None for m in o.data.materials]} for o in meshes]
payload={'label':label,'source':bpy.data.filepath,'mesh_count':len(meshes),'envelope_m':[round(v,6) for v in hi-lo],'polygon_count':sum(len(o.data.polygons) for o in meshes),'materials':sorted({m.name for o in meshes for m in o.data.materials if m}),'images':images,'objects':rows}
out.write_text(json.dumps(payload,indent=2),encoding='utf-8'); print('LINE_BOSS_MAINTENANCE_ROBOT_AUDIT_V953',label,len(meshes),list(hi-lo))
