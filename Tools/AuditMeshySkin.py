"""Read-only geometry audit for a supplied Meshy blend. Does not save input."""
import bpy
from mathutils import Vector
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
verts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
if verts:
 lo=Vector((min(v.x for v in verts),min(v.y for v in verts),min(v.z for v in verts)))
 hi=Vector((max(v.x for v in verts),max(v.y for v in verts),max(v.z for v in verts)))
 print('TOTAL|parts=%d|verts=%d|polys=%d|lo=%s|hi=%s|size=%s' % (len(meshes),sum(len(o.data.vertices) for o in meshes),sum(len(o.data.polygons) for o in meshes),tuple(round(v,4) for v in lo),tuple(round(v,4) for v in hi),tuple(round(v,4) for v in hi-lo)))
for o in meshes:
 print('PART|%s|verts=%d|polys=%d|dims=%s' % (o.name,len(o.data.vertices),len(o.data.polygons),tuple(round(v,4) for v in o.dimensions)))
print('INPUT_NOT_SAVED')
