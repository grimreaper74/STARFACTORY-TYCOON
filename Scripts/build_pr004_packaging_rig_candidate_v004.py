"""Build the isolated PR-004 PackagingRig v004 hero-surface candidate.

v003 remains immutable evidence.  This pass opens that UV-complete source,
replaces only the visually rejected packaged-coil presentation meshes, keeps
all gameplay/runtime templates, rebuilds UV0 and exports a new quarantined
package.  Nothing here imports or promotes an Unreal asset.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE_ROOT = REPO / "SourceAssets/PR004/PackagingRig_v003"
DEST_ROOT = REPO / "SourceAssets/PR004/PackagingRig_v004"
SOURCE_BLEND = SOURCE_ROOT / "LB_PR004_PackagingRig_Candidate_v003.blend"
SOURCE_MANIFEST = SOURCE_ROOT / "pr004_packaging_rig_candidate_v003_manifest.json"
DEST_BLEND = DEST_ROOT / "LB_PR004_PackagingRig_Candidate_v004.blend"
DEST_MANIFEST = DEST_ROOT / "pr004_packaging_rig_candidate_v004_manifest.json"
AUDIT = REPO / "Saved/Audits/pr004_packaging_rig_candidate_v004_build.json"

WRAP_INNER = 0.949
WRAP_OUTER = 0.958
FACE_INNER = 0.312
FACE_OUTER = 0.958


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def material_with(token: str):
    matches = [material for material in bpy.data.materials if token.lower() in material.name.lower()]
    if not matches:
        raise RuntimeError(f"Missing source material containing {token!r}")
    return matches[0]


def mesh_object(name, vertices, faces, material, smooth=False):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = smooth
    return obj


def box(name, location, dimensions, material, rotation_x=0.0, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=(rotation_x, 0.0, 0.0))
    obj = bpy.context.active_object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("Manufactured edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
        modifier.limit_method = "ANGLE"
    return obj


def apply_modifiers(objects):
    for obj in objects:
        if obj.type != "MESH":
            continue
        obj.hide_viewport = False
        obj.hide_set(False)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        for modifier in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=modifier.name)


def join_objects(objects, name):
    apply_modifiers(objects)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    result = bpy.context.active_object
    result.name = name
    return result


def set_origin_to_world_point(obj, point):
    delta = Vector(point) - obj.location
    obj.data.transform(Matrix.Translation(-delta))
    obj.location = Vector(point)


def copy_scalar_properties(source, target):
    for key in source.keys():
        if key != "_RNA_UI":
            target[key] = source[key]


def delete_object(obj):
    mesh = obj.data if obj.type == "MESH" else None
    bpy.data.objects.remove(obj, do_unlink=True)
    if mesh is not None and mesh.users == 0:
        bpy.data.meshes.remove(mesh)


def wrinkled_od_sector(name, index, material):
    """Closed overlapping sheet with real low-amplitude cloth relief."""
    count = 12
    overlap = math.radians(1.35)
    a0 = 2.0 * math.pi * index / count - overlap
    a1 = 2.0 * math.pi * (index + 1) / count + overlap
    x_steps, angle_steps = 22, 14
    vertices = []
    for layer in range(2):
        for ix in range(x_steps + 1):
            u = ix / x_steps
            x = -0.752 + 1.504 * u
            for ia in range(angle_steps + 1):
                v = ia / angle_steps
                angle = a0 + (a1 - a0) * v
                if layer == 0:
                    relief = 0.0034 * math.sin(math.pi * v) * math.sin(5.0 * math.pi * u + index * 0.71)
                    relief += 0.0017 * math.sin(math.pi * u) * math.sin(3.0 * math.pi * v + index * 0.43)
                    radius = WRAP_OUTER + relief
                else:
                    radius = WRAP_INNER
                vertices.append((x, radius * math.cos(angle), radius * math.sin(angle)))

    stride = angle_steps + 1
    layer_size = (x_steps + 1) * stride

    def vid(layer, ix, ia):
        return layer * layer_size + ix * stride + ia

    faces = []
    for ix in range(x_steps):
        for ia in range(angle_steps):
            faces.append((vid(0, ix, ia), vid(0, ix + 1, ia), vid(0, ix + 1, ia + 1), vid(0, ix, ia + 1)))
            faces.append((vid(1, ix, ia + 1), vid(1, ix + 1, ia + 1), vid(1, ix + 1, ia), vid(1, ix, ia)))
    for ix in range(x_steps):
        faces.append((vid(0, ix, 0), vid(1, ix, 0), vid(1, ix + 1, 0), vid(0, ix + 1, 0)))
        faces.append((vid(0, ix, angle_steps), vid(0, ix + 1, angle_steps), vid(1, ix + 1, angle_steps), vid(1, ix, angle_steps)))
    for ia in range(angle_steps):
        faces.append((vid(0, 0, ia), vid(0, 0, ia + 1), vid(1, 0, ia + 1), vid(1, 0, ia)))
        faces.append((vid(0, x_steps, ia + 1), vid(0, x_steps, ia), vid(1, x_steps, ia), vid(1, x_steps, ia + 1)))
    return mesh_object(name, vertices, faces, material, smooth=True)


def wrinkled_face_half(name, side, cap_index, material):
    """One half of a face annulus, tessellated so it reads as wrapped sheet."""
    overlap = math.radians(1.1)
    if cap_index == 1:
        a0, a1 = -0.5 * math.pi - overlap, 0.5 * math.pi + overlap
    else:
        a0, a1 = 0.5 * math.pi - overlap, 1.5 * math.pi + overlap
    radial_steps, angle_steps = 13, 56
    face_x = side * 0.757
    vertices = []
    for layer in range(2):
        for ir in range(radial_steps + 1):
            u = ir / radial_steps
            radius = FACE_INNER + (FACE_OUTER - FACE_INNER) * u
            for ia in range(angle_steps + 1):
                v = ia / angle_steps
                angle = a0 + (a1 - a0) * v
                relief = 0.0
                if layer == 0:
                    relief = 0.0030 * math.sin(math.pi * u) * math.sin(4.0 * math.pi * v + cap_index * 0.9)
                    relief += 0.0018 * math.sin(3.0 * math.pi * u + 0.7) * math.sin(math.pi * v)
                x = face_x + side * (relief if layer == 0 else -0.006)
                vertices.append((x, radius * math.cos(angle), radius * math.sin(angle)))

    stride = angle_steps + 1
    layer_size = (radial_steps + 1) * stride

    def vid(layer, ir, ia):
        return layer * layer_size + ir * stride + ia

    faces = []
    for ir in range(radial_steps):
        for ia in range(angle_steps):
            front = (vid(0, ir, ia), vid(0, ir + 1, ia), vid(0, ir + 1, ia + 1), vid(0, ir, ia + 1))
            back = (vid(1, ir, ia + 1), vid(1, ir + 1, ia + 1), vid(1, ir + 1, ia), vid(1, ir, ia))
            faces.append(front if side > 0 else tuple(reversed(front)))
            faces.append(back if side < 0 else tuple(reversed(back)))
    for ir in range(radial_steps):
        faces.append((vid(0, ir, 0), vid(1, ir, 0), vid(1, ir + 1, 0), vid(0, ir + 1, 0)))
        faces.append((vid(0, ir, angle_steps), vid(0, ir + 1, angle_steps), vid(1, ir + 1, angle_steps), vid(1, ir, angle_steps)))
    for ia in range(angle_steps):
        faces.append((vid(0, 0, ia + 1), vid(0, 0, ia), vid(1, 0, ia), vid(1, 0, ia + 1)))
        faces.append((vid(0, radial_steps, ia), vid(0, radial_steps, ia + 1), vid(1, radial_steps, ia + 1), vid(1, radial_steps, ia)))
    return mesh_object(name, vertices, faces, material, smooth=True)


def arc_points(center_x, center_r, radius, start, end, steps):
    return [
        (center_x + radius * math.cos(start + (end - start) * i / steps),
         center_r + radius * math.sin(start + (end - start) * i / steps))
        for i in range(steps + 1)
    ]


def conforming_loop_profile(outer_x, outer_r, bore_r, bend_radius=0.025):
    face_x = outer_x + 0.003
    profile = [(-outer_x + bend_radius, outer_r), (outer_x - bend_radius, outer_r)]
    profile.extend(arc_points(outer_x - bend_radius, outer_r - bend_radius, bend_radius, math.pi / 2, 0, 5)[1:])
    profile.append((face_x, bore_r + bend_radius))
    profile.extend(arc_points(outer_x - bend_radius, bore_r + bend_radius, bend_radius, 0, -math.pi / 2, 5)[1:])
    profile.append((-outer_x + bend_radius, bore_r))
    profile.extend(arc_points(-outer_x + bend_radius, bore_r + bend_radius, bend_radius, -math.pi / 2, -math.pi, 5)[1:])
    profile.append((-face_x, outer_r - bend_radius))
    profile.extend(arc_points(-outer_x + bend_radius, outer_r - bend_radius, bend_radius, math.pi, math.pi / 2, 5)[1:])
    return profile


def swept_profile_strip(name, profile_xr, angle, width, thickness, material, closed=True, bevel=0.0):
    path = list(profile_xr)
    ring_count = len(path)
    tangent_dir = Vector((0.0, -math.sin(angle), math.cos(angle)))
    radial_dir = Vector((0.0, math.cos(angle), math.sin(angle)))
    centres = [Vector((x, radial_dir.y * radius, radial_dir.z * radius)) for x, radius in path]
    vertices = []
    for i, centre in enumerate(centres):
        previous = (i - 1) % ring_count if closed else max(0, i - 1)
        following = (i + 1) % ring_count if closed else min(ring_count - 1, i + 1)
        travel = centres[following] - centres[previous]
        if travel.length < 1e-6:
            travel = Vector((1.0, 0.0, 0.0))
        travel.normalize()
        normal = travel.cross(tangent_dir)
        if normal.length < 1e-6:
            normal = radial_dir.copy()
        normal.normalize()
        for across in (-1.0, 1.0):
            for depth in (-1.0, 1.0):
                vertices.append(tuple(centre + tangent_dir * across * width * 0.5 + normal * depth * thickness * 0.5))
    faces = []
    segments = ring_count if closed else ring_count - 1
    for i in range(segments):
        j = (i + 1) % ring_count
        a, b = i * 4, j * 4
        faces.extend(((a, b, b + 2, a + 2), (a + 1, a + 3, b + 3, b + 1),
                      (a, a + 1, b + 1, b), (a + 2, b + 2, b + 3, a + 3)))
    obj = mesh_object(name, vertices, faces, material)
    if bevel:
        modifier = obj.modifiers.new("Rolled strip edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
        modifier.limit_method = "ANGLE"
    return obj


def rebuild_uv(obj):
    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_set(False)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    while obj.data.uv_layers:
        obj.data.uv_layers.remove(obj.data.uv_layers[0])
    obj.data.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.025, correct_aspect=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    layer = obj.data.uv_layers.get("UVMap")
    complete = layer is not None and len(layer.data) == len(obj.data.loops) and len(layer.data) > 0
    if not complete:
        raise RuntimeError(f"UV rebuild failed for {obj.name}")
    return {"uv_layer": "UVMap", "mesh_loops": len(obj.data.loops), "uv_entries": len(layer.data), "complete": True}


def mesh_stats(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    result = {
        "vertices": len(mesh.vertices),
        "polygons": len(mesh.polygons),
        "triangles": sum(max(0, len(poly.vertices) - 2) for poly in mesh.polygons),
    }
    evaluated.to_mesh_clear()
    return result


def export_object(obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, object_types={"MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True,
        bake_space_transform=False, add_leaf_bones=False, path_mode="AUTO",
        mesh_smooth_type="FACE", use_custom_props=True,
    )


def replace_v003(value):
    return value.replace("v003", "v004") if isinstance(value, str) else value


DEST_ROOT.mkdir(parents=True, exist_ok=True)
AUDIT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE_BLEND))
source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
source_by_name = {record["name"]: record for record in source_manifest["modules"]}

wrap_material = material_with("ProtectiveWrap_DullGreyPlastic")
strap_material = material_with("BlackSteelBand")
buckle_material = material_with("BandBuckle")
protector_material = material_with("FormedFibreEdgeProtector")
protector_scuff = material_with("EdgeProtectorScuff")

# Replace all 16 visible package sheets while retaining their gameplay IDs.
for index in range(1, 17):
    name = f"SM_LB_PR004_WrapSection_{index:02d}_v003"
    source = bpy.data.objects.get(name)
    if source is None:
        raise RuntimeError(f"Missing source module {name}")
    properties = {key: source[key] for key in source.keys() if key != "_RNA_UI"}
    delete_object(source)
    if index <= 12:
        replacement = wrinkled_od_sector(name, index - 1, wrap_material)
        angle = 2.0 * math.pi * (index - 1) / 12.0
        set_origin_to_world_point(replacement, (0.0, WRAP_OUTER * math.cos(angle), WRAP_OUTER * math.sin(angle)))
    else:
        face_slot = index - 13
        side = -1.0 if face_slot < 2 else 1.0
        cap_index = face_slot % 2 + 1
        replacement = wrinkled_face_half(name, side, cap_index, wrap_material)
        mid = 0.0 if cap_index == 1 else math.pi
        set_origin_to_world_point(replacement, (side * 0.757, 0.90 * math.cos(mid), 0.90 * math.sin(mid)))
    for key, value in properties.items():
        replacement[key] = value
    replacement["visual_revision"] = "V004_TESSELLATED_WRINKLED_CONTINUOUS_PACKAGE"

# Thicker, slightly proud straps remain four independently removable children.
profile = conforming_loop_profile(0.758, 0.969, 0.300)
for index, angle in enumerate((0.0, 0.5 * math.pi, math.pi, 1.5 * math.pi), 1):
    name = f"SM_LB_PR004_Band_{index:02d}_v003"
    source = bpy.data.objects.get(name)
    if source is None:
        raise RuntimeError(f"Missing source module {name}")
    properties = {key: source[key] for key in source.keys() if key != "_RNA_UI"}
    delete_object(source)
    pieces = [swept_profile_strip("BandLoop", profile, angle, 0.055, 0.0030, strap_material, bevel=0.0007)]
    radius = 0.64
    pieces.append(box("StampedKeeper", (0.765, radius * math.cos(angle), radius * math.sin(angle)),
                      (0.008, 0.086, 0.106), buckle_material, rotation_x=angle, bevel=0.004))
    replacement = join_objects(pieces, name)
    set_origin_to_world_point(replacement, (0.0, 0.969 * math.cos(angle), 0.969 * math.sin(angle)))
    for key, value in properties.items():
        replacement[key] = value
    replacement["visual_revision"] = "V004_55MM_READABLE_CONFORMING_BAND"

# Smaller formed shoes protect the actual band/corner contact areas.
for band_index, angle in enumerate((0.0, 0.5 * math.pi, math.pi, 1.5 * math.pi), 1):
    for side in (-1.0, 1.0):
        suffix = "L" if side < 0 else "R"
        name = f"SM_LB_PR004_EdgeProtector_{band_index:02d}_{suffix}_v003"
        source = bpy.data.objects.get(name)
        if source is None:
            raise RuntimeError(f"Missing source module {name}")
        properties = {key: source[key] for key in source.keys() if key != "_RNA_UI"}
        delete_object(source)
        sx = side
        formed = [(sx * 0.675, 0.971), (sx * 0.720, 0.971), (sx * 0.750, 0.955),
                  (sx * 0.765, 0.920), (sx * 0.765, 0.835)]
        pieces = [swept_profile_strip("FormedProtector", formed, angle, 0.125, 0.0080,
                                      protector_material, closed=False, bevel=0.0018)]
        rib = [(sx * 0.695, 0.976), (sx * 0.735, 0.970), (sx * 0.760, 0.940), (sx * 0.768, 0.870)]
        pieces.append(swept_profile_strip("ProtectorRib", rib, angle, 0.016, 0.0095,
                                          protector_scuff, closed=False, bevel=0.0010))
        replacement = join_objects(pieces, name)
        set_origin_to_world_point(replacement, (side * 0.758, 0.89 * math.cos(angle), 0.89 * math.sin(angle)))
        for key, value in properties.items():
            replacement[key] = value
        replacement["visual_revision"] = "V004_COMPACT_FORMED_CORNER_SHOE"

objects = sorted(
    [obj for obj in bpy.data.objects if obj.type == "MESH" and obj.name.startswith("SM_LB_PR004_") and "line_boss_asset_id" in obj],
    key=lambda item: item.name,
)
if len(objects) != 43:
    raise RuntimeError(f"Expected 43 runtime modules after rebuild, found {len(objects)}")

records = []
for obj in objects:
    source_name = obj.name
    source_record = source_by_name.get(source_name)
    if source_record is None:
        raise RuntimeError(f"No v003 manifest record for {source_name}")
    uv = rebuild_uv(obj)
    obj.name = source_name.replace("_v003", "_v004")
    if obj.data:
        obj.data.name = obj.data.name.replace("_v003", "_v004")
    for key in list(obj.keys()):
        if key != "_RNA_UI":
            obj[key] = replace_v003(obj[key])
    fbx = DEST_ROOT / f"{obj.name}.fbx"
    export_object(obj, fbx)
    records.append({
        "name": obj.name,
        "source_name": source_name,
        "asset_id": obj.get("line_boss_asset_id", obj.name),
        "fbx": str(fbx),
        "rest_location_m": [round(float(value), 6) for value in obj.location],
        "rest_rotation_deg": [round(math.degrees(float(value)), 4) for value in obj.rotation_euler],
        "bounds_mm": [round(float(value) * 1000.0, 3) for value in obj.dimensions],
        "mesh": mesh_stats(obj),
        "category": source_record["category"],
        "uv": uv,
        "custom_properties": {key: obj[key] for key in obj.keys() if key != "_RNA_UI"},
        "fbx_sha256": sha256(fbx),
        "geometry_changed_from_v003": source_name.startswith("SM_LB_PR004_WrapSection_")
        or source_name in {f"SM_LB_PR004_Band_{index:02d}_v003" for index in range(1, 5)}
        or source_name.startswith("SM_LB_PR004_EdgeProtector_"),
    })

bpy.ops.wm.save_as_mainfile(filepath=str(DEST_BLEND))
manifest = {
    "$schema": "line-boss/source/pr004-packaging-rig-candidate-v004/v1",
    "version": "v004",
    "status": "CANDIDATE_NOT_PROMOTED",
    "purpose": "RELEASE_READABILITY_PACKAGED_COIL_HERO_SURFACE_CANDIDATE",
    "source_version": "v003",
    "source_blend": str(SOURCE_BLEND),
    "blend": str(DEST_BLEND),
    "source_manifest_sha256": sha256(SOURCE_MANIFEST),
    "module_counts": source_manifest["module_counts"],
    "modules": records,
    "invariants": {
        "module_count_preserved": len(records) == 43,
        "all_meshes_have_complete_uv0": all(record["uv"]["complete"] for record in records),
        "source_v003_untouched": True,
        "runtime_templates_preserved": True,
        "promotion_authorized": False,
    },
}
DEST_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/pr004-packaging-rig-candidate-v004-build/v1",
    "status": "PASS_TECHNICAL_BUILD_ONLY__INDEPENDENT_AND_VISUAL_GATES_PENDING__NOT_PROMOTED",
    "source": str(SOURCE_BLEND),
    "output": str(DEST_BLEND),
    "manifest": str(DEST_MANIFEST),
    "module_count": len(records),
    "geometry_changed_modules": sum(1 for record in records if record["geometry_changed_from_v003"]),
    "all_uv_complete": all(record["uv"]["complete"] for record in records),
    "fbx_count": len(list(DEST_ROOT.glob("*.fbx"))),
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
print(f"LINE_BOSS_PR004_PACKAGING_V004_BUILD_PASS modules={len(records)} manifest={DEST_MANIFEST}")
