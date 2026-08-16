"""Build a clean, source-only Meshy Train A press-body comparison.

No legacy Train A visual assets are included. Nothing is written to Unreal.
"""
import bpy
import json
import math
from datetime import datetime, timezone
from hashlib import sha256
from mathutils import Vector
from pathlib import Path

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ProDetailModular_v046/CA_MW_PressTrainA_ProDetailModular_v046.blend"
MESHY = Path(r"C:\Users\greg_\Downloads\Meshy_AI_Cairnwell_S03_Walker_0808080548_texture.glb")
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/HybridMeshyEvaluation_v633"
BLEND = OUT / "CA_MW_PressTrainA_HybridMeshyEvaluation_v633.blend"
RENDER = OUT / "CA_MW_PressTrainA_HybridMeshyEvaluation_OperatorThreeQuarter_v633.png"
MANIFEST = OUT / "PRESS_TRAIN_A_HYBRID_MESHY_EVALUATION_v633.json"

STATIONS = {"S02": 7.5, "S03": 15.0, "S04": 22.5, "S05": 30.0, "S06": 37.5}
TARGET_HEIGHT = 7.2  # visual fit only; engineering values remain TBC


def digest(path):
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def bounds(objects):
    corners = [obj.matrix_world @ Vector(c) for obj in objects for c in obj.bound_box]
    lo = Vector(tuple(min(c[i] for c in corners) for i in range(3)))
    hi = Vector(tuple(max(c[i] for c in corners) for i in range(3)))
    return lo, hi


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
hidden = []

before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(MESHY))
imported = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
if not imported:
    raise RuntimeError("Meshy import created no mesh objects")

# Join only if a later Meshy export contains more than one top-level mesh.
bpy.ops.object.select_all(action="DESELECT")
for obj in imported:
    obj.select_set(True)
bpy.context.view_layer.objects.active = imported[0]
if len(imported) > 1:
    bpy.ops.object.join()
master = bpy.context.object
master.name = "SM_CA_MW_PTA_S02_MeshyPressVisual_v633"

# Meshy is front-facing on Y. Rotate the press so its operator face follows the
# established Train A operator aisle (world -X). Preserve the generated asset's
# proportions: non-uniform scaling made the body appear flattened.
master.rotation_euler[2] = 0.0
bpy.context.view_layer.objects.active = master
bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
lo, hi = bounds([master])
master.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
bpy.context.view_layer.update()
current = Vector(master.dimensions)
uniform_scale = TARGET_HEIGHT / current.z
master.scale = Vector((uniform_scale, uniform_scale, uniform_scale))
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
# Applying scale changes the world bounds; re-seat the model precisely on Z=0.
lo, hi = bounds([master])
master.location.z -= lo.z
floor_contact_z = master.location.z
master.location = (0.0, STATIONS["S02"], floor_contact_z)

instances = {"S02": master.name}
for station, y in list(STATIONS.items())[1:]:
    duplicate = master.copy()
    duplicate.data = master.data
    duplicate.name = f"SM_CA_MW_PTA_{station}_MeshyPressVisual_v633"
    duplicate.location = (0.0, y, floor_contact_z)
    bpy.context.collection.objects.link(duplicate)
    instances[station] = duplicate.name

# Keep the evaluation responsive: linked geometry and Eevee preview rendering.
for obj in list(bpy.data.objects):
    if obj.type in {"CAMERA", "LIGHT"}:
        bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
if scene.world is None:
    scene.world = bpy.data.worlds.new("HybridEvaluationWorld")
scene.world.color = (0.025, 0.03, 0.035)

# Neutral concrete floor for scale/context, outside the asset collection.
bpy.ops.mesh.primitive_plane_add(size=90, location=(0, 22.5, -0.025))
floor = bpy.context.object
floor.name = "REVIEW_FLOOR_ONLY_v633"
mat = bpy.data.materials.new("M_REVIEW_Concrete_v633")
mat.diffuse_color = (0.12, 0.135, 0.14, 1.0)
mat.roughness = 0.82
floor.data.materials.append(mat)

for name, location, energy, size in (
    ("ReviewKey", (-16, 8, 18), 3300, 12),
    ("ReviewFill", (-5, 39, 15), 2600, 10),
    ("ReviewRim", (15, 24, 17), 3000, 9),
):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    light = bpy.data.objects.new(name, data)
    light.location = location
    bpy.context.collection.objects.link(light)
    look_at(light, (0, 22.5, 3.5))

camera_data = bpy.data.cameras.new("ReviewCamera_v633")
camera = bpy.data.objects.new("ReviewCamera_v633", camera_data)
bpy.context.collection.objects.link(camera)
camera.location = (-31.5, -3.0, 15.5)
camera.data.lens = 52
look_at(camera, (0, 22.5, 3.7))
scene.camera = camera
scene.render.filepath = str(RENDER)

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
bpy.ops.render.render(write_still=True)

payload = {
    "$schema": "cairnwell/source/press-train-a-hybrid-meshy-evaluation-v633/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SOURCE_ONLY_MESHY_PRESS_BODY_EVALUATION__NOT_PROMOTED",
    "source_parent": str(SOURCE),
    "source_parent_sha256": digest(SOURCE),
    "meshy_source": str(MESHY),
    "meshy_source_sha256": digest(MESHY),
    "retained": [],
    "excluded_for_clean_review": "all legacy Train A models and supporting systems",
    "replaced_for_review": "S02-S06 press-body visuals only",
    "hidden_old_object_count": len(hidden),
    "meshy_instances": instances,
    "linked_mesh_data": True,
    "visual_target_height_m_tbc": TARGET_HEIGHT,
    "uniform_scale_preserves_meshy_proportions": True,
    "engineering_values": "TBC_NOT_INVENTED",
    "runtime_authority_added": False,
    "unreal_content_modified": False,
    "promotion_authorized": False,
    "blend": str(BLEND),
    "blend_sha256": digest(BLEND),
    "render": str(RENDER),
}
MANIFEST.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"blend": str(BLEND), "render": str(RENDER), "hidden": len(hidden), "instances": instances}, indent=2))
