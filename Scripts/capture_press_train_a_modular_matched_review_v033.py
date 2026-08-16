"""Bright, matched, non-mutating visual review for Train A v033."""
import bpy, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v033/CA_MW_PressTrainA_ModularAssembly_v033.blend"
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v033/MatchedReview"
REPORT = OUT / "PRESS_TRAIN_A_MATCHED_REVIEW_v033.json"
OUT.mkdir(parents=True, exist_ok=True)
if REPORT.exists() or any(OUT.glob("*.png")):
    raise RuntimeError("refusing to overwrite v033 matched review")

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

bpy.ops.wm.open_mainfile(filepath=str(SRC))
scene = bpy.context.scene
for obj in list(bpy.data.objects):
    if obj.type in {"LIGHT", "CAMERA"}:
        bpy.data.objects.remove(obj, do_unlink=True)
world = scene.world or bpy.data.worlds.new("MatchedReviewWorld_v033")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.1, 0.12, 0.14, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = 1.35
for loc, energy, size in (((45, -5, 28), 15000, 22), ((-42, 50, 24), 13000, 22), ((0, 22, 38), 12000, 28), ((30, 25, 10), 8000, 16)):
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
bpy.ops.object.camera_add()
cam = bpy.context.object
cam.data.type = "ORTHO"
scene.camera = cam
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1800
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False

def look(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

views = (
    ("operator", (72, 22.5, 5.7), (0, 22.5, 4.4), 52, 0),
    ("rear", (-72, 22.5, 5.7), (0, 22.5, 4.4), 52, 0),
    ("elevated", (55, -18, 34), (0, 22.5, 3.3), 60, 0),
    # Rotate the overhead camera so the 45 m train uses the landscape frame.
    ("top", (0, 22.5, 90), (0, 22.5, 0), 52, math.pi / 2),
)
captures = []
for name, location, target, scale, roll in views:
    cam.location = location
    cam.data.ortho_scale = scale
    look(cam, target)
    cam.rotation_euler.z = roll
    path = OUT / f"train_a_matched_{name}_v033.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    captures.append({"view": name, "file": path.name, "sha256": sha(path)})
payload = {
    "$schema": "cairnwell/source/press-train-a-matched-review-v033/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FRESH_BRIGHT_MATCHED_SOURCE_REVIEW__HUMAN_DECISION_REQUIRED__NOT_PROMOTED",
    "source_sha256": sha(SRC),
    "captures": captures,
    "source_mutated": False,
    "promotion_authorized": False,
}
REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
