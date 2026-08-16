"""Read-only audit of one split Meshy source; appends no data and saves nothing.

The caller collects stdout into the industrial-detail library intake report.
"""
import bpy
from mathutils import Vector
meshes=sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:o.name)
allv=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
if allv:
 lo=Vector((min(v.x for v in allv),min(v.y for v in allv),min(v.z for v in allv)))
 hi=Vector((max(v.x for v in allv),max(v.y for v in allv),max(v.z for v in allv)))
 print('SUMMARY|%d|%d|%d|%.5f|%.5f|%.5f' % (len(meshes),sum(len(o.data.vertices) for o in meshes),sum(len(o.data.polygons) for o in meshes),*(hi-lo)))
for i,o in enumerate(meshes):
 print('PART|%d|%s|%d|%d|%.5f|%.5f|%.5f' % (i,o.name,len(o.data.vertices),len(o.data.polygons),*o.dimensions))
print('INPUT_NOT_SAVED')
