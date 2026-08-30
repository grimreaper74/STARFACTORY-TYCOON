"""Fail-closed native import of Claude's Material Flow RuntimePrep v001.

The Material Flow pack is an immutable source handoff.  This lane imports its
six FBXs as ten independent static meshes (``combine_meshes=False``) so the
two approved mover pivots remain useful at runtime.  It deliberately reuses
the already-audited StagePack PBR master, its nine shared material instances,
and its byte-identical texture families; only the four genuinely new families
are imported and instanced locally.

This script never opens or saves a map, never writes under ArtSource, never
imports FBX-provided materials or textures, never creates collision, and
refuses to touch an existing native destination or receipt.  A successful
receipt is the sole evidence it writes.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
from pathlib import Path

import unreal


PROJECT_ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
SOURCE_ASSET_DIR = PROJECT_ROOT / "ArtSource/Claude_PressShop_MaterialFlowPack_v001"
SOURCE_PREP_DIR = PROJECT_ROOT / "ArtSource/Claude_PressShop_MaterialFlowPack_RuntimePrep_v001"
SOURCE_MANIFEST = SOURCE_ASSET_DIR / "matflowpack_manifest.json"
SOURCE_TEXTURE_MANIFEST = SOURCE_ASSET_DIR / "texture_material_manifest.json"
SOURCE_RUNTIME_STATS = SOURCE_PREP_DIR / "runtime_prep_stats.json"
SOURCE_PAYLOAD_AUDIT = (
    PROJECT_ROOT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v001/"
    "fbx_payload_audit_retry1.json"
)

SHARED_DESTINATION = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "SharedTrainModules_v003"
)
SHARED_TEXTURE_DESTINATION = SHARED_DESTINATION + "/Textures"
SHARED_MATERIAL_DESTINATION = SHARED_DESTINATION + "/Materials"
SHARED_IMPORT_RECEIPT = (
    PROJECT_ROOT / "Saved/Audits/OneFactory/Press/S03S06StagePackRuntimePrep_v001/"
    "import_receipt.json"
)
SHARED_SOURCE_ASSET_DIR = PROJECT_ROOT / "ArtSource/Claude_S03S06_StagePack_v001"
SHARED_SOURCE_PREP_DIR = PROJECT_ROOT / "ArtSource/Claude_S03S06_StagePack_RuntimePrep_v001"
SHARED_SOURCE_TEXTURE_MANIFEST = (
    SHARED_SOURCE_ASSET_DIR / "texture_material_manifest.json"
)

DESTINATION = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "MaterialFlowPack_v001"
)
MESH_DESTINATION = DESTINATION + "/Meshes"
TEXTURE_DESTINATION = DESTINATION + "/Textures"
MATERIAL_DESTINATION = DESTINATION + "/Materials"
AUDIT_DIR = (
    PROJECT_ROOT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v001"
)
RECEIPT = AUDIT_DIR / "import_receipt.json"


SOURCE_BLEND_SHA256 = "7666d2d524bb58cd3c5ad0f5537d63128ca88868731c5a5004956e734667faf1"
COORDINATE_SYSTEM = (
    "+X across train, +Y material flow, +Z up; metres; operator -X, service +X; "
    "NO baked yaw"
)
CHANNELS = ("BC", "N", "ORM", "MASK")
SHARED_FAMILIES = (
    "CairnwellGreen", "FoundryCharcoal", "ServiceGrey", "SafetyYellow",
    "WorkedSteel", "InspectionGlass", "TrainAAccent", "StatusGreen",
    "StatusAmber",
)
NEW_FAMILIES = (
    "GalvanizedCoil", "DarkRubber", "TaskLightGlass", "StampedPanel",
)
ALL_FAMILIES = SHARED_FAMILIES + NEW_FAMILIES
TEXTURE_PARAMETERS = {
    "BaseColorMap": "BC",
    "NormalMap": "N",
    "ORMMap": "ORM",
    "WearMaskMap": "MASK",
}
MASTER_NAME = "M_CA_MW_PT_StagePack_PBR_Master_v001"
MASTER_PATH = (
    f"{SHARED_MATERIAL_DESTINATION}/{MASTER_NAME}.{MASTER_NAME}"
)

# The source manifest has no approved runtime dust scalar for these new
# families.  Preserve the master default rather than inventing a weathering
# treatment at integration time.
NEW_FAMILY_DUST = {family: 0.0 for family in NEW_FAMILIES}

# This is deliberately a concrete import contract rather than a discovery
# pass.  The source manifest and RuntimePrep stats must agree with it before
# the first native asset is created.
EXPECTED_MODULES = {
    "FeedCoilAssembly": {
        "file": "CA_PTA_S01_FeedCoilAssembly_LOD0.fbx",
        "station": "S01",
        "placement_slot_cm": (0, -4350, 0),
        "meshes": (
            "SM_CA_MW_PT_S01CoilCart_v001",
            "SM_CA_MW_PT_S01CoilRack_v001",
            "SM_CA_MW_PT_S01DecoilerBase_v001",
            "SM_CA_MW_PT_S01DecoilerSpindle_v001",
        ),
    },
    "StraightenerServoFeed": {
        "file": "CA_PTA_S01_StraightenerServoFeed_LOD0.fbx",
        "station": "S01",
        "placement_slot_cm": (0, -4350, 0),
        "meshes": ("SM_CA_MW_PT_S01StraightenerFeed_v001",),
    },
    "S01FeedBridge": {
        "file": "CA_PTA_S01_FeedBridge_LOD0.fbx",
        "station": "S01",
        "placement_slot_cm": (0, -4350, 0),
        "meshes": ("SM_CA_MW_PT_S01FeedBridge_v001",),
    },
    "S07ExitConveyor": {
        "file": "CA_PTA_S07_ExitConveyor_LOD0.fbx",
        "station": "S07",
        "placement_slot_cm": (0, 4350, 0),
        "meshes": (
            "SM_CA_MW_PT_S07ExitConveyorBelt_v001",
            "SM_CA_MW_PT_S07ExitConveyorFrame_v001",
        ),
    },
    "InspectionCell": {
        "file": "CA_PTA_S07_InspectionCell_LOD0.fbx",
        "station": "S07",
        "placement_slot_cm": (0, 4350, 0),
        "meshes": ("SM_CA_MW_PT_S07InspectionCell_v001",),
    },
    "OutboundDunnage": {
        "file": "CA_PTA_S07_OutboundDunnage_LOD0.fbx",
        "station": "S07",
        "placement_slot_cm": (0, 4350, 0),
        "meshes": ("SM_CA_MW_PT_S07OutboundDunnage_v001",),
    },
}
EXPECTED_TRIANGLES = {
    "SM_CA_MW_PT_S01CoilCart_v001": 300,
    "SM_CA_MW_PT_S01CoilRack_v001": 604,
    "SM_CA_MW_PT_S01DecoilerBase_v001": 132,
    "SM_CA_MW_PT_S01DecoilerSpindle_v001": 452,
    "SM_CA_MW_PT_S01StraightenerFeed_v001": 556,
    "SM_CA_MW_PT_S01FeedBridge_v001": 144,
    "SM_CA_MW_PT_S07ExitConveyorBelt_v001": 24,
    "SM_CA_MW_PT_S07ExitConveyorFrame_v001": 908,
    "SM_CA_MW_PT_S07InspectionCell_v001": 252,
    "SM_CA_MW_PT_S07OutboundDunnage_v001": 420,
}
MOVER_MESHES = {
    "SM_CA_MW_PT_S01CoilCart_v001": {
        "pivot": "cart deck centre",
        "parked_offset_m": (2.2, -4.3, 0.32),
        "motion": "local Y, 0 to +3.2 m (coil rack line to decoiler transfer); "
        "parked at rack end; coil loading from rack is by overhead crane "
        "(authority: 8 m hook clearance)",
    },
    "SM_CA_MW_PT_S01DecoilerSpindle_v001": {
        "pivot": "mandrel axis at pedestal face",
        "parked_offset_m": (-0.2, -1.2, 1.15),
        "motion": "continuous rotation about local X (strip pays off over top toward +Y); "
        "no end stops",
    },
}
SLOT_SUFFIX = re.compile(r"\.\d{3}$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().lower()


def read_json(path: Path) -> dict:
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as error:
        fail("cannot read JSON authority {}: {}".format(path, error))
    raise AssertionError("fail() must raise")


def fail(message: str) -> None:
    raise RuntimeError("Material Flow RuntimePrep v001 import failed: {}".format(message))


def object_path(folder: str, name: str) -> str:
    return "{0}/{1}.{1}".format(folder, name)


def package_path(object_path_value: str) -> str:
    return object_path_value.rsplit(".", 1)[0]


def asset_path(asset) -> str:
    return str(asset.get_path_name()) if asset else "none"


def texture_name(family: str, channel: str) -> str:
    return "T_CA_MW_PT_{}_{}".format(family, channel)


def material_name(family: str) -> str:
    return "MI_CA_MW_PT_{}_v001".format(family)


def semantic_slot(family: str) -> str:
    return "CA_MW_{}".format(family)


def normalise_terminal_blender_slot_suffix(raw_name) -> str:
    """Remove only Blender's terminal .ddd duplicate suffix.

    The runtime FBXs were authored separately, so Blender has appended local
    duplicate material aliases in several files (for example
    ``CA_MW_FoundryCharcoal.004``).  Only that terminal three-digit suffix is
    an import-local alias.  Names with any other difference must fail later
    against the source semantic contract.
    """
    return SLOT_SUFFIX.sub("", str(raw_name))


def tuple3(value, label: str) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        fail("{} must be a three-value vector, got {}".format(label, value))
    return tuple(float(item) for item in value)


def exact_list(value, expected, label: str) -> None:
    if list(value) != list(expected):
        fail("{} drifted: got {}, expected {}".format(label, value, expected))


def source_texture_specs(texture_manifest: dict) -> dict[str, dict[str, dict]]:
    families = texture_manifest.get("families", {})
    if set(families) != set(ALL_FAMILIES):
        fail("texture family contract drifted: {}".format(sorted(families)))
    result: dict[str, dict[str, dict]] = {}
    for family in ALL_FAMILIES:
        family_row = families[family]
        if family_row.get("material_slot") != semantic_slot(family):
            fail("{} material-slot contract drifted".format(family))
        provenance = str(family_row.get("provenance", ""))
        if family in SHARED_FAMILIES:
            if not provenance.startswith(
                    "reused - regenerated byte-identical to the S03-S06 stage pack family"):
                fail("{} no longer declares byte-identical StagePack reuse".format(family))
        elif provenance != "newly authored for this pack":
            fail("{} no longer declares itself a newly authored Material Flow family".format(
                family))
        maps = family_row.get("maps", {})
        if set(maps) != set(CHANNELS):
            fail("{} texture channels drifted: {}".format(family, sorted(maps)))
        result[family] = {}
        for channel in CHANNELS:
            map_row = maps[channel]
            relative_file = map_row.get("file")
            expected_name = texture_name(family, channel) + ".png"
            if relative_file != "Textures/{}".format(expected_name):
                fail("{} {} texture path drifted: {}".format(
                    family, channel, relative_file))
            source_path = SOURCE_ASSET_DIR / relative_file
            source_hash = str(map_row.get("sha256", "")).lower()
            if not re.fullmatch(r"[0-9a-f]{64}", source_hash):
                fail("{} {} texture manifest hash is invalid".format(family, channel))
            if not source_path.is_file():
                fail("{} {} source texture is missing: {}".format(
                    family, channel, source_path))
            actual_hash = sha256(source_path)
            if actual_hash != source_hash:
                fail("{} {} source texture hash drifted".format(family, channel))
            result[family][channel] = {
                "family": family,
                "channel": channel,
                "source_path": source_path,
                "source_sha256": source_hash,
                "asset_name": texture_name(family, channel),
            }
    return result


def validate_shared_texture_equality(
        material_flow_textures: dict[str, dict[str, dict]],
        stage_texture_manifest: dict,
) -> dict[str, dict[str, dict]]:
    """Prove all nine reused source maps are byte-identical to StagePack."""
    if stage_texture_manifest.get("asset_pack") != "CA_PTA_S03S06_StagePack_v001":
        fail("shared StagePack texture manifest is not its approved v001 authority")
    stage_families = stage_texture_manifest.get("families", {})
    if set(stage_families) != set(SHARED_FAMILIES):
        fail("shared StagePack texture family contract drifted")
    equality = {}
    for family in SHARED_FAMILIES:
        stage_row = stage_families[family]
        if stage_row.get("material_slot") != semantic_slot(family):
            fail("shared StagePack {} slot contract drifted".format(family))
        stage_maps = stage_row.get("maps", {})
        if set(stage_maps) != set(CHANNELS):
            fail("shared StagePack {} map contract drifted".format(family))
        equality[family] = {}
        for channel in CHANNELS:
            stage_map = stage_maps[channel]
            stage_relative = stage_map.get("file")
            expected_relative = "Textures/{}.png".format(texture_name(family, channel))
            if stage_relative != expected_relative:
                fail("shared StagePack {} {} map path drifted".format(family, channel))
            stage_hash = str(stage_map.get("sha256", "")).lower()
            source_hash = material_flow_textures[family][channel]["source_sha256"]
            if stage_hash != source_hash:
                fail("{} {} is not byte-identical to the StagePack source map".format(
                    family, channel))
            stage_path = SHARED_SOURCE_ASSET_DIR / stage_relative
            if not stage_path.is_file() or sha256(stage_path) != stage_hash:
                fail("shared StagePack {} {} source map drifted".format(family, channel))
            equality[family][channel] = {
                "material_flow_source": str(
                    material_flow_textures[family][channel]["source_path"]),
                "stagepack_source": str(stage_path),
                "sha256": source_hash,
                "byte_identical": True,
            }
    return equality


def validate_context_fbx_hashes(source_manifest: dict) -> dict[str, str]:
    context_hashes = source_manifest.get("context_fbx_sha256", {})
    expected_names = {
        "CA_PTA_S03_Frame_Form_LOD0.fbx",
        "CA_PTA_S03_Cue_SecondaryForm_LOD0.fbx",
        "CA_PTA_S04_Frame_Trim_LOD0.fbx",
        "CA_PTA_S04_Cue_TrimScrap_LOD0.fbx",
        "CA_PTA_S05_Frame_Pierce_LOD0.fbx",
        "CA_PTA_S05_Cue_PierceSlug_LOD0.fbx",
        "CA_PTA_S06_Frame_Flange_LOD0.fbx",
        "CA_PTA_S06_Cue_RestrikeQuality_LOD0.fbx",
    }
    if set(context_hashes) != expected_names:
        fail("StagePack render-context FBX set drifted")
    result = {}
    for filename in sorted(expected_names):
        expected_hash = str(context_hashes[filename]).lower()
        path = SHARED_SOURCE_PREP_DIR / filename
        if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            fail("render-context hash is invalid for {}".format(filename))
        if not path.is_file() or sha256(path) != expected_hash:
            fail("render-context FBX hash drifted for {}".format(filename))
        result[filename] = expected_hash
    return result


def validate_source_contract(
        source_manifest: dict,
        texture_manifest: dict,
        runtime_stats: dict,
        payload_audit: dict,
) -> tuple[
        dict[str, dict[str, dict]],
        dict[str, dict[str, dict]],
        dict[str, str],
        dict[str, str],
]:
    if source_manifest.get("asset_pack") != "CA_PressShop_MaterialFlowPack_v001":
        fail("source manifest is not the declared Material Flow v001 authority")
    if source_manifest.get("coordinate_system") != COORDINATE_SYSTEM:
        fail("source manifest coordinate-system contract drifted")
    if runtime_stats.get("coordinate_system") != COORDINATE_SYSTEM:
        fail("RuntimePrep coordinate-system contract drifted")
    if runtime_stats.get("source_blend_sha256") != SOURCE_BLEND_SHA256:
        fail("RuntimePrep source blend provenance drifted")
    source_blend = SOURCE_ASSET_DIR / "CA_PressShop_MaterialFlowPack_v001.blend"
    if not source_blend.is_file() or sha256(source_blend) != SOURCE_BLEND_SHA256:
        fail("source blend is missing or has drifted from RuntimePrep provenance")
    if texture_manifest.get("asset_pack") != "CA_PressShop_MaterialFlowPack_v001":
        fail("texture manifest is not the declared Material Flow v001 authority")
    if runtime_stats.get("uv_channels") != [
            "UVMap (tiling, 1 UV tile per 2 m)",
            "UV_Unique (non-overlapping, re-packed per mesh here)",
    ]:
        fail("RuntimePrep top-level UV contract drifted")
    if "negates Y" not in str(runtime_stats.get("convert_scene_note", "")):
        fail("RuntimePrep Convert Scene placement note is missing")

    expected_slots = {
        "S01": [0, -4350, 0],
        "S02_reserved": [0, -2900, 0],
        "S07": [0, 4350, 0],
    }
    if source_manifest.get("station_slots_source_cm") != expected_slots:
        fail("source station-slot contract drifted")
    if runtime_stats.get("station_slots_source_cm") != expected_slots:
        fail("RuntimePrep station-slot contract drifted")

    reconstruction = runtime_stats.get("reconstruction", {})
    if reconstruction.get("exported_triangles_total") != 3792:
        fail("RuntimePrep does not record the approved 3,792 exported triangles")
    if reconstruction.get("triangles_match_source") is not True:
        fail("RuntimePrep does not record source triangle conservation")
    if reconstruction.get("per_station_bounds_error_m") != {"S01": 0.0, "S07": 0.0}:
        fail("RuntimePrep reconstruction is not zero-error for both station groups")

    if payload_audit.get("status") != "PASS__MATERIAL_FLOW_FBX_PAYLOAD_MATCHES_RUNTIMEPREP":
        fail("the required retry1 FBX payload audit is not a pass")
    if payload_audit.get("failures") != []:
        fail("the required retry1 FBX payload audit records failures")
    if payload_audit.get("published_exported_triangles_total") != 3792:
        fail("payload audit publication total drifted")
    if payload_audit.get("audited_exported_triangles_total") != 3792:
        fail("payload audit does not prove 3,792 actual FBX triangles")
    if payload_audit.get("source_runtimeprep_stats_sha256") != sha256(SOURCE_RUNTIME_STATS):
        fail("payload audit does not correspond to the current RuntimePrep stats")

    source_modules = source_manifest.get("modules", {})
    runtime_modules = runtime_stats.get("modules", {})
    if set(source_modules) != set(EXPECTED_MODULES):
        fail("source module set drifted: {}".format(sorted(source_modules)))
    if set(runtime_modules) != set(EXPECTED_MODULES):
        fail("RuntimePrep module set drifted: {}".format(sorted(runtime_modules)))

    mesh_specs: dict[str, dict] = {}
    module_hashes: dict[str, str] = {}
    for module_name, module_contract in EXPECTED_MODULES.items():
        source_module = source_modules[module_name]
        runtime_module = runtime_modules[module_name]
        if source_module.get("station") != module_contract["station"]:
            fail("source {} station contract drifted".format(module_name))
        if runtime_module.get("station") != module_contract["station"]:
            fail("RuntimePrep {} station contract drifted".format(module_name))
        exact_list(runtime_module.get("placement_slot_cm", ()),
                   module_contract["placement_slot_cm"],
                   "RuntimePrep {} placement".format(module_name))
        exact_list(runtime_module.get("rotation", ()), (0, 0, 0),
                   "RuntimePrep {} rotation".format(module_name))
        if runtime_module.get("file") != module_contract["file"]:
            fail("RuntimePrep {} FBX name drifted".format(module_name))
        fbx_path = SOURCE_PREP_DIR / module_contract["file"]
        fbx_hash = str(runtime_module.get("fbx_sha256", "")).lower()
        if not re.fullmatch(r"[0-9a-f]{64}", fbx_hash):
            fail("RuntimePrep {} FBX hash is invalid".format(module_name))
        if not fbx_path.is_file() or sha256(fbx_path) != fbx_hash:
            fail("RuntimePrep {} FBX hash drifted".format(module_name))
        module_hashes[module_name] = fbx_hash

        source_meshes = source_module.get("meshes", {})
        runtime_meshes = runtime_module.get("meshes", {})
        if set(source_meshes) != set(module_contract["meshes"]):
            fail("source {} mesh set drifted".format(module_name))
        if set(runtime_meshes) != set(module_contract["meshes"]):
            fail("RuntimePrep {} mesh set drifted".format(module_name))
        for mesh_name in module_contract["meshes"]:
            source_mesh = source_meshes[mesh_name]
            runtime_mesh = runtime_meshes[mesh_name]
            # These fields are source-verifiable rather than visual estimates.
            for field in (
                    "local_aabb_min_m", "local_aabb_max_m", "material_slots",
                    "triangles", "uv_layers", "root",
            ):
                if source_mesh.get(field) != runtime_mesh.get(field):
                    fail("{} {} {} differs between source and RuntimePrep".format(
                        module_name, mesh_name, field))
            if runtime_mesh.get("triangles") != EXPECTED_TRIANGLES[mesh_name]:
                fail("{} triangle contract drifted".format(mesh_name))
            exact_list(runtime_mesh.get("uv_layers", ()), ("UVMap", "UV_Unique"),
                       "{} UV layers".format(mesh_name))
            tuple3(runtime_mesh.get("local_aabb_min_m"),
                   "{} local_aabb_min_m".format(mesh_name))
            tuple3(runtime_mesh.get("local_aabb_max_m"),
                   "{} local_aabb_max_m".format(mesh_name))
            if not runtime_mesh.get("material_slots"):
                fail("{} is missing semantic material slots".format(mesh_name))
            for slot in runtime_mesh["material_slots"]:
                if slot not in {semantic_slot(family) for family in ALL_FAMILIES}:
                    fail("{} has an unknown semantic material slot {}".format(mesh_name, slot))
            if mesh_name in MOVER_MESHES:
                expected_mover = MOVER_MESHES[mesh_name]
                if runtime_mesh.get("root") != "honest mover pivot; place at station transform + parked_offset":
                    fail("{} no longer declares an honest mover pivot".format(mesh_name))
                if runtime_mesh.get("pivot") != expected_mover["pivot"]:
                    fail("{} pivot contract drifted".format(mesh_name))
                if tuple3(runtime_mesh.get("parked_offset_m"), mesh_name + " parked offset") != expected_mover["parked_offset_m"]:
                    fail("{} parked offset contract drifted".format(mesh_name))
                if runtime_mesh.get("motion") != expected_mover["motion"]:
                    fail("{} motion contract drifted".format(mesh_name))
            elif runtime_mesh.get("root") != "station origin (in-station offsets baked in mesh)":
                fail("{} root contract drifted".format(mesh_name))
            mesh_specs[mesh_name] = runtime_mesh

    if set(mesh_specs) != set(EXPECTED_TRIANGLES) or sum(
            int(spec["triangles"]) for spec in mesh_specs.values()) != 3792:
        fail("ten-mesh / 3,792-triangle source contract drifted")
    audit_modules = payload_audit.get("modules", {})
    if set(audit_modules) != set(EXPECTED_MODULES):
        fail("payload audit module set drifted")
    for module_name, module_contract in EXPECTED_MODULES.items():
        audited_meshes = audit_modules[module_name].get("meshes", {})
        if set(audited_meshes) != set(module_contract["meshes"]):
            fail("payload audit {} mesh set drifted".format(module_name))
        for mesh_name in module_contract["meshes"]:
            if audited_meshes[mesh_name].get("triangles") != EXPECTED_TRIANGLES[mesh_name]:
                fail("payload audit triangle result drifted for {}".format(mesh_name))
            exact_list(audited_meshes[mesh_name].get("uv_layers", ()),
                       ("UVMap", "UV_Unique"),
                       "payload audit {} UV layers".format(mesh_name))
            exact_list(
                [normalise_terminal_blender_slot_suffix(slot)
                 for slot in audited_meshes[mesh_name].get("material_slots_raw", ())],
                mesh_specs[mesh_name]["material_slots"],
                "payload audit {} semantic slots".format(mesh_name),
            )

    source_textures = source_texture_specs(texture_manifest)
    stage_texture_manifest = read_json(SHARED_SOURCE_TEXTURE_MANIFEST)
    shared_equality = validate_shared_texture_equality(source_textures, stage_texture_manifest)
    context_hashes = validate_context_fbx_hashes(source_manifest)
    return source_textures, shared_equality, module_hashes, context_hashes


def validate_preflight_non_overwrite() -> None:
    if unreal.EditorAssetLibrary.does_directory_exist(DESTINATION):
        # UE retains an empty virtual directory after a recovered import failure.
        # Treat that as clean only when there are genuinely no assets under it;
        # an existing asset remains a hard no-overwrite failure.
        existing_assets = list(unreal.EditorAssetLibrary.list_assets(
            DESTINATION, recursive=True, include_folder=False))
        if existing_assets:
            fail("destination already contains assets; refusing to overwrite native content: {}"
                 .format(sorted(existing_assets)))
    if RECEIPT.exists():
        fail("receipt already exists; refusing to overwrite evidence: {}".format(RECEIPT))


def expected_shared_texture_path(family: str, channel: str) -> str:
    name = texture_name(family, channel)
    return object_path(SHARED_TEXTURE_DESTINATION, name)


def expected_shared_material_path(family: str) -> str:
    return object_path(SHARED_MATERIAL_DESTINATION, material_name(family))


def expected_new_texture_path(family: str, channel: str) -> str:
    name = texture_name(family, channel)
    return object_path(TEXTURE_DESTINATION, name)


def expected_new_material_path(family: str) -> str:
    return object_path(MATERIAL_DESTINATION, material_name(family))


def expected_sampler_type(parameter: str):
    return {
        "BaseColorMap": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
        "NormalMap": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
        "ORMMap": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
        "WearMaskMap": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    }[parameter]


def verify_texture_settings(texture, channel: str, label: str) -> dict:
    if texture is None or not isinstance(texture, unreal.Texture):
        fail("{} does not resolve to a Texture".format(label))
    expected_srgb = channel == "BC"
    expected_compression = {
        "BC": unreal.TextureCompressionSettings.TC_DEFAULT,
        "N": unreal.TextureCompressionSettings.TC_NORMALMAP,
        "ORM": unreal.TextureCompressionSettings.TC_MASKS,
        "MASK": unreal.TextureCompressionSettings.TC_MASKS,
    }[channel]
    srgb = bool(texture.get_editor_property("srgb"))
    compression = texture.get_editor_property("compression_settings")
    flip_green = bool(texture.get_editor_property("flip_green_channel"))
    if srgb != expected_srgb or compression != expected_compression:
        fail("{} texture settings drifted (sRGB={}, compression={})".format(
            label, srgb, compression))
    if flip_green != (channel == "N"):
        fail("{} green-channel convention drifted".format(label))
    return {
        "path": asset_path(texture),
        "srgb": srgb,
        "compression": str(compression),
        "flip_green_channel": flip_green,
    }


def load_and_verify_shared_assets(
        stage_receipt: dict,
) -> tuple[object, dict[str, object], dict[str, dict[str, object]], dict]:
    """Load shared assets only after their receipt and live state both agree."""
    if stage_receipt.get("status") != "PASS__TEXTURED_STAGEPACK_V001_IMPORTED_AT_RECEIPTED_UNREAL_SCALE":
        fail("StagePack v003 receipt is not an approved textured native import")
    if stage_receipt.get("destination") != SHARED_DESTINATION:
        fail("StagePack receipt destination drifted")
    if stage_receipt.get("material_master") != MASTER_PATH:
        fail("StagePack receipt no longer identifies the required shared master")
    if stage_receipt.get("source_texture_manifest_sha256") != sha256(SHARED_SOURCE_TEXTURE_MANIFEST):
        fail("StagePack receipt texture-manifest provenance drifted")
    if set(stage_receipt.get("materials_by_semantic_slot", {})) != {
            semantic_slot(family) for family in SHARED_FAMILIES}:
        fail("StagePack receipt shared material set drifted")

    textures: dict[str, dict[str, object]] = {family: {} for family in SHARED_FAMILIES}
    texture_evidence = {}
    receipt_textures = stage_receipt.get("textures", {})
    for family in SHARED_FAMILIES:
        for channel in CHANNELS:
            name = texture_name(family, channel)
            path = expected_shared_texture_path(family, channel)
            if receipt_textures.get(name) != path:
                fail("StagePack receipt shared texture path drifted for {}".format(name))
            texture = unreal.load_asset(path)
            textures[family][channel] = texture
            texture_evidence[name] = verify_texture_settings(texture, channel, name)

    master = unreal.load_asset(MASTER_PATH)
    if master is None or not isinstance(master, unreal.Material):
        fail("required shared StagePack master does not resolve to a Material")
    blend_mode = master.get_editor_property("blend_mode")
    if getattr(blend_mode, "name", None) != "BLEND_OPAQUE":
        fail("required shared StagePack master is not opaque")
    if bool(master.get_editor_property("two_sided")):
        fail("required shared StagePack master is unexpectedly two-sided")
    expressions = list(unreal.MaterialEditingLibrary.get_material_expressions(master))
    sample_by_parameter = {}
    for expression in expressions:
        if isinstance(expression, unreal.MaterialExpressionTextureSampleParameter2D):
            parameter = str(expression.get_editor_property("parameter_name"))
            sample_by_parameter.setdefault(parameter, []).append(expression)
    for parameter, channel in TEXTURE_PARAMETERS.items():
        samples = sample_by_parameter.get(parameter, [])
        if len(samples) != 1:
            fail("shared master {} sample contract is not singular".format(parameter))
        if samples[0].get_editor_property("sampler_type") != expected_sampler_type(parameter):
            fail("shared master {} sampler type is incorrect".format(parameter))
        expected_texture = textures["FoundryCharcoal"][channel]
        default_texture = unreal.MaterialEditingLibrary.get_material_default_texture_parameter_value(
            master, parameter)
        if asset_path(default_texture) != asset_path(expected_texture):
            fail("shared master {} default map drifted".format(parameter))

    # UE 5.8 silently accepted the original importer addressing the unnamed
    # ComponentMask input as ``Input``.  That left the material graph
    # syntactically valid but visually wrong.  Sampler types alone therefore
    # are not a sufficient dependency gate for the four new MIs below.
    expected_mask_inputs = {
        320: "ORMMap",
        400: "ORMMap",
        480: "ORMMap",
        600: "WearMaskMap",
    }
    mask_nodes = [
        expression for expression in expressions
        if isinstance(expression, unreal.MaterialExpressionComponentMask)
    ]
    masks_by_y = {
        int(node.get_editor_property("material_expression_editor_y")): node
        for node in mask_nodes
    }
    if len(mask_nodes) != len(expected_mask_inputs) or set(masks_by_y) != set(expected_mask_inputs):
        fail("shared master ComponentMask graph shape drifted")
    mask_evidence = {}
    for y, parameter in sorted(expected_mask_inputs.items()):
        node = masks_by_y[y]
        inputs = list(unreal.MaterialEditingLibrary.get_inputs_for_material_expression(
            master, node))
        source = inputs[0] if len(inputs) == 1 else None
        source_parameter = (
            str(source.get_editor_property("parameter_name"))
            if source and isinstance(
                source, unreal.MaterialExpressionTextureSampleParameter2D)
            else None
        )
        output = (
            str(unreal.MaterialEditingLibrary
                .get_input_node_output_name_for_material_expression(node, source))
            if source else None
        )
        mask_evidence[str(y)] = {
            "source_parameter": source_parameter,
            "output": output,
        }
        if source_parameter != parameter or output != "RGB":
            fail("shared master ComponentMask y={} is not wired to {}.RGB".format(
                y, parameter))
    default_dust = float(unreal.MaterialEditingLibrary.get_material_default_scalar_parameter_value(
        master, "RawDustStrength"))
    if abs(default_dust) > 0.0001:
        fail("shared master RawDustStrength default drifted from zero")

    materials: dict[str, object] = {}
    material_evidence = {}
    for family in SHARED_FAMILIES:
        slot = semantic_slot(family)
        path = expected_shared_material_path(family)
        if stage_receipt["materials_by_semantic_slot"].get(slot) != path:
            fail("StagePack receipt shared material path drifted for {}".format(slot))
        material = unreal.load_asset(path)
        if material is None or not isinstance(material, unreal.MaterialInstanceConstant):
            fail("shared material {} does not resolve to a MaterialInstanceConstant".format(slot))
        if asset_path(material.get_editor_property("parent")) != MASTER_PATH:
            fail("shared material {} does not parent to the shared master".format(slot))
        parameters = {}
        for parameter, channel in TEXTURE_PARAMETERS.items():
            actual_texture = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
                material, parameter)
            expected_texture = textures[family][channel]
            if asset_path(actual_texture) != asset_path(expected_texture):
                fail("shared material {} {} map drifted".format(slot, parameter))
            parameters[parameter] = asset_path(actual_texture)
        materials[slot] = material
        material_evidence[slot] = {
            "path": asset_path(material),
            "parent": MASTER_PATH,
            "texture_parameters": parameters,
            "RawDustStrength": float(
                unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(
                    material, "RawDustStrength")),
        }
    return master, materials, textures, {
        "master": {
            "path": MASTER_PATH,
            "blend_mode": getattr(blend_mode, "name", str(blend_mode)),
            "two_sided": False,
            "texture_sampler_contract": {
                parameter: str(expected_sampler_type(parameter))
                for parameter in TEXTURE_PARAMETERS
            },
            "component_mask_inputs": mask_evidence,
            "RawDustStrength": default_dust,
        },
        "textures": texture_evidence,
        "materials": material_evidence,
    }


def configure_texture(texture, channel: str) -> None:
    try:
        if channel == "BC":
            texture.set_editor_property("srgb", True)
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
        elif channel == "N":
            texture.set_editor_property("srgb", False)
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            texture.set_editor_property("flip_green_channel", True)
        else:
            texture.set_editor_property("srgb", False)
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
    except Exception as error:
        fail("cannot apply {} texture settings to {}: {}".format(
            channel, texture.get_name(), error))
    if not unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False):
        fail("cannot save imported texture {}".format(texture.get_name()))
    verify_texture_settings(texture, channel, texture.get_name())


def import_new_texture(spec: dict):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(spec["source_path"]),
        "destination_path": TEXTURE_DESTINATION,
        "destination_name": spec["asset_name"],
        "automated": True,
        "replace_existing": False,
        "save": True,
    })
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported_paths = list(task.get_editor_property("imported_object_paths") or [])
    if len(imported_paths) != 1 or imported_paths[0] != expected_new_texture_path(
            spec["family"], spec["channel"]):
        fail("expected one new texture {} at its exact path, got {}".format(
            spec["asset_name"], imported_paths))
    texture = unreal.load_asset(imported_paths[0])
    configure_texture(texture, spec["channel"])
    return texture


def set_required_property(obj, name: str, value, label: str) -> None:
    """Set a pivot-critical FBX option and prove UE accepted it."""
    try:
        obj.set_editor_property(name, value)
        actual = obj.get_editor_property(name)
    except Exception as error:
        fail("{} lacks required {} control: {}".format(label, name, error))
    if actual != value:
        fail("{} did not retain {}={}".format(label, name, value))


def raw_imported_mesh_name(module_contract: dict, semantic_name: str) -> str:
    """UE's Combine-Meshes-off FBX convention, measured from the real lane.

    UE 5.8 retains a single-mesh FBX under its file stem, but prefixes each
    source child node with that stem when an FBX yields multiple retained
    meshes.  Both forms were measured in the guarded import lane.  The raw
    name is useful provenance evidence; it is then renamed to the stable
    semantic native asset name consumed by the press actor.
    """
    source_meshes = module_contract["meshes"]
    if semantic_name not in source_meshes:
        fail("{} is not declared by {}".format(semantic_name, module_contract["file"]))
    stem = Path(module_contract["file"]).stem
    if len(source_meshes) == 1:
        return stem
    return "{}_{}".format(stem, semantic_name)


def import_module(module_name: str, module_contract: dict) -> dict[str, tuple[object, str]]:
    """Import one FBX into separate, semantically named mesh assets.

    The two phases are intentional: first prove UE created one asset for each
    exact FBX child node; only then rename the new, unreferenced packages to
    the stable ``SM_CA_*`` contract used at runtime.  ``destination_name``
    cannot assign distinct names to a multi-node import and would weaken that
    proof.
    """
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_materials": False,
        "import_textures": False,
        "import_as_skeletal": False,
        "automated_import_should_detect_type": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    static_data = options.static_mesh_import_data
    static_data.set_editor_properties({
        "combine_meshes": False,
        "auto_generate_collision": False,
        "generate_lightmap_u_vs": False,
        "remove_degenerates": True,
        "import_uniform_scale": 1.0,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
    })
    # A mover's local mesh origin is the approved mechanical pivot.  Do not
    # flatten the FBX node transform into the vertices and do not bake a new
    # pivot.  The RuntimePrep parked offsets remain actor-placement data.
    set_required_property(static_data, "transform_vertex_to_absolute", False,
                          "FBX static-mesh import")
    set_required_property(static_data, "bake_pivot_in_vertex", False,
                          "FBX static-mesh import")
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE_PREP_DIR / module_contract["file"]),
        "destination_path": MESH_DESTINATION,
        "automated": True,
        "replace_existing": False,
        "save": True,
        "options": options,
    })
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported_paths = list(task.get_editor_property("imported_object_paths") or [])
    expected_names = set(module_contract["meshes"])
    if len(imported_paths) != len(expected_names):
        fail("{} imported {} objects, expected {} independent meshes: {}".format(
            module_name, len(imported_paths), len(expected_names), imported_paths))
    raw_to_semantic = {
        raw_imported_mesh_name(module_contract, semantic_name): semantic_name
        for semantic_name in expected_names
    }
    expected_raw_paths = {
        raw_name: object_path(MESH_DESTINATION, raw_name)
        for raw_name in raw_to_semantic
    }
    raw_meshes: dict[str, tuple[object, str]] = {}
    for imported_path in imported_paths:
        mesh = unreal.load_asset(imported_path)
        if mesh is None or not isinstance(mesh, unreal.StaticMesh):
            fail("{} imported a non-StaticMesh object: {}".format(module_name, imported_path))
        raw_name = mesh.get_name()
        if raw_name not in raw_to_semantic:
            fail("{} imported unexpected raw mesh {}".format(module_name, raw_name))
        expected_raw_path = expected_raw_paths[raw_name]
        if imported_path != expected_raw_path:
            fail("{} raw mesh {} imported at {} rather than {}".format(
                module_name, raw_name, imported_path, expected_raw_path))
        semantic_name = raw_to_semantic[raw_name]
        if semantic_name in raw_meshes:
            fail("{} imported duplicate semantic mesh {}".format(
                module_name, semantic_name))
        raw_meshes[semantic_name] = (mesh, imported_path)
    if set(raw_meshes) != expected_names:
        fail("{} independent raw mesh names differ: got {}, expected {}".format(
            module_name, sorted(raw_meshes), sorted(expected_names)))

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    rename_operations = [
        unreal.AssetRenameData(raw_meshes[semantic_name][0], MESH_DESTINATION,
                               semantic_name)
        for semantic_name in sorted(expected_names)
    ]
    if not asset_tools.rename_assets(rename_operations):
        fail("{} could not rename raw imported meshes to semantic native names".format(
            module_name))
    if not unreal.EditorAssetLibrary.save_directory(
            MESH_DESTINATION, only_if_is_dirty=False, recursive=True):
        fail("{} could not save semantic mesh rename results".format(module_name))

    result: dict[str, tuple[object, str]] = {}
    for semantic_name in sorted(expected_names):
        raw_name = raw_imported_mesh_name(module_contract, semantic_name)
        raw_path = expected_raw_paths[raw_name]
        expected_path = object_path(MESH_DESTINATION, semantic_name)
        if unreal.EditorAssetLibrary.does_asset_exist(raw_path):
            fail("{} left a raw-name package or redirector at {}".format(
                module_name, raw_path))
        if not unreal.EditorAssetLibrary.does_asset_exist(expected_path):
            fail("{} semantic mesh rename did not create {}".format(
                module_name, expected_path))
        mesh = unreal.load_asset(expected_path)
        if mesh is None or not isinstance(mesh, unreal.StaticMesh):
            fail("{} renamed asset does not resolve to a StaticMesh: {}".format(
                module_name, expected_path))
        if mesh.get_name() != semantic_name or asset_path(mesh) != expected_path:
            fail("{} semantic mesh identity drifted after rename: {}".format(
                module_name, asset_path(mesh)))
        result[semantic_name] = (mesh, expected_path)
    return result


def converted_source_bounds_cm(mesh_spec: dict) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Translate source AABB to UE's documented Convert Scene Y-negation."""
    source_min = tuple3(mesh_spec["local_aabb_min_m"], "source local AABB minimum")
    source_max = tuple3(mesh_spec["local_aabb_max_m"], "source local AABB maximum")
    return (
        (source_min[0] * 100.0, -source_max[1] * 100.0, source_min[2] * 100.0),
        (source_max[0] * 100.0, -source_min[1] * 100.0, source_max[2] * 100.0),
    )


