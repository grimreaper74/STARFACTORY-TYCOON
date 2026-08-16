"""Blender CLI: export accepted textured S03 to GLB, re-import, and render a round-trip visual gate."""
from pathlib import Path
from datetime import datetime, timezone
import bpy, json, math
from mathutils import Vector
ROOT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT=ROOT/r"SourceAssets\Candidate\PressTrains\TrainA\TexturedStationExport_v727";REVIEW=OUT/'Review';OUT.mkdir(parents=True,exist_ok=True);REVIEW.mkdir(parents=True,exist_ok=True)
GLB=OUT/'SM_CA_MW_PTA_S03_TexturedRoundTrip_v727.glb';AUDIT=OUT/'TEXTURED_STATION_EXPORT_AUDIT_v727.json'
if GLB.exists() or AUDIT.exists():raise RuntimeError('Refusing overwrite v727')
selected=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('SM_CA_MW_PTA_S03_')]
if len(selected)!=27:raise RuntimeError(f'Expected 27 S03 objects, found {len(selected)}')
def bounds(objs):
 pts=[o.matrix_world@Vector(c) for o in objs for c in o.bound_box];return Vector(tuple(min(p[i] for p in pts) for i in range(3))),Vector(tuple(max(p[i] for p in pts) for i in range(3)))
before_lo,before_hi=bounds(selected)
bpy.ops.object.select_all(action='DESELECT')
for o in selected:
 o.select_set(True);o.location.y-=15.0
 if o.data.users>1:o.data=o.data.copy()
 bpy.context.view_layer.objects.active=o
 for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
 tri=o.modifiers.new('LB_DeterministicTriangulate_v727','TRIANGULATE');bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=tri.name)
 if len(o.data.uv_layers)==0:raise RuntimeError(f'Missing UVs: {o.name}')
bpy.ops.export_scene.gltf(filepath=str(GLB),export_format='GLB',use_selection=True,export_materials='EXPORT',export_normals=True,export_tangents=True,export_apply=True)
source_tri=sum(len(p.vertices)-2 for o in selected for p in o.data.polygons)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(GLB))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];after_lo,after_hi=bounds(objects);round_tri=sum(len(p.vertices)-2 for o in objects for p in o.data.polygons)
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.look='AgX - Medium High Contrast'
world=scene.world or bpy.data.worlds.new('World');scene.world=world;world.use_nodes=True;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.012,.016,.02,1);bg.inputs['Strength'].default_value=.35
centre=(after_lo+after_hi)*.5;dims=after_hi-after_lo
def area(name,loc,energy,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.size=size;d.color=color;a=bpy.data.objects.new(name,d);scene.collection.objects.link(a);a.location=Vector(loc);a.rotation_euler=(centre-a.location).to_track_quat('-Z','Y').to_euler()
area('Key',centre+Vector((-10,-9,13)),2600,10,(1,.9,.76));area('Fill',centre+Vector((10,-4,9)),1900,9,(.72,.84,1));area('Rim',centre+Vector((0,8,12)),2200,9,(.78,1,.82))
def render(name,loc):
 d=bpy.data.cameras.new(name);c=bpy.data.objects.new(name,d);scene.collection.objects.link(c);scene.camera=c;d.lens=55;c.location=Vector(loc);c.rotation_euler=(centre-c.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(REVIEW/name);bpy.ops.render.render(write_still=True);bpy.data.objects.remove(c,do_unlink=True)
render('S03_textured_roundtrip_hero_v727.png',centre+Vector((-14,-13,9)));render('S03_textured_roundtrip_front_v727.png',centre+Vector((-16,0,1.2)));render('S03_textured_roundtrip_service_v727.png',centre+Vector((14,7,7)))
delta=[abs((before_hi-before_lo)[i]-(after_hi-after_lo)[i]) for i in range(3)]
AUDIT.write_text(json.dumps({'revision':'v727','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__TEXTURED_GLTF_ROUNDTRIP__UNREAL_IMPORT_NOT_STARTED__VISUAL_REVIEW_REQUIRED','source_object_count':len(selected),'roundtrip_object_count':len(objects),'source_triangle_count':source_tri,'roundtrip_triangle_count':round_tri,'source_dimensions_m':list(before_hi-before_lo),'roundtrip_dimensions_m':list(after_hi-after_lo),'dimension_delta_m':delta,'material_count':len(bpy.data.materials),'image_count':len(bpy.data.images),'glb':str(GLB),'renders':[str(p) for p in sorted(REVIEW.glob('*.png'))]},indent=2),encoding='utf-8')
print('LINE_BOSS_PTA_S03_TEXTURED_ROUNDTRIP_V727_PASS')
