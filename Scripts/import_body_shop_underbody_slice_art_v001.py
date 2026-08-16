"""Guarded static-mesh intake for frozen Body Shop v001 art."""
from __future__ import annotations
import hashlib, json, traceback
from datetime import datetime, timezone
from pathlib import Path
import unreal

PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
SRC = PROJECT / "SourceAssets/Candidate/WeldShop/BodyShopUnderbodySlice_v001"
MANIFEST = SRC / "MANIFEST_v001.json"
FREEZE = SRC / "Audit/FROZEN_v001.json"
ROUNDTRIP = SRC / "Audit/roundtrip_validation_v001.json"
DEST = "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001"
DEST_DISK = PROJECT / "Content/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001"
STAGING = DEST + "/__LegacyLODStaging"
STAGING_DISK = DEST_DISK / "__LegacyLODStaging"
AUDIT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001"
RECEIPT = AUDIT / "import_underbody_slice_art_receipt_v001.json"
FAILURE = AUDIT / "import_underbody_slice_art_failure_v001.json"
NAMES = {"SM_LB_BodyShopRobot_Base_v001", "SM_LB_BodyShopRobot_J1_v001",
    "SM_LB_BodyShopRobot_J2_v001", "SM_LB_BodyShopRobot_J3_v001",
    "SM_LB_BodyShopRobot_J4_v001", "SM_LB_BodyShopRobot_J5_v001",
    "SM_LB_BodyShopTool_PanelPick8Cup_v001", "SM_LB_BodyShop_UnderbodyFixture_v001",
    "SM_LB_BodyShop_VisionGate_v001"}
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

def fail(text):
    raise RuntimeError("BODYSHOP_UNDERBODY_ART_IMPORT_V001_FAIL: " + text)

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1048576), b""):
            h.update(part)
    return h.hexdigest().upper()

def now(): return datetime.now(timezone.utc).isoformat()

def disk_asset(asset):
    return PROJECT / "Content" / Path(asset.replace("/Game/", "")).with_suffix(".uasset")

def content_fingerprint(skip_dest=True):
    root = PROJECT / "Content"; out = {}
    for p in root.rglob("*"):
        if not p.is_file(): continue
        if skip_dest:
            try:
                p.resolve().relative_to(DEST_DISK.resolve()); continue
            except ValueError: pass
        s = p.stat()
        out[str(p.relative_to(root)).replace("\\", "/")] = [s.st_size, s.st_mtime_ns]
    return out

def namespace_inventory():
    if not DEST_DISK.is_dir(): return {}
    out = {}
    for p in DEST_DISK.rglob("*"):
        if p.is_file():
            s = p.stat()
            out[str(p.relative_to(PROJECT / "Content")).replace("\\", "/")] = {"bytes":s.st_size, "sha256":digest(p)}
    return out

def verify_freeze():
    if not FREEZE.is_file(): fail("freeze manifest missing")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if freeze.get("status") != "FROZEN_SOURCE_DERIVATIVE__ROUNDTRIP_PASS__UNREAL_IMPORT_PENDING": fail("freeze is not approved")
    out = {}
    for row in freeze.get("files", []):
        rel = row.get("path", ""); p = SRC / rel
        actual = {"bytes": p.stat().st_size, "sha256": digest(p)} if p.is_file() else None
        if not actual or actual["bytes"] != row.get("bytes") or actual["sha256"] != str(row.get("sha256","")).upper():
            fail("frozen source drift: " + rel)
        out[rel] = actual
    if not out: fail("empty freeze inventory")
    return out

