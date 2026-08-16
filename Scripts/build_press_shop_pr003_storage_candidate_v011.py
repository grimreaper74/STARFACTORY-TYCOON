"""Build an isolated PR-003 release-art candidate from the accepted v006 map.

Imports the independently validated packaged-coil v003 and 30 t saddle v002
FBXs, applies controlled existing Unreal materials, then swaps only tagged
front-end coil/saddle StaticMeshActors.  Anchors, transforms, inventory tags,
PR-004 lighting and all other map content remain unchanged.
"""

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
DEST_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003StorageCandidate_v011"
DEST_ROOT = "/Game/LineBoss/IndustrialKit/MaterialHandling/PR003Candidate_v011"
AUDIT = ROOT / "Saved/Audits/press_shop_pr003_storage_candidate_v011.json"

SPECS = {
    "coil": {
        "source": ROOT / "SourceAssets/IndustrialKit/MasterCoil/SM_LB_MasterCoil_Candidate_v003.fbx",
        "name": "SM_LB_MasterCoil_Candidate_v003",
        "tag": "LB.Material.MasterCoil",
        "materials": {
            "woundsteel": "/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_CoilSteel.M_PR005_CoilSteel",
            "boreedge": "/Game/LineBoss/Materials/M_LB_StructureSteel.M_LB_StructureSteel",
            "protectivewrap": "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/M_LB_MasterCoil_SilverWrap_v002.M_LB_MasterCoil_SilverWrap_v002",
            "wrapoverlap": "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/M_LB_MasterCoil_SilverWrap_v002.M_LB_MasterCoil_SilverWrap_v002",
            "wraprepairpatch": "/Game/LineBoss/Materials/M_LB_ShellCharcoal.M_LB_ShellCharcoal",
            "blacksteelband": "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/M_LB_MasterCoil_Strap_v002.M_LB_MasterCoil_Strap_v002",
            "edgeprotector": "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/M_LB_MasterCoil_Cardboard_v002.M_LB_MasterCoil_Cardboard_v002",
            "bandbuckle": "/Game/LineBoss/Materials/M_LB_StructureSteel.M_LB_StructureSteel",
            "idlabel": "/Game/LineBoss/Materials/M_LB_FactoryConcrete.M_LB_FactoryConcrete",
            "labelink": "/Game/LineBoss/Materials/M_LB_ShellCharcoal.M_LB_ShellCharcoal",
        },
    },
    "saddle": {
        "source": ROOT / "SourceAssets/IndustrialKit/CoilSaddle/SM_LB_CoilSaddle_Candidate_v002.fbx",
        "name": "SM_LB_CoilSaddle_Candidate_v002",
        "tag": "LB.Module.CoilSaddle",
        "materials": {
            "framecharcoal": "/Game/LineBoss/Materials/M_LB_ShellCharcoal.M_LB_ShellCharcoal",
            "loadshoesteel": "/Game/LineBoss/Materials/M_LB_StructureSteel.M_LB_StructureSteel",
            "replaceablerubber": "/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_Rubber.M_PR005_Rubber",
            "safetyyellow": "/Game/LineBoss/Materials/M_LB_SafetyYellow.M_LB_SafetyYellow",
            "hightensilefastener": "/Game/LineBoss/Materials/M_LB_StructureSteel.M_LB_StructureSteel",
            "ratingplate": "/Game/LineBoss/Materials/M_LB_FactoryConcrete.M_LB_FactoryConcrete",
            "ratingplateink": "/Game/LineBoss/Materials/M_LB_ShellCharcoal.M_LB_ShellCharcoal",
        },
    },
}


def import_mesh(spec):
    if not spec["source"].is_file():
        raise RuntimeError(f"Missing FBX source {spec['source']}")
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(spec["source"]), "destination_path": DEST_ROOT,
        "destination_name": spec["name"], "automated": True,
        "replace_existing": True, "replace_existing_settings": True,
        "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False,
        "import_materials": False, "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "force_front_x_axis": False, "generate_lightmap_u_vs": True,
        "auto_generate_collision": True, "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    mesh = unreal.load_asset(f"{DEST_ROOT}/{spec['name']}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Import did not produce StaticMesh {spec['name']}")
    assignments = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
        key = next((key for key in spec["materials"] if key in slot_name.lower().replace("_", "")), None)
        if key is None:
            raise RuntimeError(f"Unmapped material slot {slot_name} on {spec['name']}")
        material = unreal.load_asset(spec["materials"][key])
        if material is None:
            raise RuntimeError(f"Missing controlled material {spec['materials'][key]}")
        mesh.set_material(index, material)
        assignments.append({"slot": slot_name, "material": material.get_path_name()})
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    bounds = mesh.get_bounding_box()
    return mesh, assignments, [bounds.max.x-bounds.min.x, bounds.max.y-bounds.min.y, bounds.max.z-bounds.min.z]


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level("/Game/LineBoss/Maps/LB_PressShop_Foundation")
if unreal.EditorAssetLibrary.does_asset_exist(DEST_MAP):
    raise RuntimeError(f"Refusing to overwrite preserved candidate {DEST_MAP}")

imported = {}
for kind, spec in SPECS.items():
    mesh, assignments, bounds = import_mesh(spec)
    imported[kind] = {"mesh": mesh, "materials": assignments, "bounds_cm": bounds}

if not unreal.EditorAssetLibrary.duplicate_asset(BASE_MAP, DEST_MAP):
    raise RuntimeError(f"Could not duplicate {BASE_MAP}")
if not levels.load_level(DEST_MAP):
    raise RuntimeError(f"Could not load {DEST_MAP}")

replaced = {"coil": [], "saddle": []}
for actor in actors.get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    tags = {str(tag) for tag in actor.tags}
    kind = next((key for key, spec in SPECS.items() if spec["tag"] in tags), None)
    if kind is None:
        continue
    component = actor.get_editor_property("static_mesh_component")
    before = component.get_editor_property("static_mesh")
    component.set_editor_property("static_mesh", imported[kind]["mesh"])
    replaced[kind].append({
        "actor": actor.get_actor_label(),
        "before": before.get_path_name() if before else None,
        "after": imported[kind]["mesh"].get_path_name(),
        "location_cm": list(actor.get_actor_location().to_tuple()),
        "rotation_deg": list(actor.get_actor_rotation().to_tuple()),
        "tags": sorted(tags),
    })

if len(replaced["coil"]) != 15 or len(replaced["saddle"]) != 16:
    raise RuntimeError(f"Unexpected replacement counts { {key: len(value) for key, value in replaced.items()} }")
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {DEST_MAP}")

result = {
    "$schema": "line-boss/audit/press-shop-pr003-storage-candidate/v1",
    "status": "CANDIDATE_NOT_PROMOTED__FRESH_VISUAL_REVIEW_REQUIRED",
    "base_map": BASE_MAP, "map": DEST_MAP,
    "station_anchors_modified": False, "actor_transforms_modified": False,
    "replacement_counts": {key: len(value) for key, value in replaced.items()},
    "imports": {key: {"asset": value["mesh"].get_path_name(), "bounds_cm": value["bounds_cm"], "materials": value["materials"]} for key, value in imported.items()},
    "replaced": replaced, "promotion_supported": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR003_STORAGE_V011_PASS coils={len(replaced['coil'])} saddles={len(replaced['saddle'])}")
unreal.SystemLibrary.quit_editor()