def vector_tuple(vector, decimals: int = 3) -> tuple[float, float, float]:
    return (round(float(vector.x), decimals), round(float(vector.y), decimals),
            round(float(vector.z), decimals))


def within_tolerance(actual, expected, tolerance: float) -> bool:
    return all(abs(float(actual_value) - float(expected_value)) <= tolerance
               for actual_value, expected_value in zip(actual, expected))


def bind_and_verify_mesh(
        mesh_name: str,
        mesh,
        mesh_path: str,
        mesh_spec: dict,
        material_by_slot: dict[str, object],
        mesh_editor,
) -> dict:
    """Prove source geometry survived and bind only its semantic materials."""
    if mesh_editor is None or not hasattr(mesh_editor, "get_num_uv_channels"):
        fail("StaticMeshEditorSubsystem UV query is unavailable")
    source_triangles = int(mesh_spec["triangles"])
    unreal_triangles = int(mesh.get_num_triangles(0))
    if unreal_triangles != source_triangles:
        fail("{} UE LOD0 triangles={} rather than payload-verified source {}".format(
            mesh_name, unreal_triangles, source_triangles))
    if int(mesh.get_num_lods()) != 1:
        fail("{} imported unexpected authored LOD count {}".format(
            mesh_name, mesh.get_num_lods()))
    uv_channels = int(mesh_editor.get_num_uv_channels(mesh, 0))
    if uv_channels != 2:
        fail("{} UV-channel contract drifted: got {}, expected 2".format(
            mesh_name, uv_channels))

    bounds = mesh.get_bounding_box()
    actual_min = vector_tuple(bounds.min)
    actual_max = vector_tuple(bounds.max)
    expected_min, expected_max = converted_source_bounds_cm(mesh_spec)
    # 0.25 cm allows binary FBX rounding but catches a lost node pivot or a
    # material-flow placement offset being baked into a mover mesh.
    if not within_tolerance(actual_min, expected_min, 0.25) or not within_tolerance(
            actual_max, expected_max, 0.25):
        fail("{} bounds do not preserve its source local pivot/AABB: got {}..{}, "
             "expected {}..{}".format(
                 mesh_name, actual_min, actual_max, expected_min, expected_max))

    static_materials = list(mesh.get_editor_property("static_materials"))
    expected_slots = tuple(mesh_spec["material_slots"])
    if len(static_materials) != len(expected_slots):
        fail("{} material slot count drifted: got {}, expected {}".format(
            mesh_name, len(static_materials), len(expected_slots)))
    raw_slots = []
    normalised_slots = []
    for index, material_slot in enumerate(static_materials):
        raw_name = str(material_slot.get_editor_property("material_slot_name"))
        canonical_name = normalise_terminal_blender_slot_suffix(raw_name)
        raw_slots.append(raw_name)
        normalised_slots.append(canonical_name)
        if canonical_name != expected_slots[index]:
            fail("{} slot {} differs after only terminal .ddd normalization: {} -> {}, "
                 "expected {}".format(mesh_name, index, raw_name, canonical_name,
                                        expected_slots[index]))
        material = material_by_slot.get(canonical_name)
        if material is None:
            fail("{} has no loaded semantic material for {}".format(mesh_name, canonical_name))
        # Strip only the documented Blender duplicate suffix in the native
        # slot label, then bind the exact shared/new MI for that semantic role.
        material_slot.set_editor_property("material_slot_name", canonical_name)
        material_slot.set_editor_property("material_interface", material)
        mesh.set_material(index, material)
    mesh.set_editor_property("static_materials", static_materials)
    mesh.set_editor_property("light_map_coordinate_index", 1)
    mesh.set_editor_property("light_map_resolution", 128)
    if not unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False):
        fail("cannot save semantic material bindings for {}".format(mesh_name))

    bound_slots = tuple(str(slot.get_editor_property("material_slot_name"))
                        for slot in mesh.get_editor_property("static_materials"))
    bound_materials = tuple(asset_path(
        slot.get_editor_property("material_interface"))
        for slot in mesh.get_editor_property("static_materials"))
    expected_material_paths = tuple(asset_path(material_by_slot[slot]) for slot in expected_slots)
    if bound_slots != expected_slots or bound_materials != expected_material_paths:
        fail("{} native semantic material binding did not persist".format(mesh_name))
    if int(mesh.get_editor_property("light_map_coordinate_index")) != 1:
        fail("{} lightmap coordinate index did not persist".format(mesh_name))
    if int(mesh.get_editor_property("light_map_resolution")) != 128:
        fail("{} lightmap resolution did not persist".format(mesh_name))
    simple_collision = (int(mesh_editor.get_simple_collision_count(mesh))
                        if hasattr(mesh_editor, "get_simple_collision_count") else None)
    convex_collision = (int(mesh_editor.get_convex_collision_count(mesh))
                        if hasattr(mesh_editor, "get_convex_collision_count") else None)
    if simple_collision not in (None, 0) or convex_collision not in (None, 0):
        fail("{} unexpectedly has imported collision".format(mesh_name))
    return {
        "mesh_object_path": mesh_path,
        "source_triangles": source_triangles,
        "unreal_render_triangles": unreal_triangles,
        "source_local_aabb_m": {
            "min": list(tuple3(mesh_spec["local_aabb_min_m"], mesh_name + " source min")),
            "max": list(tuple3(mesh_spec["local_aabb_max_m"], mesh_name + " source max")),
        },
        "expected_unreal_aabb_cm_after_convert_scene": {
            "min": list(expected_min), "max": list(expected_max),
        },
        "unreal_aabb_cm": {"min": list(actual_min), "max": list(actual_max)},
        "authored_uv_layers": list(mesh_spec["uv_layers"]),
        "unreal_uv_channels": uv_channels,
        "lod_count": int(mesh.get_num_lods()),
        "raw_import_slot_names": raw_slots,
        "normalised_slot_names": normalised_slots,
        "semantic_slots": list(bound_slots),
        "default_materials": list(bound_materials),
        "light_map_coordinate_index": 1,
        "light_map_resolution": 128,
        "combine_meshes": False,
        "transform_vertex_to_absolute": False,
        "bake_pivot_in_vertex": False,
        "auto_generated_collision": False,
        "simple_collision_count": simple_collision,
        "convex_collision_count": convex_collision,
        "source_root_contract": mesh_spec["root"],
        "mover": (MOVER_MESHES[mesh_name] if mesh_name in MOVER_MESHES else None),
    }