def source_contract():
    if PROJECT != EXPECTED_PROJECT: fail("wrong project path")
    if str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory": fail("wrong game name")
    if not MANIFEST.is_file() or not ROUNDTRIP.is_file(): fail("source manifest/report missing")
    m = json.loads(MANIFEST.read_text(encoding="utf-8")); r = json.loads(ROUNDTRIP.read_text(encoding="utf-8"))
    if m.get("asset_id") != "LB_BODYSHOP_UNDERBODY_SLICE_ART_V001" or m.get("status") != "FROZEN_SOURCE_DERIVATIVE__ROUNDTRIP_PASS__UNREAL_IMPORT_PENDING": fail("source identity/status drift")
    if m.get("unreal_content_intent") != DEST: fail("destination intent drift")
    if r.get("status") != "PASS" or not all(r.get("checks",{}).get(k) is True for k in ("source_authorities_unchanged","all_56_exports_present","all_fbx_and_glb_roundtrip","exact_eight_cups_and_sockets","j1_to_j5_hierarchy_nodes","j4_locked_initially","unreal_not_run","meshy_not_called")): fail("roundtrip evidence drift")
    return m, r

def expected_assets(m, r):
    bindings = m.get("unreal_import_bindings", {})
    if set(bindings) != NAMES: fail("binding inventory drift")
    rows = {x.get("file"):x for x in r.get("roundtrips", [])}
    out = {}
    for name, b in bindings.items():
        obj = b.get("object_path", "")
        if not obj.endswith("/" + name + "." + name): fail("object path drift: " + name)
        asset = obj.rsplit(".", 1)[0]
        if not asset.startswith(DEST + "/"): fail("asset escapes namespace: " + name)
        srcs = [SRC / b.get(k, "") for k in ("lod0_fbx", "lod1_fbx", "lod2_fbx")]
        if any(not p.is_file() for p in srcs): fail("missing FBX: " + name)
        roundtrip = [rows.get(p.name) for p in srcs]
        if any(x is None or int(x.get("triangles", -1)) <= 0 for x in roundtrip): fail("roundtrip LOD evidence drift: " + name)
        lod_dims = [[float(v)*100.0 for v in x.get("bounds_m", [])] for x in roundtrip]
        if any(len(dims) != 3 for dims in lod_dims): fail("roundtrip dimensions missing: " + name)
        out[name] = {"asset":asset,"object":obj,"folder":asset.rsplit("/",1)[0],"srcs":srcs,
                     "tris":[int(x["triangles"]) for x in roundtrip],"lod_dims":lod_dims}
    return out

def import_task(src, folder, name):
    task = unreal.AssetImportTask()
    task.set_editor_properties({"filename":str(src),"destination_path":folder,"destination_name":name,
        "automated":True,"async_":False,"replace_existing":False,"replace_existing_settings":False,"save":True})
    opt = unreal.FbxImportUI()
    opt.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,"import_materials":False,
        "import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type":False})
    data = opt.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({"combine_meshes":False,"convert_scene":True,"convert_scene_unit":True,
        "force_front_x_axis":False,"transform_vertex_to_absolute":True,"bake_pivot_in_vertex":False,
        "generate_lightmap_u_vs":False,"auto_generate_collision":False,"one_convex_hull_per_ucx":True,
        "build_nanite":False,"import_mesh_lods":False,
        # The frozen Base LOD0 contains thin authored surfaces.  Leaving the
        # legacy importer's removal threshold disabled preserves its validated
        # source triangle contract; this remains collision-free and Nanite-off.
        # The frozen FBX files declare metres.  Absolute vertex conversion
        # applies the FBX metre-to-centimetre scene transform exactly once;
        # uniform scale therefore stays at the neutral 1.0.
        "remove_degenerates":False,"import_uniform_scale":1.0})
    # UE 5.8 routes an un-specified factory through Interchange.  An explicit
    # FbxFactory is the documented AssetTools escape hatch to use the legacy
    # static-mesh FBX importer, which is the required intake path for v001.
    factory = unreal.FbxFactory()
    factory.set_editor_property("asset_import_task", task)
    task.factory = factory
    task.options = opt
    return task

def vec(v): return [float(v.x),float(v.y),float(v.z)]

