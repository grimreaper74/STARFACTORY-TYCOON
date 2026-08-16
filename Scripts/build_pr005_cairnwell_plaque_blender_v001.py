"""Build a standalone, dimensioned PR-005 Cairnwell asset plaque candidate."""

import json
from pathlib import Path

import bpy


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Brand\Candidate_v001\PR005_Plaque")
BLEND = ROOT / "LB_PR005_CairnwellAssetPlaque_Candidate_v001.blend"
FBX = ROOT / "SM_LB_PR005_CairnwellAssetPlaque_Candidate_v001.fbx"
MANIFEST = ROOT / "manifest.json"

ROOT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Cabinet is 600 mm wide. The plate follows the approved 480 x 144 mm identity
# proportion and uses a manufacturable 12 mm engraved/printed metal carrier.
bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 0.0))
plaque = bpy.context.object
plaque.name = "SM_LB_PR005_CairnwellAssetPlaque_Candidate_v001"
plaque.dimensions = (0.012, 0.480, 0.144)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bevel = plaque.modifiers.new("ManufacturedEdgeRadius_2mm", "BEVEL")
bevel.width = 0.002
bevel.segments = 3
bpy.context.view_layer.objects.active = plaque
bpy.ops.object.modifier_apply(modifier=bevel.name)

material = bpy.data.materials.new("MI_Cairnwell_PlaqueCarrier")
material.diffuse_color = (0.035, 0.045, 0.043, 1.0)
material.metallic = 0.72
material.roughness = 0.34
plaque.data.materials.append(material)

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
bpy.ops.object.select_all(action="DESELECT")
plaque.select_set(True)
bpy.context.view_layer.objects.active = plaque
bpy.ops.export_scene.fbx(
    filepath=str(FBX), use_selection=True, object_types={"MESH"},
    apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
    axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True,
    mesh_smooth_type="FACE", use_tspace=True, bake_anim=False,
    add_leaf_bones=False, path_mode="AUTO",
)

MANIFEST.write_text(json.dumps({
    "status": "CANDIDATE_NOT_PROMOTED",
    "asset": plaque.name,
    "dimensions_mm": [12, 480, 144],
    "source_blend": str(BLEND),
    "export_fbx": str(FBX),
    "mount_source_blend": r"C:\Users\greg_\Projects\car factoy mayhem\art\source\tests\pr005_3d_viability\guarding_hmi_v013\pr005_guarding_hmi_v013.blend",
    "mount_world_blender_m": [-2.905, -2.8, 0.655],
    "mount_world_unreal_cm": [-290.7, 280.0, 65.5],
    "note": "X location includes 2 mm stand-off ahead of the authored plate face.",
}, indent=2), encoding="utf-8")
print(f"LINE_BOSS_PR005_CAIRNWELL_PLAQUE_BUILD_PASS fbx={FBX}")