def create_new_material_instance(family: str, textures: dict[str, object], master):
    name = material_name(family)
    expected_path = expected_new_material_path(family)
    if unreal.EditorAssetLibrary.does_asset_exist(expected_path):
        fail("new material path already exists: {}".format(expected_path))
    instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIAL_DESTINATION, unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew())
    if instance is None or not isinstance(instance, unreal.MaterialInstanceConstant):
        fail("could not create new material instance for {}".format(family))
    if asset_path(instance) != expected_path:
        fail("new material {} was created at {} rather than {}".format(
            family, asset_path(instance), expected_path))
    instance.set_editor_property("parent", master)
    editing = unreal.MaterialEditingLibrary
    for parameter, channel in TEXTURE_PARAMETERS.items():
        editing.set_material_instance_texture_parameter_value(
            instance, parameter, textures[channel])
    editing.set_material_instance_scalar_parameter_value(
        instance, "RawDustStrength", NEW_FAMILY_DUST[family])
    if not unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False):
        fail("cannot save new material instance for {}".format(family))
    if asset_path(instance.get_editor_property("parent")) != MASTER_PATH:
        fail("new material {} did not retain the shared master parent".format(family))
    for parameter, channel in TEXTURE_PARAMETERS.items():
        actual = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
            instance, parameter)
        if asset_path(actual) != asset_path(textures[channel]):
            fail("new material {} {} map did not persist".format(family, parameter))
    dust = float(unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(
        instance, "RawDustStrength"))
    if abs(dust - NEW_FAMILY_DUST[family]) > 0.0001:
        fail("new material {} RawDustStrength did not persist".format(family))
    return instance


