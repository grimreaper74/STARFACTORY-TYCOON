"""Render matching front, side, rear and elevated maintenance-robot views."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
label=args[0] if args else Path(bpy.data.filepath).stem
out=Path(r'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\ValidationScreenshots\SourceAssets\MaintenanceRobotComparison_v953'); out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene; scene.render.engine='BLENDER_EEVEE'; scene.render.resolution_x=1400; scene.render.resolution_y=1400; scene.render.resolution_percentage=100; scene.render.image_settings.file_format='PNG'
if scene.world is None: scene.world=bpy.data.worlds.new('MaintenanceReviewWorld')
scene.world.color=(.02,.02,.02)
meshes=[o for o in scene.objects if o.type=='MESH' and not o.hide_render]; pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]; lo=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts))); hi=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts))); center=(lo+hi)*.5; size=hi-lo; span=max(size)
def aim(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=max(15,span*3),location=(center.x,center.y,lo.z-.01)); floor=bpy.context.object; fm=bpy.data.materials.new('MaintenanceReviewFloor'); fm.diffuse_color=(.12,.13,.14,1); fm.roughness=.8; floor.data.materials.append(fm)
for name,d,e in [('Key',Vector((-1,-1,1.2)),2200),('Fill',Vector((1,-.4,.8)),1400),('Rim',Vector((.2,1,1.1)),1800)]:
 ld=bpy.data.lights.new(name,'AREA'); ld.energy=e; ld.size=max(2,span*.8); l=bpy.data.objects.new(name,ld); scene.collection.objects.link(l); l.location=center+d.normalized()*span*2; aim(l,center)
cd=bpy.data.cameras.new('MaintenanceReviewCamera'); cam=bpy.data.objects.new('MaintenanceReviewCamera',cd); scene.collection.objects.link(cam); cd.type='ORTHO'; cd.ortho_scale=span*1.32; scene.camera=cam
for n,d in {'front':Vector((0,-1,.12)),'side':Vector((1,0,.12)),'rear':Vector((0,1,.12)),'elevated':Vector((1,-1,.75))}.items():
 cam.location=center+d.normalized()*span*3; aim(cam,center); scene.render.filepath=str(out/f'{label}_{n}.png'); bpy.ops.render.render(write_still=True)
print('LINE_BOSS_MAINTENANCE_ROBOT_RENDER_V953',label,list(size),len(meshes),out)