def lod_bounds_cm(mesh, lod_index):
    dynamic_mesh = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    requested_lod = unreal.GeometryScriptMeshReadLOD()
    requested_lod.set_editor_properties({"lod_type":unreal.GeometryScriptLODType.SOURCE_MODEL,"lod_index":lod_index})
    dynamic_mesh, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic_mesh, options, requested_lod, False)
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        fail("source LOD bounds extraction failed: " + mesh.get_name() + ":" + str(lod_index) + ":" + str(outcome))
    box = dynamic_mesh.get_mesh_bounding_box(); mn, mx = vec(box.min), vec(box.max)
    return mn, mx, [mx[i] - mn[i] for i in range(3)]

def staging_spec(name, lod_index):
    stage_name = name + "__LegacySourceLOD" + str(lod_index)
    asset = STAGING + "/" + stage_name
    return {"name":stage_name,"asset":asset,"object":asset + "." + stage_name}

def import_legacy_sibling_lods(expected):
    staged = {}
    for name in sorted(expected):
        spec = expected[name]
        for lod_index in (1, 2):
            stage = staging_spec(name, lod_index)
            if lib.does_asset_exist(stage["asset"]): fail("staging freshness violation: " + stage["asset"])
            task = import_task(spec["srcs"][lod_index], STAGING, stage["name"])
            tools.import_asset_tasks([task])
            if stage["object"] not in [str(x) for x in task.imported_object_paths]:
                fail("legacy sibling LOD import result drift: " + name + ":" + str(lod_index) + ":" + str(task.imported_object_paths))
            unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
            staged[(name, lod_index)] = stage
    return staged

def transfer_legacy_sibling_lods(mesh, name, subsystem, staged):
    for lod_index in (1, 2):
        stage = staged[(name, lod_index)]
        source = lib.load_asset(stage["asset"])
        if not isinstance(source, unreal.StaticMesh) or source.get_path_name() != stage["object"]:
            fail("legacy staging source drift: " + name + ":" + str(lod_index))
        if subsystem.set_lod_from_static_mesh(mesh, lod_index, source, 0, True) != lod_index:
            fail("legacy sibling LOD transfer failed: " + name + ":" + str(lod_index))
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

def inspect_mesh(name, spec, subsystem, staged):
    mesh = lib.load_asset(spec["asset"])
    if not isinstance(mesh, unreal.StaticMesh): fail("missing static mesh: " + spec["asset"])
    if mesh.get_path_name() != spec["object"]: fail("object path drift: " + name)
    transfer_legacy_sibling_lods(mesh, name, subsystem, staged)
    if not subsystem.set_lod_screen_sizes(mesh, [1.0, .55, .25]): fail("LOD screen set failed: " + name)
    n = subsystem.get_nanite_settings(mesh); n.set_editor_property("enabled", False); subsystem.set_nanite_settings(mesh, n, True)
    body = mesh.get_editor_property("body_setup")
    if not body: fail("body setup missing: " + name)
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
    if not lib.save_loaded_asset(mesh, only_if_is_dirty=False): fail("mesh save failed: " + name)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    lods = int(mesh.get_num_lods()); tris = [int(mesh.get_num_triangles(i)) for i in range(lods)]
    if lods != 3 or tris != spec["tris"]: fail("LOD/triangle drift: " + name + ":" + str(tris))
    lod_bounds=[]
    for lod_index in range(3):
        mn, mx, dims = lod_bounds_cm(mesh, lod_index)
        delta=[dims[i]-spec["lod_dims"][lod_index][i] for i in range(3)]
        if max(abs(x) for x in delta) > .5:
            fail("scale/axis drift: " + name + ":LOD" + str(lod_index) + ":" + str(delta))
        lod_bounds.append({"lod":lod_index,"min_cm":[round(x,4) for x in mn],"max_cm":[round(x,4) for x in mx],
            "dimensions_cm":[round(x,4) for x in dims],"expected_dimensions_cm":[round(x,4) for x in spec["lod_dims"][lod_index]],
            "dimension_delta_cm":[round(x,5) for x in delta]})
    simple=int(subsystem.get_simple_collision_count(mesh)); convex=int(subsystem.get_convex_collision_count(mesh))
    if simple or convex: fail("unexpected collision: " + name + ":" + str([simple,convex]))
    enabled=bool(subsystem.get_nanite_settings(mesh).get_editor_property("enabled"))
    trace=str(body.get_editor_property("collision_trace_flag"))
    if enabled or "SIMPLE_AS_COMPLEX" not in trace.upper(): fail("Nanite/collision policy drift: " + name)
    slots=[]
    for i, slot in enumerate(mesh.get_editor_property("static_materials")):
        mat=mesh.get_material(i); path=mat.get_path_name() if mat else None
        if path and path.startswith(DEST+"/"): fail("unexpected material created: "+path)
        slots.append({"index":i,"slot":str(slot.get_editor_property("material_slot_name")),"material":path})
    import_data=mesh.get_editor_property("asset_import_data")
    try:
        import_scale=float(import_data.get_editor_property("import_uniform_scale"))
        absolute=bool(import_data.get_editor_property("transform_vertex_to_absolute"))
        remove=bool(import_data.get_editor_property("remove_degenerates"))
    except Exception as error:
        fail("legacy import-data unavailable: " + name + ":" + str(error))
    if abs(import_scale-1.0) > .0001 or not absolute or remove:
        fail("legacy import-data policy drift: " + name + ":" + str([import_scale,absolute,remove]))
    return mesh, {"asset":mesh.get_path_name(),"lod_count":lods,"triangles":tris,
        "vertices":[int(mesh.get_num_vertices(i)) for i in range(lods)],
        "lod_bounds_cm":lod_bounds,
        "material_slots":slots,"simple_collision_count":simple,"convex_collision_count":convex,
        "collision_trace_flag":trace,"nanite_enabled":enabled,
        "legacy_import_data":{"import_uniform_scale":import_scale,"transform_vertex_to_absolute":absolute,
            "remove_degenerates":remove}}