def exact_native_package_inventory() -> list[str]:
    expected_object_paths = {
        *{object_path(MESH_DESTINATION, mesh_name) for mesh_name in EXPECTED_TRIANGLES},
        *{expected_new_texture_path(family, channel)
          for family in NEW_FAMILIES for channel in CHANNELS},
        *{expected_new_material_path(family) for family in NEW_FAMILIES},
    }
    actual_assets = set(unreal.EditorAssetLibrary.list_assets(
        DESTINATION, recursive=True, include_folder=False))
    actual_packages = {package_path(path) for path in actual_assets}
    expected_packages = {package_path(path) for path in expected_object_paths}
    if actual_packages != expected_packages:
        fail("native Material Flow package inventory differs from the exact 30-package "
             "closure; got {} packages".format(len(actual_packages)))
    return sorted(actual_assets)


def main() -> None:
    # All source and shared-native gates run before the first asset import.
    validate_preflight_non_overwrite()
    source_manifest = read_json(SOURCE_MANIFEST)
    texture_manifest = read_json(SOURCE_TEXTURE_MANIFEST)
    runtime_stats = read_json(SOURCE_RUNTIME_STATS)
    payload_audit = read_json(SOURCE_PAYLOAD_AUDIT)
    stage_receipt = read_json(SHARED_IMPORT_RECEIPT)
    (source_textures, shared_equality, module_hashes,
     context_hashes) = validate_source_contract(
         source_manifest, texture_manifest, runtime_stats, payload_audit)
    shared_master, shared_materials, shared_textures, shared_evidence = (
        load_and_verify_shared_assets(stage_receipt))

    unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")

    # Import precisely the four genuinely new texture families.  The nine
    # shared families have already been proven byte-identical and are never
    # duplicated into this destination.
    new_texture_assets: dict[str, dict[str, object]] = {
        family: {} for family in NEW_FAMILIES
    }
    new_texture_receipt = {}
    for family in NEW_FAMILIES:
        for channel in CHANNELS:
            spec = source_textures[family][channel]
            texture = import_new_texture(spec)
            new_texture_assets[family][channel] = texture
            new_texture_receipt[spec["asset_name"]] = {
                "path": asset_path(texture),
                "source_file": str(spec["source_path"]),
                "source_sha256": spec["source_sha256"],
                **verify_texture_settings(texture, channel, spec["asset_name"]),
            }

    # Separate-node FBX import preserves the two mover pivots.  No material,
    # texture, collision, or generated UV is accepted from an FBX.
    imported_meshes: dict[str, tuple[object, str]] = {}
    for module_name, module_contract in EXPECTED_MODULES.items():
        module_meshes = import_module(module_name, module_contract)
        if set(imported_meshes).intersection(module_meshes):
            fail("module {} duplicated a prior mesh name".format(module_name))
        imported_meshes.update(module_meshes)
    if set(imported_meshes) != set(EXPECTED_TRIANGLES):
        fail("native import did not produce the exact required ten mesh assets")

    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    mesh_editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if mesh_editor is None:
        fail("StaticMeshEditorSubsystem is unavailable")

    # New MIs parent only to the already-live, sampler-validated StagePack
    # master.  Shared MIs and textures are never saved or changed here.
    material_by_slot = dict(shared_materials)
    new_material_receipt = {}
    for family in NEW_FAMILIES:
        material = create_new_material_instance(
            family, new_texture_assets[family], shared_master)
        slot = semantic_slot(family)
        material_by_slot[slot] = material
        new_material_receipt[slot] = {
            "path": asset_path(material),
            "parent": MASTER_PATH,
            "texture_parameters": {
                parameter: asset_path(new_texture_assets[family][channel])
                for parameter, channel in TEXTURE_PARAMETERS.items()
            },
            "RawDustStrength": NEW_FAMILY_DUST[family],
        }
    if set(material_by_slot) != {semantic_slot(family) for family in ALL_FAMILIES}:
        fail("13-family semantic material closure is incomplete")

    mesh_results = {}
    modules_receipt = {}
    for module_name, module_contract in EXPECTED_MODULES.items():
        module_mesh_results = {}
        for mesh_name in module_contract["meshes"]:
            mesh, mesh_path = imported_meshes[mesh_name]
            module_mesh_results[mesh_name] = bind_and_verify_mesh(
                mesh_name, mesh, mesh_path,
                runtime_stats["modules"][module_name]["meshes"][mesh_name],
                material_by_slot, mesh_editor)
            mesh_results[mesh_name] = module_mesh_results[mesh_name]
        modules_receipt[module_name] = {
            "source_fbx": str(SOURCE_PREP_DIR / module_contract["file"]),
            "source_fbx_sha256": module_hashes[module_name],
            "station": module_contract["station"],
            "placement_slot_source_cm": list(module_contract["placement_slot_cm"]),
            "rotation_source": [0, 0, 0],
            "meshes": module_mesh_results,
        }
    if sum(result["unreal_render_triangles"] for result in mesh_results.values()) != 3792:
        fail("native ten-mesh triangle total is not 3,792")

    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.EditorAssetLibrary.save_directory(DESTINATION, only_if_is_dirty=False, recursive=True)
    native_assets = exact_native_package_inventory()

    receipt = {
        "$schema": "lineboss/onefactory/press/material-flow-runtimeprep-v001-import/v1",
        "status": "PASS__MATERIAL_FLOW_V001_IMPORTED_AS_TEN_SEMANTIC_MESHES",
        "destination": DESTINATION,
        "source_asset": str(SOURCE_ASSET_DIR),
        "source_runtimeprep": str(SOURCE_PREP_DIR),
        "source_blend_sha256": SOURCE_BLEND_SHA256,
        "source_matflow_manifest_sha256": sha256(SOURCE_MANIFEST),
        "source_texture_manifest_sha256": sha256(SOURCE_TEXTURE_MANIFEST),
        "source_runtimeprep_stats_sha256": sha256(SOURCE_RUNTIME_STATS),
        "source_payload_audit": str(SOURCE_PAYLOAD_AUDIT),
        "source_payload_audit_sha256": sha256(SOURCE_PAYLOAD_AUDIT),
        "source_payload_audit_status": payload_audit["status"],
        "source_payload_triangles": 3792,
        "source_coordinate_system": COORDINATE_SYSTEM,
        "convert_scene": True,
        "convert_scene_note": runtime_stats["convert_scene_note"],
        "shared_stagepack_reuse": {
            "destination": SHARED_DESTINATION,
            "import_receipt": str(SHARED_IMPORT_RECEIPT),
            "import_receipt_sha256": sha256(SHARED_IMPORT_RECEIPT),
            "source_texture_manifest": str(SHARED_SOURCE_TEXTURE_MANIFEST),
            "source_texture_manifest_sha256": sha256(SHARED_SOURCE_TEXTURE_MANIFEST),
            "master": shared_evidence["master"],
            "materials": shared_evidence["materials"],
            "textures": shared_evidence["textures"],
            "byte_identical_source_texture_families": shared_equality,
            "render_context_fbx_sha256": context_hashes,
        },
        "new_texture_families": list(NEW_FAMILIES),
        "new_textures": new_texture_receipt,
        "new_material_instances": new_material_receipt,
        "modules": modules_receipt,
        "native_mesh_count": len(mesh_results),
        "native_package_count": len(native_assets),
        "native_assets": native_assets,
        "texture_import_counts": {
            "new_imported": len(NEW_FAMILIES) * len(CHANNELS),
            "shared_reused_without_import": len(SHARED_FAMILIES) * len(CHANNELS),
        },
        "material_instance_counts": {
            "new_created": len(NEW_FAMILIES),
            "shared_reused_without_mutation": len(SHARED_FAMILIES),
        },
        "material_master_created": False,
        "imported_materials_from_fbx": False,
        "imported_textures_from_fbx": False,
        "fbx_combine_meshes": False,
        "mover_pivots_preserved": list(MOVER_MESHES),
        "blender_slot_suffix_normalisation": "terminal .ddd only",
        "normal_maps_green_flipped": True,
        "auto_generated_collision": False,
        "authored_lods": "LOD0 only; no LOD1/LOD2 assets shipped",
        "map_opened_by_script": False,
        "map_saved_by_script": False,
        "source_content_writes": [],
        "shared_stagepack_content_writes": [],
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    if RECEIPT.exists():
        fail("receipt appeared during import; refusing to overwrite it")
    with io.open(RECEIPT, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    unreal.log("LINE_BOSS_MATERIAL_FLOW_RUNTIMEPREP_V001_IMPORT=" +
               json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    finally:
        # ``-ExecutePythonScript`` otherwise leaves a full editor session
        # alive after the one-shot import.  Always release it, including on a
        # fail-closed gate, so a failed import cannot leave this lane holding
        # the project open for a recovery pass.
        unreal.SystemLibrary.quit_editor()
