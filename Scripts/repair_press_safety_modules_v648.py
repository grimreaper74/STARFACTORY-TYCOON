"""Create clean zero-credit safety modules from accepted v646 proportions.

The Meshy fence and gate contained flattened reference-sheet artefacts, while the
right access-door generation changed semantic class.  Rebuild only the simple
structural safety meshes and mirror the accepted left door; raw outputs remain
untouched as failure evidence.
"""
import bpy
import json
from pathlib import Path

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SRC_DOOR = ROOT / r"SourceAssets\Candidate\PressTrains\Shared\MeshyIsolatedIntake_v625\Generated\Meshy6_v646\04_LeftAccessDoor\Cleaned_v647\SM_CA_MW_PT_04_LeftAccessDoor_LOD0_v639.glb"
OUT = ROOT / r"SourceAssets\Candidate\PressTrains\Shared\MeshyIsolatedIntake_v625\Generated\Meshy6_v646\Repaired_v648"
OUT.mkdir(parents=True, exist_ok=True)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def cube(name, location, scale, bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new("EdgeSoftening", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return obj

def join_export(asset, objects, metadata):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    master = bpy.context.object
    master.name = asset
    master["lineboss_source_status"] = "ZERO_CREDIT_REPAIR_NOT_PROMOTED"
    master["lineboss_scale_status"] = "TBC_PENDING_S03_ASSEMBLY"
    master["lineboss_collision_status"] = "NOT_AUTHORED"
    blend = OUT / f"{asset}_Master_v648.blend"
    glb = OUT / f"{asset}_LOD0_v648.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", use_selection=True)
    metadata.update({"asset": asset, "blend": str(blend), "glb": str(glb),
                     "polygons": len(master.data.polygons), "status": "SOURCE_ONLY_NOT_PROMOTED"})
    return metadata

def build_panel(asset, gate=False):
    reset()
    width, height = (1.62, 1.90) if gate else (1.90, 1.83)
    depth = 0.075
    objs = []
    post = 0.065
    rail = 0.045
    objs += [cube(asset+"_PostL", (-width/2, 0, height/2), (post, depth, height/2)),
             cube(asset+"_PostR", ( width/2, 0, height/2), (post, depth, height/2)),
             cube(asset+"_RailTop", (0, 0, height-rail), (width/2, depth, rail)),
             cube(asset+"_RailBottom", (0, 0, rail), (width/2, depth, rail))]
    # Deliberately regular welded mesh: no flattened input-image lettering.
    spacing_x, spacing_z = 0.105, 0.105
    x = -width/2 + 0.15
    while x < width/2 - 0.14:
        objs.append(cube(asset+"_WireV", (x, 0, height/2), (0.008, 0.018, height/2-0.08), 0.004))
        x += spacing_x
    z = 0.13
    while z < height - 0.12:
        objs.append(cube(asset+"_WireH", (0, 0, z), (width/2-0.08, 0.018, 0.008), 0.004))
        z += spacing_z
    if gate:
        objs += [cube(asset+"_LockBody", (width/2-0.18, -0.12, 0.82), (0.15, 0.10, 0.19)),
                 cube(asset+"_HingeTop", (-width/2+0.03, -0.10, 1.48), (0.05, 0.07, 0.12)),
                 cube(asset+"_HingeBottom", (-width/2+0.03, -0.10, 0.40), (0.05, 0.07, 0.12))]
    return join_export(asset, objs, {"revision":"v648", "repair":"procedural structural rebuild",
        "reason":"v646 contained flattened reference-sheet artefacts", "gate":gate})

reports = []
reports.append(build_panel("SM_CA_MW_PT_FixedSafetyFence", False))
reports.append(build_panel("SM_CA_MW_PT_InterlockedGate", True))

reset()
bpy.ops.import_scene.gltf(filepath=str(SRC_DOOR))
door = next(o for o in bpy.context.scene.objects if o.type == "MESH")
door.name = "SM_CA_MW_PT_RightAccessDoor"
door.scale.x *= -1.0
bpy.context.view_layer.objects.active = door
door.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
reports.append(join_export("SM_CA_MW_PT_RightAccessDoor", [door], {"revision":"v648",
    "repair":"mirrored accepted left access door", "reason":"v646 right-door output became a cabinet"}))

(OUT / "REPAIR_MANIFEST_v648.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
print("LB_REPAIR_V648=" + json.dumps(reports, separators=(",", ":")))