def cleanup_staging(staged):
    staged_paths=[stage["asset"] for _,stage in sorted(staged.items())]
    for asset in staged_paths:
        if not lib.does_asset_exist(asset): fail("staging asset vanished before cleanup: " + asset)
    for asset in staged_paths:
        if not lib.delete_asset(asset): fail("staging cleanup failed: " + asset)
    leftovers=lib.list_assets(STAGING,recursive=True,include_folder=False)
    if leftovers: fail("staging registry cleanup drift: " + str(leftovers))
    disk_leftovers=[]
    if STAGING_DISK.exists():
        disk_leftovers=[str(x.relative_to(PROJECT / "Content")).replace("\\","/") for x in STAGING_DISK.rglob("*") if x.is_file()]
    if disk_leftovers: fail("staging disk cleanup drift: " + str(disk_leftovers))
    return {"legacy_fbx_sibling_staging_assets_removed":len(staged_paths),"staging_namespace":STAGING,
        "staging_registry_leftovers":[],"staging_disk_leftovers":[]}

def main():
    before_content=content_fingerprint(); evidence={"$schema":"lineboss/audit/bodyshop/experimental-v001-underbody-art-import/v1",
        "generated_utc":now(),"destination_namespace":DEST,"map_changes":[],"runtime_binding_changes":[],
        "source_assets_mutated":False,"meshy_credits_used_by_codex":0,
        "import_settings":{"legacy_fbx_static_importer":True,"materials_imported":False,"textures_imported":False,
            "combine_meshes":False,"skeletal":False,"animations":False,"nanite":False,
            "collision":"NO_AUTHORED_COLLISION__SIMPLE_AS_COMPLEX"}}
    try:
        manifest,roundtrip=source_contract(); frozen_before=verify_freeze(); expected=expected_assets(manifest,roundtrip)
        evidence.update({"source_manifest_sha256":digest(MANIFEST),"freeze_manifest_sha256":digest(FREEZE),
            "roundtrip_report_sha256":digest(ROUNDTRIP),"frozen_source_hashes_before":frozen_before})
        if DEST_DISK.exists() or lib.does_directory_exist(DEST): fail("destination namespace exists; refusing overwrite")
        if RECEIPT.exists(): fail("approved receipt exists while destination is not fresh")
        for name in sorted(expected):
            spec=expected[name]
            if lib.does_asset_exist(spec["asset"]): fail("freshness violation: "+spec["asset"])
            task=import_task(spec["srcs"][0],spec["folder"],name); tools.import_asset_tasks([task])
            if spec["object"] not in [str(x) for x in task.imported_object_paths]: fail("LOD0 import result drift: "+name+":"+str(task.imported_object_paths))
            unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        subsystem=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        if not subsystem: fail("StaticMeshEditorSubsystem unavailable")
        staged=import_legacy_sibling_lods(expected)
        mesh_rows={}
        for name in sorted(expected):
            _,mesh_rows[name]=inspect_mesh(name,expected[name],subsystem,staged)
        staging_cleanup=cleanup_staging(staged)
        registry=set(lib.list_assets(DEST,recursive=True,include_folder=False)); wanted={x["asset"] for x in expected.values()}
        if registry != wanted: fail("asset registry inventory drift: "+str(sorted(registry)))
        inventory=namespace_inventory(); actual={x for x in inventory if x.lower().endswith(".uasset")}
        wanted_disk={str(disk_asset(x["asset"]).relative_to(PROJECT/"Content")).replace("\\","/") for x in expected.values()}
        if actual != wanted_disk: fail("on-disk package inventory drift: "+str(sorted(actual)))
        if content_fingerprint() != before_content: fail("Content outside destination changed")
        frozen_after=verify_freeze()
        if frozen_after != frozen_before: fail("frozen source changed during import")
        evidence.update({"status":"PASS__FRESH_GUARDED_BODYSHOP_UNDERBODY_ART_INTAKE_V001",
            "source_manifest_status":manifest.get("status"),"frozen_source_hashes_after":frozen_after,
            "assets":mesh_rows,"asset_packages":inventory,
            "expected_object_paths":{n:expected[n]["object"] for n in sorted(expected)},
            "hierarchy_proof_excluded":"Exports/LB_BodyShopRobot_WithPanelPick8Cup_Hierarchy_v001.fbx",
            "legacy_lod_import_policy":{"all_27_fbx_imports":"FbxFactory legacy static mesh importer",
                "lod0_imports":9,"sibling_lod_imports":18,"lod_transfer":"set_lod_from_static_mesh from legacy-imported staging assets",
                "interchange_cvars_changed":False,"cvar_restore_required":False},"legacy_staging_cleanup":staging_cleanup,
            "unintended_content_mutations":[],"failures":[]})
        AUDIT.mkdir(parents=True,exist_ok=True); RECEIPT.write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
        unreal.log("LINE_BOSS_BODYSHOP_UNDERBODY_ART_IMPORT_V001_PASS"); print(json.dumps(evidence,indent=2))
    except Exception as error:
        AUDIT.mkdir(parents=True,exist_ok=True)
        record={"$schema":"lineboss/audit/bodyshop/experimental-v001-underbody-art-import-failure/v1",
            "generated_utc":now(),"status":"FAIL_CLOSED__BODYSHOP_UNDERBODY_ART_IMPORT_V001",
            "destination_namespace":DEST,"error":str(error),"traceback":traceback.format_exc(),
            "namespace_files_preserved_for_inspection":namespace_inventory(),
            "outside_content_changed":content_fingerprint()!=before_content,
            "automatic_cleanup":"NOT_PERFORMED__partial artifacts preserved for explicit review",
            "map_changes":[],"runtime_binding_changes":[],"source_assets_mutated":False,"meshy_credits_used_by_codex":0,
            "legacy_lod_import_policy":{"all_27_fbx_imports":"FbxFactory legacy static mesh importer",
                "interchange_cvars_changed":False,"cvar_restore_required":False}}
        FAILURE.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8"); print(json.dumps(record,indent=2)); raise

if __name__ == "__main__": main()
