"""Integrate the detailed, bore-safe packaged master coil into PR-004 v029."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v028"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneLoadCandidate_v029"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v029"
MESH_DEST = f"{DEST}/ReleaseScale_v002"
MESH_NAME = "SM_LB_MasterCoil_Candidate_v004"
MESH_PATH = f"{MESH_DEST}/{MESH_NAME}"
OLD_TINY_MESH_PATH = f"{DEST}/{MESH_NAME}"
FBX = Path(unreal.Paths.project_dir()) / "SourceAssets/IndustrialKit/MasterCoil/Candidate_v004/SM_LB_MasterCoil_Candidate_v004.fbx"
MANIFEST = Path(unreal.Paths.project_dir()) / "SourceAssets/IndustrialKit/MasterCoil/Candidate_v004/master_coil_candidate_v004_manifest.json"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_crane_load_candidate_v029.json"
WRAP_MASTER = "/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/M_LB_PR004_NonmetalPBR_Master_v003"

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# The generic AssetImportTask bridge does not expose Interchange 5.8's
# bImportCollisionAccordingToMeshName setting. Use the still-supported legacy
# static-mesh factory for this authored FBX so its UCX objects remain collision
# rather than being merged into render triangles.
unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")


def collision_counts(static_mesh):
    if not isinstance(static_mesh, unreal.StaticMesh):
        return {"box": 0, "sphere": 0, "capsule": 0, "convex": 0, "total": 0}
    setup = static_mesh.get_editor_property("body_setup")
    aggregate = setup.get_editor_property("agg_geom") if setup else None
    if aggregate is None:
        return {"box": 0, "sphere": 0, "capsule": 0, "convex": 0, "total": 0}
    counts = {
        "box": len(aggregate.get_editor_property("box_elems")),
        "sphere": len(aggregate.get_editor_property("sphere_elems")),
        "capsule": len(aggregate.get_editor_property("sphyl_elems")),
        "convex": len(aggregate.get_editor_property("convex_elems")),
    }
    counts["total"] = sum(counts.values())
    return counts

source = json.loads(MANIFEST.read_text(encoding="utf-8"))
if source.get("status") != "CANDIDATE_NOT_PROMOTED":
    raise RuntimeError("Packaged-coil source is not quarantined")
if source.get("collision", {}).get("count") != 12:
    raise RuntimeError("Packaged-coil source did not pass the 12-hull UCX gate")
if "ONEDRIVE" in str(FBX).upper() or not FBX.is_file():
    raise RuntimeError(f"Invalid canonical FBX source: {FBX}")

existing_mesh = lib.load_asset(MESH_PATH)
existing_collision_count = collision_counts(existing_mesh)["total"]
existing_bounds_x = -1.0
if isinstance(existing_mesh, unreal.StaticMesh):
    existing_box = existing_mesh.get_bounding_box()
    existing_bounds_x = existing_box.max.x - existing_box.min.x
if existing_collision_count != 12 or not 149.0 <= existing_bounds_x <= 151.0:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(FBX),
        "destination_path": MESH_DEST,
        "destination_name": MESH_NAME,
        "automated": True,
        "replace_existing": True,
        "replace_existing_settings": True,
        "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": False,
        "import_materials": False,
        "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    static_data = options.get_editor_property("static_mesh_import_data")
    static_data.set_editor_properties({
        "combine_meshes": True,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "generate_lightmap_u_vs": True,
        # UE 5.8 Interchange maps this legacy flag to the whole collision
        # pipeline. It must remain enabled for authored UCX hulls to import;
        # the exact 12-hull post-import gate below rejects fallback collision.
        "auto_generate_collision": True,
        "remove_degenerates": True,
        "one_convex_hull_per_ucx": True,
        # On a fresh legacy import ConvertSceneUnit performs the metre-to-cm
        # conversion. Keep uniform scale at one; applying 100 here double
        # converts the authored 1.5 m x 1.9 m source envelope.
        "import_uniform_scale": 1.0,
    })
    task.set_editor_property("options", options)
    tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

mesh = lib.load_asset(MESH_PATH)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(f"Could not import {MESH_PATH}")
imported_collision_counts = collision_counts(mesh)
simple_collision_count = imported_collision_counts["total"]
if simple_collision_count != 12:
    raise RuntimeError(f"Expected 12 imported UCX hulls, found {imported_collision_counts}")
body = mesh.get_editor_property("body_setup")
body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
body.modify()
mesh.modify()
lib.save_loaded_asset(mesh, only_if_is_dirty=False)
box = mesh.get_bounding_box()
bounds_cm = [box.max.x - box.min.x, box.max.y - box.min.y, box.max.z - box.min.z]
if not (149.0 <= bounds_cm[0] <= 151.0 and 189.0 <= bounds_cm[1] <= 191.0
        and 189.0 <= bounds_cm[2] <= 191.0):
    raise RuntimeError(f"Packaged-coil import scale gate failed: {bounds_cm}")


def material_instance(name, tint, roughness, texture_influence, normal_strength):
    path = f"{DEST}/{name}"
    instance = lib.load_asset(path)
    if instance is None:
        instance = tools.create_asset(
            name, DEST, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
    parent = lib.load_asset(WRAP_MASTER)
    if instance is None or parent is None:
        raise RuntimeError(f"Could not create {path}")
    instance.set_editor_property("parent", parent)
    mel.set_material_instance_vector_parameter_value(
        instance, "SurfaceTint", unreal.LinearColor(*tint))
    for parameter, value in {
        "TextureInfluence": texture_influence,
        "TextureScale": 11.0,
        "BaseRoughness": roughness,
        "RoughTextureInfluence": 0.24,
        "Metallic": 0.0,
        "NormalStrength": normal_strength,
    }.items():
        mel.set_material_instance_scalar_parameter_value(instance, parameter, value)
    mel.update_material_instance(instance)
    lib.save_loaded_asset(instance, only_if_is_dirty=False)
    return instance


materials = {
    "LB_MasterCoil_ProtectiveWrap_SatinGrey_v003": material_instance(
        "MI_LB_MasterCoil_SatinGreyWrap_v029", (0.16, 0.19, 0.22, 1.0), 0.78, 0.30, 0.16),
    "LB_MasterCoil_WrapOverlap_v003": material_instance(
        "MI_LB_MasterCoil_WrapOverlap_v029", (0.055, 0.070, 0.090, 1.0), 0.84, 0.26, 0.13),
    "LB_MasterCoil_WrapRepairPatch_v003": material_instance(
        "MI_LB_MasterCoil_WrapPatch_v029", (0.10, 0.15, 0.21, 1.0), 0.82, 0.28, 0.15),
    "LB_MasterCoil_CompressedEdgeProtector_v003": material_instance(
        "MI_LB_MasterCoil_CompressedFibre_v029", (0.24, 0.105, 0.030, 1.0), 0.92, 0.34, 0.22),
    "LB_MasterCoil_IDLabel_v003": material_instance(
        "MI_LB_MasterCoil_LabelPaper_v029", (0.58, 0.54, 0.43, 1.0), 0.84, 0.18, 0.07),
}
materials.update({
    "LB_MasterCoil_WoundSteel_v003": lib.load_asset(
        "/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_CoilSteel"),
    "LB_MasterCoil_BoreEdge_v003": lib.load_asset(
        "/Game/LineBoss/Materials/M_LB_StructureSteel"),
    "LB_MasterCoil_BlackSteelBand_v003": lib.load_asset(
        "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/M_LB_MasterCoil_Strap_v002"),
    "LB_MasterCoil_BandBuckle_v003": lib.load_asset(
        "/Game/LineBoss/Materials/M_LB_StructureSteel"),
    "LB_MasterCoil_LabelInk_v003": lib.load_asset(
        "/Game/LineBoss/Materials/M_LB_ShellCharcoal"),
})
if any(value is None for value in materials.values()):
    raise RuntimeError("One or more packaged-coil release materials are missing")

slots = mesh.get_editor_property("static_materials")
assigned_slots = []
for index, slot in enumerate(slots):
    slot_name = str(slot.get_editor_property("imported_material_slot_name")
                    or slot.get_editor_property("material_slot_name"))
    material = materials.get(slot_name)
    if material is None:
        raise RuntimeError(f"No explicit material assignment for slot {index}: {slot_name}")
    mesh.set_material(index, material)
    assigned_slots.append({"index": index, "slot": slot_name, "material": material.get_path_name()})
lib.save_loaded_asset(mesh, only_if_is_dirty=False)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

replaced = []
station_replaced = False
for actor in actors.get_all_level_actors():
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        old_mesh = component.get_editor_property("static_mesh")
        old_path = old_mesh.get_path_name() if old_mesh else ""
        if not ("SM_LB_MasterCoil_Candidate_v002" in old_path
                or old_path.startswith(OLD_TINY_MESH_PATH + ".")
                or old_path.startswith(MESH_PATH + ".")):
            continue
        component.set_static_mesh(mesh)
        for index, assignment in enumerate(assigned_slots):
            component.set_material(index, materials[assignment["slot"]])
        component.set_editor_property("can_ever_affect_navigation", False)
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        component.set_collision_profile_name(unreal.Name("BlockAll"))
        replaced.append({"actor": actor.get_actor_label(), "component": component.get_name()})
        if component.get_name() == "PR004_WrappedCoilVisual":
            station_replaced = True

if len(replaced) != 15 or not station_replaced:
    raise RuntimeError(f"Expected 15 packaged-coil replacements including native station, got {replaced}")

# Add a fresh high oblique camera that avoids the foreground column obscuring
# the bridge-width proof in the v028 views.
for existing_camera in list(actors.get_all_level_actors()):
    if existing_camera.get_actor_label().startswith("LB_PR004_V029_CAM_CraneSpanClear"):
        actors.destroy_actor(existing_camera)
camera = actors.spawn_actor_from_class(
    unreal.CameraActor, unreal.Vector(-1900.0, -5150.0, 1710.0), unreal.Rotator())
camera.set_actor_label("LB_PR004_V029_CAM_CraneSpanClear")
camera.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR004Crane.v029"),
               unreal.Name("LB.Asset.Candidate.v029"), unreal.Name("LB.Asset.CandidateNotPromoted")]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    camera.get_actor_location(), unreal.Vector(-5050.0, -2415.0, 1480.0)), False)
camera.camera_component.set_editor_properties({
    "field_of_view": 94.0,
    "aspect_ratio": 16.0 / 9.0,
    "constrain_aspect_ratio": True,
})

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-crane-load-candidate-v029/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "DETAILED_PACKAGED_LOAD_INTEGRATED__RUNTIME_AND_VISUAL_REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": BASE,
    "map": MAP,
    "asset": mesh.get_path_name(),
    "bounds_cm": bounds_cm,
    "render_triangles": source["render_mesh"]["triangles"],
    "material_slots": assigned_slots,
    "simple_collision_primitive_count": simple_collision_count,
    "simple_collision_primitives": imported_collision_counts,
    "collision_trace_flag": str(body.get_editor_property("collision_trace_flag")),
    "collision_clear_bore_mm": source["collision"]["minimum_clear_bore_mm"],
    "replaced_packaged_coil_components": replaced,
    "fixed_camera": camera.get_actor_label(),
    "runtime_gate": "OPEN",
    "collision_gate": "OPEN",
    "visual_gate": "OPEN",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_CRANE_LOAD_V029_BUILD_PASS replacements={len(replaced)} ucx={simple_collision_count} map={MAP}")
unreal.SystemLibrary.quit_editor()
