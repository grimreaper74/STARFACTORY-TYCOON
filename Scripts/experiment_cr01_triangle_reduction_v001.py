"""Isolated CR01 triangle-reduction and Blender add-on experiment.

Run by opening the frozen textured CR01 source blend, then executing this script.
It never saves over the source.  Reduced FBXs are exported through PROTO Game
Asset Tools, while Texel Density Checker verifies that each reduced mesh still
has usable UV density.  Blender's native Collapse decimator performs the actual
automatic reduction; PolyQuilt remains a manual retopology tool.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = PROJECT / "SourceAssets/Candidate/PressShop/CleaningRobot/Cairnwell_LB_CR01_v938/Cairnwell_LB_CR01_TexturedVisual_v938.blend"
OUTPUT = PROJECT / "Saved/Experiments/SupportRobots/CR01_TriangleReduction_v001"
EXPORTS = OUTPUT / "Exports"
RENDERS = OUTPUT / "Renders"
MANIFEST = OUTPUT / "experiment_manifest_v001.json"
STUDY_BLEND = OUTPUT / "LB_CR01_TriangleReductionStudy_v001.blend"
COMPARISON = RENDERS / "LB_CR01_TriangleReduction_Comparison_v001.png"

TARGETS = (
    ("CR01_LOD_Close_200k_v001", 200_000),
    ("CR01_LOD_Game_75k_v001", 75_000),
    ("CR01_LOD_Far_25k_v001", 25_000),
)


def fail(message: str) -> None:
    raise RuntimeError("CR01_TRIANGLE_REDUCTION_V001_FAIL: " + message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def triangle_count(obj: bpy.types.Object) -> int:
    return sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons)


def dimensions_cm(obj: bpy.types.Object) -> list[float]:
    return [round(float(value) * 100.0, 5) for value in obj.dimensions]


def select_only(obj: bpy.types.Object) -> None:
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def measure_texel_density(obj: bpy.types.Object) -> dict[str, object]:
    select_only(obj)
    td = bpy.context.scene.td
    td.texture_size = "2048"
    td.selected_faces = False
    result = bpy.ops.object.texel_density_check()
    if "FINISHED" not in result:
        fail(f"Texel Density Checker failed for {obj.name}: {sorted(result)}")
    try:
        density = float(td.density)
        uv_space = float(str(td.uv_space).replace("%", "").strip())
    except ValueError as exc:
        fail(f"Texel Density Checker returned invalid values for {obj.name}: {exc}")
    if density <= 0.0 or uv_space <= 0.0:
        fail(f"Texel Density Checker returned non-positive UV evidence for {obj.name}")
    return {
        "operator": "object.texel_density_check",
        "texture_resolution": 2048,
        "density": density,
        "uv_space_percent": uv_space,
    }


def proto_export(obj: bpy.types.Object, destination: Path) -> None:
    select_only(obj)
    quick = bpy.context.scene.proto_quickexport
    quick.quick_export_mode = "ExportSelected"
    props = quick.export_selected_properties
    props.model_path = str(destination)
    props.scene_conversion_mode = "Unreal"
    props.apply_modifiers_mode = "No"
    props.move_to_origin = True
    result = bpy.ops.prototools.quick_export_mesh(export_name=obj.name)
    if "FINISHED" not in result or not destination.is_file():
        fail(f"PROTO Unreal FBX export failed for {obj.name}: {sorted(result)}")


def look_at(obj: bpy.types.Object, point: Vector) -> None:
    obj.rotation_euler = (point - obj.location).to_track_quat("-Z", "Y").to_euler()


def new_principled_material(name: str, colour: tuple[float, float, float, float], roughness: float, emission: float = 0.0) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Roughness"].default_value = roughness
    if emission > 0.0:
        bsdf.inputs["Emission Color"].default_value = colour
        bsdf.inputs["Emission Strength"].default_value = emission
    return material


def create_comparison_scene(objects: list[bpy.types.Object], labels: list[str]) -> None:
    # Remove source cameras/lights while retaining the meshes, packed images and materials.
    keep = set(objects)
    for obj in list(bpy.data.objects):
        if obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)

    spacing = 2.45
    positions = [spacing * (index - (len(objects) - 1) / 2.0) for index in range(len(objects))]
    for obj, x in zip(objects, positions):
        obj.location = Vector((x, 0.0, 0.0))
        obj.rotation_euler = (0.0, 0.0, 0.0)
        obj.scale = (1.0, 1.0, 1.0)
        obj.hide_render = False
        obj.hide_set(False)

    min_z = min((obj.matrix_world @ Vector(corner)).z for obj in objects for corner in obj.bound_box)
    max_z = max((obj.matrix_world @ Vector(corner)).z for obj in objects for corner in obj.bound_box)

    bpy.ops.mesh.primitive_plane_add(size=14.0, location=(0.0, 0.0, min_z - 0.02))
    floor = bpy.context.object
    floor.name = "CR01_StudyFloor"
    floor.data.materials.append(new_principled_material("M_CR01_StudyFloor", (0.055, 0.065, 0.07, 1.0), 0.78))

    label_material = new_principled_material("M_CR01_StudyLabel", (0.8, 0.94, 0.88, 1.0), 0.35, emission=1.2)
    text_objects: list[bpy.types.Object] = []
    for x, label in zip(positions, labels):
        bpy.ops.object.text_add(location=(x - 0.78, -0.72, max_z + 0.28))
        text = bpy.context.object
        text.name = "Label_" + label.replace(" ", "_")
        text.data.body = label
        text.data.align_x = "LEFT"
        text.data.size = 0.22
        text.data.extrude = 0.004
        text.data.materials.append(label_material)
        text_objects.append(text)

    bpy.ops.object.camera_add(location=(6.8, -12.6, 5.8))
    camera = bpy.context.object
    camera.name = "CR01_StudyCamera"
    camera.data.lens = 54.0
    look_at(camera, Vector((0.0, 0.0, 0.62)))
    bpy.context.scene.camera = camera
    for text in text_objects:
        text.rotation_euler = camera.rotation_euler

    for name, location, energy, size in (
        ("Key", (-3.5, -4.5, 6.5), 1250.0, 5.0),
        ("Fill", (5.0, -1.5, 4.0), 850.0, 4.0),
        ("Rim", (0.0, 4.0, 5.5), 1050.0, 3.0),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = "CR01_Study" + name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        look_at(light, Vector((0.0, 0.0, 0.65)))

    scene = bpy.context.scene
    # Blender 5.2 exposes Eevee Next under the BLENDER_EEVEE enum identifier.
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.filepath = str(COMPARISON)
    scene.render.image_settings.color_mode = "RGBA"
    scene.world.color = (0.012, 0.016, 0.02)
    scene.view_settings.look = "AgX - Medium High Contrast"


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        fail("wrong source blend opened")
    if MANIFEST.exists() or STUDY_BLEND.exists() or OUTPUT.exists():
        fail("output already exists; experiment is one-shot and non-overwriting")

    OUTPUT.mkdir(parents=True)
    EXPORTS.mkdir()
    RENDERS.mkdir()

    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    if len(meshes) != 1:
        fail(f"expected exactly one source mesh, found {len(meshes)}")
    source = meshes[0]
    source.name = "CR01_SOURCE_1M955K_v938"
    source_triangles = triangle_count(source)
    if source_triangles != 1_955_114:
        fail(f"source triangle drift: {source_triangles}")
    if [layer.name for layer in source.data.uv_layers] != ["UVMap"]:
        fail("source UV contract drift")
    if [slot.material.name if slot.material else None for slot in source.material_slots] != ["Material_0"]:
        fail("source material contract drift")

    source_dimensions = dimensions_cm(source)
    source_td = measure_texel_density(source)
    reduced: list[bpy.types.Object] = []
    rows: list[dict[str, object]] = []

    for name, target in TARGETS:
        started = time.monotonic()
        obj = source.copy()
        obj.data = source.data.copy()
        obj.name = name
        bpy.context.scene.collection.objects.link(obj)
        select_only(obj)

        modifier = obj.modifiers.new(name="CR01_AutomaticReduction_v001", type="DECIMATE")
        modifier.decimate_type = "COLLAPSE"
        modifier.ratio = max(0.0001, min(1.0, target / source_triangles))
        modifier.use_collapse_triangulate = True
        result = bpy.ops.object.modifier_apply(modifier=modifier.name)
        if "FINISHED" not in result:
            fail(f"native decimator failed for {name}: {sorted(result)}")
        obj.data.update()
        for polygon in obj.data.polygons:
            polygon.use_smooth = True

        actual = triangle_count(obj)
        if actual > int(target * 1.04) or actual < int(target * 0.90):
            fail(f"triangle result outside target band for {name}: {actual} vs {target}")
        if [layer.name for layer in obj.data.uv_layers] != ["UVMap"]:
            fail(f"UV layer lost for {name}")
        materials = [slot.material.name if slot.material else None for slot in obj.material_slots]
        if materials != ["Material_0"]:
            fail(f"material slot drift for {name}: {materials}")
        dims = dimensions_cm(obj)
        max_dimension_drift = max(abs(a - b) for a, b in zip(source_dimensions, dims))
        if max_dimension_drift > 1.0:
            fail(f"bounds drift exceeds 1 cm for {name}: {max_dimension_drift}")

        texel = measure_texel_density(obj)
        fbx_path = EXPORTS / f"SM_LB_{name}.fbx"
        proto_export(obj, fbx_path)
        reduced.append(obj)
        rows.append({
            "name": name,
            "target_triangles": target,
            "actual_triangles": actual,
            "reduction_percent": round(100.0 * (1.0 - actual / source_triangles), 4),
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "dimensions_cm": dims,
            "max_dimension_drift_cm": round(max_dimension_drift, 6),
            "uv_layers": [layer.name for layer in obj.data.uv_layers],
            "materials": materials,
            "texel_density_checker": texel,
            "fbx": str(fbx_path.relative_to(OUTPUT)).replace("\\", "/"),
            "fbx_sha256": sha256(fbx_path),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        })

    labels = ["SOURCE 1.96M", "AUTO 200K", "AUTO 75K", "AUTO 25K"]
    create_comparison_scene([source] + reduced, labels)
    bpy.ops.wm.save_as_mainfile(filepath=str(STUDY_BLEND), check_existing=False)
    bpy.ops.render.render(write_still=True)
    if not STUDY_BLEND.is_file() or not COMPARISON.is_file():
        fail("study blend or comparison render missing")

    payload = {
        "schema": "lineboss/experiment/support-robots/cr01-triangle-reduction-v001/v1",
        "status": "PASS__ISOLATED_CR01_AUTOMATIC_REDUCTION_AND_ADDON_EXPORT_EXPERIMENT_V001",
        "source": {
            "path": str(SOURCE),
            "sha256": sha256(SOURCE),
            "triangles": source_triangles,
            "vertices": len(source.data.vertices),
            "dimensions_cm": source_dimensions,
            "uv_layers": [layer.name for layer in source.data.uv_layers],
            "materials": [slot.material.name if slot.material else None for slot in source.material_slots],
            "texel_density_checker": source_td,
        },
        "reducers": {
            "automatic": "Blender native Collapse Decimate modifier",
            "manual_followup": "PolyQuilt Fork retopology (not used headlessly)",
        },
        "addons": {
            "enabled": sorted(bpy.context.preferences.addons.keys()),
            "proto_game_asset_tools": {
                "used": True,
                "operator": "prototools.quick_export_mesh",
                "scene_conversion": "Unreal",
            },
            "texel_density_checker": {
                "used": True,
                "operator": "object.texel_density_check",
                "resolution": 2048,
            },
            "polyquilt_fork": {
                "used": False,
                "reason": "interactive manual retopology tool; not an automatic or headless decimator",
            },
            "node_wrangler": {
                "used": False,
                "reason": "material-node workflow helper; geometry reduction does not need node edits",
            },
        },
        "results": rows,
        "study_blend": {
            "path": str(STUDY_BLEND.relative_to(OUTPUT)).replace("\\", "/"),
            "sha256": sha256(STUDY_BLEND),
        },
        "comparison_render": {
            "path": str(COMPARISON.relative_to(OUTPUT)).replace("\\", "/"),
            "sha256": sha256(COMPARISON),
        },
        "source_modified": False,
        "unreal_content_modified": False,
        "promotion_authorized": False,
        "limitations": [
            "The Meshy source remains one monolithic mesh; triangle reduction does not create articulation pivots.",
            "Automatic decimation must pass visual review before any Unreal import.",
            "Final collision, LOD screens, state lights and runtime anchor binding remain separate work.",
        ],
        "failures": [],
    }
    MANIFEST.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("CR01_TRIANGLE_REDUCTION_V001_PASS=" + str(MANIFEST))


if __name__ == "__main__":
    main()
