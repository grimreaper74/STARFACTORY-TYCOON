"""Blender CLI: inspect/render rejected static S03 Front-O and assess separability for moving parts."""
from pathlib import Path
from datetime import datetime,timezone
import bpy,bmesh,json,hashlib
from mathutils import Vector
SRC=Path(r"C:\Users\greg_\Downloads\Meshy_AI_Cairnwell_S03_Front_O_0808162709_texture.glb")
ROOT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT=ROOT/r"Saved\ValidationScreenshots\PressTrains\UserS03FrontO_v732";OUT.mkdir(parents=True,exist_ok=True)
AUDIT=ROOT/r"Saved\Audits\PressTrains\user_s03_front_o_blender_inspection_v732.json"
if not SRC.exists():raise RuntimeError(f'Missing user GLB: {SRC}')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(SRC))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
if not objects:raise RuntimeError('No meshes')
pts=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box];lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)));centre=(lo+hi)*.5;dims=hi-lo
# Connected-component counts without altering the model.
islands=[]
for o in objects:
 bm=bmesh.new();bm.from_mesh(o.data);remaining=set(bm.verts)
 while remaining:
  seed=remaining.pop();stack=[seed];count=0;ilo=Vector((1e30,1e30,1e30));ihi=Vector((-1e30,-1e30,-1e30))
  while stack:
   v=stack.pop();count+=1;co=o.matrix_world@v.co;ilo.x=min(ilo.x,co.x);ilo.y=min(ilo.y,co.y);ilo.z=min(ilo.z,co.z);ihi.x=max(ihi.x,co.x);ihi.y=max(ihi.y,co.y);ihi.z=max(ihi.z,co.z)
   for e in v.link_edges:
    n=e.other_vert(v)
    if n in remaining:remaining.remove(n);stack.append(n)
  islands.append({'vertices':count,'min':list(ilo),'max':list(ihi),'dimensions':list(ihi-ilo)})
 bm.free()
islands.sort(key=lambda x:x['vertices'],reverse=True)
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.look='AgX - Medium High Contrast'
world=scene.world or bpy.data.worlds.new('World');scene.world=world;world.use_nodes=True;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.012,.016,.02,1);bg.inputs['Strength'].default_value=.35
def area(name,loc,energy,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.size=size;d.color=color;a=bpy.data.objects.new(name,d);scene.collection.objects.link(a);a.location=Vector(loc);a.rotation_euler=(centre-a.location).to_track_quat('-Z','Y').to_euler()
r=max(dims);area('Key',centre+Vector((-r,-r,r*1.4)),2600,r,(1,.9,.76));area('Fill',centre+Vector((r,-r*.4,r)),2000,r,(.72,.84,1));area('Rim',centre+Vector((0,r,r*1.3)),2200,r,(.78,1,.84))
def render(name,loc):
 d=bpy.data.cameras.new(name);c=bpy.data.objects.new(name,d);scene.collection.objects.link(c);scene.camera=c;d.lens=58;c.location=Vector(loc);c.rotation_euler=(centre-c.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True);bpy.data.objects.remove(c,do_unlink=True)
render('UserS03FrontO_hero_v732.png',centre+Vector((-r*1.25,-r*1.35,r*.85)));render('UserS03FrontO_front_v732.png',centre+Vector((0,-r*1.9,r*.12)));render('UserS03FrontO_side_v732.png',centre+Vector((r*1.9,0,r*.12)))
tris=sum(len(p.vertices)-2 for o in objects for p in o.data.polygons);large=[i for i in islands if i['vertices']>=1000]
AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps({'revision':'v732','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'USER_REJECTED_NO_MOVING_PARTS__BLENDER_SEPARABILITY_ASSESSMENT','source':str(SRC),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest().upper(),'source_bytes':SRC.stat().st_size,'mesh_object_count':len(objects),'vertex_count':sum(len(o.data.vertices) for o in objects),'triangle_count':tris,'dimensions_source_units':list(dims),'material_count':len({m.name for o in objects for m in o.data.materials if m}),'connected_island_count':len(islands),'large_island_count_ge_1000_vertices':len(large),'largest_islands':islands[:30],'candidate_strategy':'SEPARATE_LOOSE_ISLANDS_THEN_CLASSIFY' if len(large)>1 else 'RETAIN_STATIC_SHELL_AND_REBUILD_MOVERS_AS_SEPARATE_RIGID_MODULES','renders':[str(p) for p in sorted(OUT.glob('*.png'))],'source_modified':False},indent=2),encoding='utf-8')
print('LINE_BOSS_USER_S03_FRONT_O_V732_PASS')
