"""Build a reusable 40 m visual transfer-truss module in Blender.

Presentation/game asset only. Span, member sizes and structural capacity are
unverified TBC and must not be treated as engineering documentation.
"""
import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/Candidate/PressShop/Structure/WideSpanTruss_v372"
BLEND = OUT / "CA_MW_PressShop_WideSpanTruss_v372.blend"
FBX = OUT / "FBX/SM_CA_MW_PressShop_WideSpanTruss_40m_TBC_v372.fbx"
if BLEND.exists() or FBX.exists():
    raise RuntimeError("Refusing to overwrite v372 truss source")
FBX.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

mat = bpy.data.materials.new("CA_MW_StructuralSteel_DarkGrey_TBC")
mat.diffuse_color = (0.055, 0.07, 0.075, 1.0)


def beam(name, a, b, width=0.18, depth=0.18):
    a, b = Vector(a), Vector(b); delta = b - a; length = delta.length
    bpy.ops.mesh.primitive_cube_add(location=(a + b) * 0.5)
    obj = bpy.context.object; obj.name = name
    obj.dimensions = (width, depth, length)
    obj.rotation_mode = 'QUATERNION'; obj.rotation_quaternion = delta.to_track_quat('Z', 'Y')
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


parts=[]
# Twin-plane top/bottom chords along the 40 m X span.
for side_y in (-0.25, 0.25):
    parts += [beam(f"ChordBottom_{side_y:+.2f}", (-20,side_y,-0.5),(20,side_y,-0.5),0.22,0.22),
              beam(f"ChordTop_{side_y:+.2f}", (-20,side_y,0.5),(20,side_y,0.5),0.22,0.22)]
    # Ten 4 m panels, alternating diagonals plus verticals.
    for i in range(11):
        x=-20+i*4
        parts.append(beam(f"Vertical_{side_y:+.2f}_{i:02d}",(x,side_y,-0.5),(x,side_y,0.5),0.14,0.14))
    for i in range(10):
        x0=-20+i*4; x1=x0+4
        za,zb=(-0.5,0.5) if i%2==0 else (0.5,-0.5)
        parts.append(beam(f"Diagonal_{side_y:+.2f}_{i:02d}",(x0,side_y,za),(x1,side_y,zb),0.13,0.13))
# Cross ties make the two truss planes read as one fabricated girder.
for i in range(11):
    x=-20+i*4
    parts += [beam(f"TieTop_{i:02d}",(x,-0.25,0.5),(x,0.25,0.5),0.12,0.12),
              beam(f"TieBottom_{i:02d}",(x,-0.25,-0.5),(x,0.25,-0.5),0.12,0.12)]

bpy.ops.object.select_all(action='DESELECT')
for obj in parts: obj.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
bpy.ops.object.join(); truss=bpy.context.object; truss.name="SM_CA_MW_PressShop_WideSpanTruss_40m_TBC_v372"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
truss["engineering_status"]="TBC_PRESENTATION_ONLY"
truss["nominal_span_m"] = 40.0
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
bpy.ops.export_scene.fbx(filepath=str(FBX),use_selection=True,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',
                         axis_forward='-Y',axis_up='Z',bake_space_transform=False,add_leaf_bones=False,path_mode='AUTO')
print(f"BLEND={BLEND}\nFBX={FBX}\nPARTS_JOINED={len(parts)}")
