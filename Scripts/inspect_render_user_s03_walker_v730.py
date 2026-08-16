"""Blender CLI: non-destructive inspection/render of Greg's supplied S03 Walker GLB."""
from pathlib import Path
from datetime import datetime,timezone
import bpy,json
from mathutils import Vector
SRC=Path(r"C:\Users\greg_\Downloads\Meshy_AI_Cairnwell_S03_Walker_0808080548_texture (1).glb")
ROOT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT=ROOT/r"Saved\ValidationScreenshots\PressTrains\UserS03Walker_v730";OUT.mkdir(parents=True,exist_ok=True)
AUDIT=ROOT/r"Saved\Audits\PressTrains\user_s03_walker_blender_inspection_v730.json"
if not SRC.exists():raise RuntimeError(f'Missing user GLB: {SRC}')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(SRC))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
if not objects:raise RuntimeError('User GLB has no mesh objects')
def bounds(objs):
 pts=[o.matrix_world@Vector(c) for o in objs for c in o.bound_box];return Vector(tuple(min(p[i] for p in pts) for i in range(3))),Vector(tuple(max(p[i] for p in pts) for i in range(3)))
lo,hi=bounds(objects);centre=(lo+hi)*.5;dims=hi-lo
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.look='AgX - Medium High Contrast'
world=scene.world or bpy.data.worlds.new('World');scene.world=world;world.use_nodes=True;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.012,.016,.02,1);bg.inputs['Strength'].default_value=.35
def area(name,loc,energy,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.size=size;d.color=color;a=bpy.data.objects.new(name,d);scene.collection.objects.link(a);a.location=Vector(loc);a.rotation_euler=(centre-a.location).to_track_quat('-Z','Y').to_euler()
r=max(dims);area('Key',centre+Vector((-r,-r,r*1.4)),2600,r,(1,.9,.76));area('Fill',centre+Vector((r,-r*.4,r)),2000,r,(.72,.84,1));area('Rim',centre+Vector((0,r,r*1.3)),2200,r,(.78,1,.84))
def render(name,loc):
 d=bpy.data.cameras.new(name);c=bpy.data.objects.new(name,d);scene.collection.objects.link(c);scene.camera=c;d.lens=58;c.location=Vector(loc);c.rotation_euler=(centre-c.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True);bpy.data.objects.remove(c,do_unlink=True)
render('UserS03Walker_hero_v730.png',centre+Vector((-r*1.25,-r*1.35,r*.85)));render('UserS03Walker_front_v730.png',centre+Vector((0,-r*1.9,r*.12)));render('UserS03Walker_side_v730.png',centre+Vector((r*1.9,0,r*.12)))
tris=sum(len(p.vertices)-2 for o in objects for p in o.data.polygons);materials=sorted({m.name for o in objects for m in o.data.materials if m})
AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps({'revision':'v730','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'USER_SUPPLIED_SOURCE__FRESH_BLENDER_RENDERS__VISUAL_REVIEW_REQUIRED','source':str(SRC),'source_bytes':SRC.stat().st_size,'mesh_object_count':len(objects),'vertex_count':sum(len(o.data.vertices) for o in objects),'triangle_count':tris,'dimensions_source_units':list(dims),'material_count':len(materials),'materials':materials,'image_count':len(bpy.data.images),'renders':[str(p) for p in sorted(OUT.glob('*.png'))],'source_modified':False},indent=2),encoding='utf-8')
print('LINE_BOSS_USER_S03_WALKER_V730_PASS')
