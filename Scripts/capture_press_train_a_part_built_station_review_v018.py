"""Create full-height review renders from immutable part-built source v018."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v018/CA_MW_PressModulePrototype_v018.blend"
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v018/FullHeightReview"
REPORT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v018/PRESS_MODULE_FULL_HEIGHT_REVIEW_v018.json"
OUT.mkdir(parents=True, exist_ok=True)
if REPORT.exists():
    raise RuntimeError("Refusing to overwrite immutable v018 full-height review")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.render.resolution_x = 1400
scene.render.resolution_y = 1400
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

def look(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

camera = bpy.data.objects.get("PressModule_v018_Camera")
if camera is None:
    raise RuntimeError("v018 camera missing")

# Review-only floor.
mat = bpy.data.materials.get("StudioGround")
if mat is None:
    mat = bpy.data.materials.new("StudioGround")
    mat.diffuse_color = (0.055, 0.06, 0.065, 1.0)
bpy.ops.mesh.primitive_plane_add(size=26, location=(0, 0, -0.02))
floor = bpy.context.object
floor.name = "ReviewOnlyFloor"
floor.data.materials.append(mat)

views = [
    ("01_full_operator_v018.png", (10.8, -13.8, 7.2), (0, 0, 4.45), 62),
    ("02_full_service_v018.png", (-10.8, -13.2, 7.5), (0, 0, 4.45), 62),
    ("03_full_front_v018.png", (0, -17.0, 4.55), (0, 0, 4.55), 66),
]
for filename, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look(camera, target)
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)

REPORT.write_text(json.dumps({
    "status": "FRESH_FULL_HEIGHT_SOURCE_REVIEW__SUBJECTIVE_DECISION_REQUIRED__NOT_PROMOTED",
    "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
    "source_changed": False,
    "renders": [str((OUT / row[0]).relative_to(ROOT)).replace("\\", "/") for row in views],
    "promotion_authorized": False
}, indent=2), encoding="utf-8")
print(REPORT)
