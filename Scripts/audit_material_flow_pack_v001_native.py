"""Read-only native audit for Claude's Material Flow RuntimePrep v001.

Run this only after ``Tools/import_material_flow_pack_v001.py`` has completed.
It deliberately does *not* import, rebind, save, open a map, or alter Claude's
source package.  It independently proves the current native closure, the
source provenance behind it, and that merely inspecting it did not mutate the
native Content tree.  Its only intended write is a new, retry-safe JSON receipt
under ``Saved/Audits``.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT_ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")

SOURCE_ASSET_DIR = PROJECT_ROOT / "ArtSource/Claude_PressShop_MaterialFlowPack_v001"
SOURCE_PREP_DIR = PROJECT_ROOT / "ArtSource/Claude_PressShop_MaterialFlowPack_RuntimePrep_v001"
SOURCE_BLEND = SOURCE_ASSET_DIR / "CA_PressShop_MaterialFlowPack_v001.blend"
SOURCE_MANIFEST = SOURCE_ASSET_DIR / "matflowpack_manifest.json"
SOURCE_TEXTURE_MANIFEST = SOURCE_ASSET_DIR / "texture_material_manifest.json"
SOURCE_RUNTIME_STATS = SOURCE_PREP_DIR / "runtime_prep_stats.json"
SOURCE_PAYLOAD_AUDIT = (
    PROJECT_ROOT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v001/"
    "fbx_payload_audit_retry1.json"
)
IMPORTER = PROJECT_ROOT / "Tools/import_material_flow_pack_v001.py"
IMPORT_RECEIPT = (
    PROJECT_ROOT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v001/"
    "import_receipt.json"
)

SHARED_SOURCE_ASSET_DIR = PROJECT_ROOT / "ArtSource/Claude_S03S06_StagePack_v001"
SHARED_SOURCE_PREP_DIR = PROJECT_ROOT / "ArtSource/Claude_S03S06_StagePack_RuntimePrep_v001"
SHARED_SOURCE_TEXTURE_MANIFEST = (
    SHARED_SOURCE_ASSET_DIR / "texture_material_manifest.json"
)
SHARED_IMPORT_RECEIPT = (
    PROJECT_ROOT / "Saved/Audits/OneFactory/Press/S03S06StagePackRuntimePrep_v001/"
    "import_receipt.json"
)

DESTINATION = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "MaterialFlowPack_v001"
)
MESH_DESTINATION = DESTINATION + "/Meshes"
TEXTURE_DESTINATION = DESTINATION + "/Textures"
MATERIAL_DESTINATION = DESTINATION + "/Materials"

SHARED_DESTINATION = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "SharedTrainModules_v003"
)
SHARED_TEXTURE_DESTINATION = SHARED_DESTINATION + "/Textures"
SHARED_MATERIAL_DESTINATION = SHARED_DESTINATION + "/Materials"

NATIVE_CONTENT_ROOT = (
    PROJECT_ROOT / "Content/LineBoss/Factory/OneFactory/v001/Native"
)
AUDIT_DIR = (
    PROJECT_ROOT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v001"
)
RECEIPT_BASENAME = "native_runtime_audit_v001"

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

# These were authored in the approved StagePack material lane; the four new
# Material Flow families intentionally inherit the master default (zero), not
# an integration-invented weathering amount.
SHARED_FAMILY_DUST = {
    "CairnwellGreen": 0.035,
    "FoundryCharcoal": 0.050,
    "ServiceGrey": 0.030,
    "SafetyYellow": 0.020,
    "WorkedSteel": 0.015,
    "InspectionGlass": 0.0,
    "TrainAAccent": 0.020,
    "StatusGreen": 0.0,
    "StatusAmber": 0.0,
}
NEW_FAMILY_DUST = {family: 0.0 for family in NEW_FAMILIES}

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
STATION_ROOT = "station origin (in-station offsets baked in mesh)"
MOVER_ROOT = "honest mover pivot; place at station transform + parked_offset"
SLOT_SUFFIX = re.compile(r"\.\d{3}$")


class AuditFailure(RuntimeError):
    """A failing contract is deliberate evidence, not an audit warning."""


def fail(message: str) -> None:
    raise AuditFailure("Material Flow native audit failed: " + message)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().lower()


def read_json(path: Path) -> dict:
    if not path.is_file():
        fail("required JSON authority is missing: {}".format(path))
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            value = json.load(handle)
    except Exception as error:
        fail("cannot read JSON authority {}: {}".format(path, error))
    if not isinstance(value, dict):
        fail("JSON authority is not an object: {}".format(path))
    return value


def object_path(folder: str, name: str) -> str:
    return "{}/{}.{}".format(folder, name, name)


def package_path(value: str) -> str:
    return value.rsplit(".", 1)[0] if "." in value.rsplit("/", 1)[-1] else value


def canonical_asset_path(value: str) -> str:
    """Accept either UE list-assets spelling and compare stable object paths."""
    package = package_path(str(value))
    name = package.rsplit("/", 1)[-1]
    return "{}.{}".format(package, name)


def asset_path(asset) -> str:
    return str(asset.get_path_name()) if asset else "none"


def texture_name(family: str, channel: str) -> str:
    return "T_CA_MW_PT_{}_{}".format(family, channel)


def material_name(family: str) -> str:
    return "MI_CA_MW_PT_{}_v001".format(family)


def semantic_slot(family: str) -> str:
    return "CA_MW_{}".format(family)


def expected_shared_texture_path(family: str, channel: str) -> str:
    return object_path(SHARED_TEXTURE_DESTINATION, texture_name(family, channel))


def expected_new_texture_path(family: str, channel: str) -> str:
    return object_path(TEXTURE_DESTINATION, texture_name(family, channel))


def expected_shared_material_path(family: str) -> str:
    return object_path(SHARED_MATERIAL_DESTINATION, material_name(family))


def expected_new_material_path(family: str) -> str:
    return object_path(MATERIAL_DESTINATION, material_name(family))


def expected_mesh_path(mesh_name: str) -> str:
    return object_path(MESH_DESTINATION, mesh_name)


def vector_tuple(vector, decimals: int = 3) -> tuple[float, float, float]:
    return (
        round(float(vector.x), decimals),
        round(float(vector.y), decimals),
        round(float(vector.z), decimals),
    )


def tuple3(value, label: str) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        fail("{} must be a three-value vector, got {}".format(label, value))
    return tuple(float(item) for item in value)


def within_tolerance(actual, expected, tolerance: float) -> bool:
    return all(
        abs(float(actual_value) - float(expected_value)) <= tolerance
        for actual_value, expected_value in zip(actual, expected)
    )


def normalise_terminal_blender_slot_suffix(raw_name) -> str:
    """Only Blender's terminal duplicate suffix is allowed during provenance checks."""
    return SLOT_SUFFIX.sub("", str(raw_name))


def mover_contract_matches(value, expected: dict, label: str) -> bool:
    """JSON turns the authored tuple into a list, so compare the contract by field."""
    if not isinstance(value, dict):
        return False
    try:
        offset = tuple3(value.get("parked_offset_m"), label + " parked offset")
    except AuditFailure:
        return False
    return (
        value.get("pivot") == expected["pivot"]
        and offset == expected["parked_offset_m"]
        and value.get("motion") == expected["motion"]
    )


def enum_name(value) -> str:
    return str(getattr(value, "name", value))


def snapshot_tree(root: Path) -> dict:
    """Hash each persisted source/native file and a deterministic aggregate."""
    if not root.is_dir():
        fail("required snapshot root is missing: {}".format(root))
    entries = {}
    aggregate = hashlib.sha256()
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = str(path.relative_to(root)).replace("\\", "/")
        info = {
            "sha256": sha256(path),
            "size": path.stat().st_size,
            "mtime_ns": path.stat().st_mtime_ns,
        }
        entries[relative] = info
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(info["sha256"].encode("ascii"))
        aggregate.update(b"\0")
        aggregate.update(str(info["size"]).encode("ascii"))
        aggregate.update(b"\0")
        aggregate.update(str(info["mtime_ns"]).encode("ascii"))
        aggregate.update(b"\n")
    return {
        "root": str(root),
        "file_count": len(entries),
        "aggregate_sha256": aggregate.hexdigest(),
        "files": entries,
    }


def snapshot_source_authorities() -> dict:
    """The audit must not alter any source package or its shared texture lineage."""
    external = {}
    for path in (SOURCE_PAYLOAD_AUDIT, IMPORT_RECEIPT, SHARED_IMPORT_RECEIPT, IMPORTER):
        if not path.is_file():
            fail("required authority is missing: {}".format(path))
        external[str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")] = {
            "sha256": sha256(path),
            "size": path.stat().st_size,
            "mtime_ns": path.stat().st_mtime_ns,
        }
    return {
        "material_flow_source": snapshot_tree(SOURCE_ASSET_DIR),
        "material_flow_runtimeprep": snapshot_tree(SOURCE_PREP_DIR),
        "stagepack_source": snapshot_tree(SHARED_SOURCE_ASSET_DIR),
        "stagepack_runtimeprep": snapshot_tree(SHARED_SOURCE_PREP_DIR),
        "external_authorities": external,
    }


def expected_native_asset_paths() -> set[str]:
    return {
        *{expected_mesh_path(name) for name in EXPECTED_TRIANGLES},
        *{expected_new_texture_path(family, channel)
          for family in NEW_FAMILIES for channel in CHANNELS},
        *{expected_new_material_path(family) for family in NEW_FAMILIES},
    }


def list_asset_paths(folder: str) -> set[str]:
    return {
        canonical_asset_path(str(path))
        for path in unreal.EditorAssetLibrary.list_assets(
            folder, recursive=True, include_folder=False)
    }


def converted_source_bounds_cm(mesh_spec: dict) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """UE Convert Scene preserves X/Z and negates source Y for this handoff."""
    source_min = tuple3(mesh_spec.get("local_aabb_min_m"), "source local AABB minimum")
    source_max = tuple3(mesh_spec.get("local_aabb_max_m"), "source local AABB maximum")
    return (
        (source_min[0] * 100.0, -source_max[1] * 100.0, source_min[2] * 100.0),
        (source_max[0] * 100.0, -source_min[1] * 100.0, source_max[2] * 100.0),
    )


def source_texture_specs(texture_manifest: dict) -> dict[str, dict[str, dict]]:
    if texture_manifest.get("asset_pack") != "CA_PressShop_MaterialFlowPack_v001":
        fail("Material Flow texture manifest has the wrong asset-pack identity")
    families = texture_manifest.get("families")
    if not isinstance(families, dict) or set(families) != set(ALL_FAMILIES):
        fail("Material Flow texture-family closure drifted")

    results: dict[str, dict[str, dict]] = {}
    for family in ALL_FAMILIES:
        row = families[family]
        if row.get("material_slot") != semantic_slot(family):
            fail("{} material-slot contract drifted".format(family))
        provenance = str(row.get("provenance", ""))
        if family in SHARED_FAMILIES:
            if not provenance.startswith(
                    "reused - regenerated byte-identical to the S03-S06 stage pack family"):
                fail("{} is no longer declared as exact StagePack texture reuse".format(family))
        elif provenance != "newly authored for this pack":
            fail("{} is no longer declared as newly authored Material Flow texture".format(family))

        maps = row.get("maps")
        if not isinstance(maps, dict) or set(maps) != set(CHANNELS):
            fail("{} map-channel closure drifted".format(family))
        results[family] = {}
        for channel in CHANNELS:
            map_row = maps[channel]
            expected_relative = "Textures/{}.png".format(texture_name(family, channel))
            if map_row.get("file") != expected_relative:
                fail("{} {} source map path drifted".format(family, channel))
            source_path = SOURCE_ASSET_DIR / expected_relative
            expected_hash = str(map_row.get("sha256", "")).lower()
            if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
                fail("{} {} source map hash is not a SHA-256".format(family, channel))
            if not source_path.is_file() or sha256(source_path) != expected_hash:
                fail("{} {} source map does not match its manifest hash".format(
                    family, channel))
            results[family][channel] = {
                "path": source_path,
                "sha256": expected_hash,
                "asset_name": texture_name(family, channel),
            }
    return results


def validate_shared_source_texture_reuse(
        material_flow_textures: dict[str, dict[str, dict]],
) -> dict:
    """Prove the nine shared families are source-byte-identical, not copied in UE."""
    stage_manifest = read_json(SHARED_SOURCE_TEXTURE_MANIFEST)
    if stage_manifest.get("asset_pack") != "CA_PTA_S03S06_StagePack_v001":
        fail("StagePack texture manifest is not its approved v001 authority")
    stage_families = stage_manifest.get("families")
    if not isinstance(stage_families, dict) or set(stage_families) != set(SHARED_FAMILIES):
        fail("StagePack texture-family closure drifted")

    results = {}
    for family in SHARED_FAMILIES:
        stage_row = stage_families[family]
        if stage_row.get("material_slot") != semantic_slot(family):
            fail("StagePack {} semantic slot drifted".format(family))
        stage_maps = stage_row.get("maps")
        if not isinstance(stage_maps, dict) or set(stage_maps) != set(CHANNELS):
            fail("StagePack {} map-channel closure drifted".format(family))
        results[family] = {}
        for channel in CHANNELS:
            map_row = stage_maps[channel]
            expected_relative = "Textures/{}.png".format(texture_name(family, channel))
            expected_hash = material_flow_textures[family][channel]["sha256"]
            if (map_row.get("file") != expected_relative
                    or str(map_row.get("sha256", "")).lower() != expected_hash):
                fail("{} {} no longer matches the StagePack source manifest".format(
                    family, channel))
            stage_path = SHARED_SOURCE_ASSET_DIR / expected_relative
            if not stage_path.is_file() or sha256(stage_path) != expected_hash:
                fail("{} {} StagePack source map hash drifted".format(family, channel))
            results[family][channel] = {
                "material_flow_source": str(material_flow_textures[family][channel]["path"]),
                "stagepack_source": str(stage_path),
                "sha256": expected_hash,
                "byte_identical": True,
            }
    return results


def validate_source_authorities() -> dict:
    """Validate the immutable source, RuntimePrep stats, and raw-FBX audit."""
    source_manifest = read_json(SOURCE_MANIFEST)
    texture_manifest = read_json(SOURCE_TEXTURE_MANIFEST)
    runtime_stats = read_json(SOURCE_RUNTIME_STATS)
    payload_audit = read_json(SOURCE_PAYLOAD_AUDIT)

    if source_manifest.get("asset_pack") != "CA_PressShop_MaterialFlowPack_v001":
        fail("Material Flow source manifest has the wrong asset-pack identity")
    if source_manifest.get("coordinate_system") != COORDINATE_SYSTEM:
        fail("Material Flow source coordinate-system contract drifted")
    if runtime_stats.get("coordinate_system") != COORDINATE_SYSTEM:
        fail("Material Flow RuntimePrep coordinate-system contract drifted")
    if runtime_stats.get("source_blend_sha256") != SOURCE_BLEND_SHA256:
        fail("RuntimePrep source blend provenance hash drifted")
    if not SOURCE_BLEND.is_file() or sha256(SOURCE_BLEND) != SOURCE_BLEND_SHA256:
        fail("source blend does not match RuntimePrep provenance")
    if "negates Y" not in str(runtime_stats.get("convert_scene_note", "")):
        fail("RuntimePrep does not document the Convert Scene Y-negation")
    if runtime_stats.get("uv_channels") != [
            "UVMap (tiling, 1 UV tile per 2 m)",
            "UV_Unique (non-overlapping, re-packed per mesh here)",
    ]:
        fail("RuntimePrep top-level UV contract drifted")

    expected_slots = {
        "S01": [0, -4350, 0],
        "S02_reserved": [0, -2900, 0],
        "S07": [0, 4350, 0],
    }
    if source_manifest.get("station_slots_source_cm") != expected_slots:
        fail("source station-slot contract drifted")
    if runtime_stats.get("station_slots_source_cm") != expected_slots:
        fail("RuntimePrep station-slot contract drifted")
    reconstruction = runtime_stats.get("reconstruction")
    if not isinstance(reconstruction, dict):
        fail("RuntimePrep reconstruction evidence is missing")
    if (reconstruction.get("exported_triangles_total") != 3792
            or reconstruction.get("triangles_match_source") is not True
            or reconstruction.get("per_station_bounds_error_m") != {"S01": 0.0, "S07": 0.0}):
        fail("RuntimePrep reconstruction contract drifted")

    if payload_audit.get("status") != "PASS__MATERIAL_FLOW_FBX_PAYLOAD_MATCHES_RUNTIMEPREP":
        fail("the required raw-FBX payload audit is not a pass")
    if payload_audit.get("failures") != []:
        fail("the raw-FBX payload audit has failures")
    if (payload_audit.get("published_exported_triangles_total") != 3792
            or payload_audit.get("audited_exported_triangles_total") != 3792
            or payload_audit.get("source_runtimeprep_stats_sha256") != sha256(SOURCE_RUNTIME_STATS)):
        fail("raw-FBX payload audit no longer matches current RuntimePrep stats")

    source_modules = source_manifest.get("modules")
    runtime_modules = runtime_stats.get("modules")
    payload_modules = payload_audit.get("modules")
    if not isinstance(source_modules, dict) or set(source_modules) != set(EXPECTED_MODULES):
        fail("source module closure drifted")
    if not isinstance(runtime_modules, dict) or set(runtime_modules) != set(EXPECTED_MODULES):
        fail("RuntimePrep module closure drifted")
    if not isinstance(payload_modules, dict) or set(payload_modules) != set(EXPECTED_MODULES):
        fail("raw-FBX payload-audit module closure drifted")

    mesh_specs = {}
    fbx_hashes = {}
    for module_name, contract in EXPECTED_MODULES.items():
        source_module = source_modules[module_name]
        runtime_module = runtime_modules[module_name]
        payload_module = payload_modules[module_name]
        if source_module.get("station") != contract["station"]:
            fail("source {} station drifted".format(module_name))
        if runtime_module.get("station") != contract["station"]:
            fail("RuntimePrep {} station drifted".format(module_name))
        if tuple(runtime_module.get("placement_slot_cm", ())) != contract["placement_slot_cm"]:
            fail("RuntimePrep {} placement drifted".format(module_name))
        if tuple(runtime_module.get("rotation", ())) != (0, 0, 0):
            fail("RuntimePrep {} rotation is no longer yaw-free".format(module_name))
        if runtime_module.get("file") != contract["file"]:
            fail("RuntimePrep {} FBX filename drifted".format(module_name))
        fbx_path = SOURCE_PREP_DIR / contract["file"]
        fbx_hash = str(runtime_module.get("fbx_sha256", "")).lower()
        if not re.fullmatch(r"[0-9a-f]{64}", fbx_hash):
            fail("RuntimePrep {} FBX hash is invalid".format(module_name))
        if not fbx_path.is_file() or sha256(fbx_path) != fbx_hash:
            fail("RuntimePrep {} FBX has drifted".format(module_name))
        if payload_module.get("sha256") != fbx_hash or payload_module.get("published_sha256") != fbx_hash:
            fail("raw-FBX payload audit hash drifted for {}".format(module_name))
        fbx_hashes[module_name] = fbx_hash

        source_meshes = source_module.get("meshes")
        runtime_meshes = runtime_module.get("meshes")
        payload_meshes = payload_module.get("meshes")
        if not isinstance(source_meshes, dict) or set(source_meshes) != set(contract["meshes"]):
            fail("source {} mesh closure drifted".format(module_name))
        if not isinstance(runtime_meshes, dict) or set(runtime_meshes) != set(contract["meshes"]):
            fail("RuntimePrep {} mesh closure drifted".format(module_name))
        if not isinstance(payload_meshes, dict) or set(payload_meshes) != set(contract["meshes"]):
            fail("raw-FBX payload {} mesh closure drifted".format(module_name))

        for mesh_name in contract["meshes"]:
            source_mesh = source_meshes[mesh_name]
            runtime_mesh = runtime_meshes[mesh_name]
            payload_mesh = payload_meshes[mesh_name]
            for field in (
                    "local_aabb_min_m", "local_aabb_max_m", "material_slots",
                    "triangles", "uv_layers", "root",
            ):
                if source_mesh.get(field) != runtime_mesh.get(field):
                    fail("{} {} differs between source and RuntimePrep".format(
                        module_name, mesh_name))
            if runtime_mesh.get("triangles") != EXPECTED_TRIANGLES[mesh_name]:
                fail("{} triangle contract drifted".format(mesh_name))
            if tuple(runtime_mesh.get("uv_layers", ())) != ("UVMap", "UV_Unique"):
                fail("{} UV-layer contract drifted".format(mesh_name))
            tuple3(runtime_mesh.get("local_aabb_min_m"), mesh_name + " source bounds min")
            tuple3(runtime_mesh.get("local_aabb_max_m"), mesh_name + " source bounds max")
            slots = runtime_mesh.get("material_slots")
            if not isinstance(slots, list) or not slots:
                fail("{} has no semantic material slots".format(mesh_name))
            if any(slot not in {semantic_slot(family) for family in ALL_FAMILIES} for slot in slots):
                fail("{} has an unknown semantic material slot".format(mesh_name))
            if payload_mesh.get("triangles") != EXPECTED_TRIANGLES[mesh_name]:
                fail("raw-FBX payload triangle count drifted for {}".format(mesh_name))
            if tuple(payload_mesh.get("uv_layers", ())) != ("UVMap", "UV_Unique"):
                fail("raw-FBX payload UV closure drifted for {}".format(mesh_name))
            payload_slots = tuple(
                normalise_terminal_blender_slot_suffix(slot)
                for slot in payload_mesh.get("material_slots_raw", ())
            )
            if payload_slots != tuple(slots):
                fail("raw-FBX payload semantic slot order drifted for {}".format(mesh_name))

            is_mover = mesh_name in MOVER_MESHES
            expected_root = MOVER_ROOT if is_mover else STATION_ROOT
            if runtime_mesh.get("root") != expected_root:
                fail("{} source root contract drifted".format(mesh_name))
            object_location = tuple3(payload_mesh.get("object_location"), mesh_name + " payload location")
            if is_mover:
                mover = MOVER_MESHES[mesh_name]
                if (runtime_mesh.get("pivot") != mover["pivot"]
                        or tuple3(runtime_mesh.get("parked_offset_m"), mesh_name + " parked offset")
                        != mover["parked_offset_m"]
                        or runtime_mesh.get("motion") != mover["motion"]):
                    fail("{} mover provenance drifted".format(mesh_name))
                if not within_tolerance(object_location, mover["parked_offset_m"], 0.0001):
                    fail("{} raw-FBX parked offset drifted".format(mesh_name))
            elif not within_tolerance(object_location, (0.0, 0.0, 0.0), 0.0001):
                fail("{} station-root FBX unexpectedly carries a node offset".format(mesh_name))
            mesh_specs[mesh_name] = runtime_mesh

    if set(mesh_specs) != set(EXPECTED_TRIANGLES):
        fail("ten-mesh source closure is incomplete")
    if sum(int(spec["triangles"]) for spec in mesh_specs.values()) != 3792:
        fail("source triangle total is not 3,792")

    textures = source_texture_specs(texture_manifest)
    shared_reuse = validate_shared_source_texture_reuse(textures)
    return {
        "source_manifest_sha256": sha256(SOURCE_MANIFEST),
        "source_texture_manifest_sha256": sha256(SOURCE_TEXTURE_MANIFEST),
        "source_runtimeprep_stats_sha256": sha256(SOURCE_RUNTIME_STATS),
        "source_payload_audit_sha256": sha256(SOURCE_PAYLOAD_AUDIT),
        "source_blend_sha256": SOURCE_BLEND_SHA256,
        "runtimeprep_fbx_sha256": fbx_hashes,
        "source_textures": textures,
        "shared_source_texture_reuse": shared_reuse,
        "mesh_specs": mesh_specs,
        "runtime_stats": runtime_stats,
    }


def audit_import_receipt(source_proof: dict) -> dict:
    """The native audit does not trust the importer receipt blindly; it cross-checks it."""
    receipt = read_json(IMPORT_RECEIPT)
    if receipt.get("status") != "PASS__MATERIAL_FLOW_V001_IMPORTED_AS_TEN_SEMANTIC_MESHES":
        fail("Material Flow import receipt is not a successful ten-mesh import")
    if receipt.get("destination") != DESTINATION:
        fail("Material Flow import receipt destination drifted")
    if receipt.get("source_blend_sha256") != SOURCE_BLEND_SHA256:
        fail("Material Flow import receipt source blend hash drifted")
    for key in (
            "source_matflow_manifest_sha256", "source_texture_manifest_sha256",
            "source_runtimeprep_stats_sha256", "source_payload_audit_sha256",
    ):
        expected = {
            "source_matflow_manifest_sha256": source_proof["source_manifest_sha256"],
            "source_texture_manifest_sha256": source_proof["source_texture_manifest_sha256"],
            "source_runtimeprep_stats_sha256": source_proof["source_runtimeprep_stats_sha256"],
            "source_payload_audit_sha256": source_proof["source_payload_audit_sha256"],
        }[key]
        if receipt.get(key) != expected:
            fail("Material Flow import receipt {} drifted".format(key))
    if (receipt.get("source_payload_triangles") != 3792
            or receipt.get("native_mesh_count") != 10
            or receipt.get("native_package_count") != 30
            or receipt.get("fbx_combine_meshes") is not False
            or receipt.get("auto_generated_collision") is not False
            or receipt.get("imported_materials_from_fbx") is not False
            or receipt.get("imported_textures_from_fbx") is not False):
        fail("Material Flow import receipt import-policy evidence drifted")
    if receipt.get("new_texture_families") != list(NEW_FAMILIES):
        fail("Material Flow import receipt new texture family closure drifted")
    if set(receipt.get("mover_pivots_preserved", ())) != set(MOVER_MESHES):
        fail("Material Flow import receipt mover-pivot declaration drifted")

    expected_import_assets = expected_native_asset_paths()
    if {canonical_asset_path(path) for path in receipt.get("native_assets", ())} != expected_import_assets:
        fail("Material Flow import receipt native asset closure drifted")

    shared = receipt.get("shared_stagepack_reuse")
    if not isinstance(shared, dict):
        fail("Material Flow import receipt omits StagePack reuse evidence")
    if (shared.get("destination") != SHARED_DESTINATION
            or shared.get("source_texture_manifest_sha256")
            != sha256(SHARED_SOURCE_TEXTURE_MANIFEST)):
        fail("Material Flow import receipt StagePack reuse provenance drifted")
    source_reuse = shared.get("byte_identical_source_texture_families")
    if not isinstance(source_reuse, dict) or set(source_reuse) != set(SHARED_FAMILIES):
        fail("Material Flow import receipt shared texture reuse closure drifted")
    for family in SHARED_FAMILIES:
        if set(source_reuse[family]) != set(CHANNELS):
            fail("Material Flow import receipt shared {} map closure drifted".format(family))
        for channel in CHANNELS:
            row = source_reuse[family][channel]
            expected_hash = source_proof["source_textures"][family][channel]["sha256"]
            if row.get("sha256") != expected_hash or row.get("byte_identical") is not True:
                fail("Material Flow import receipt shared {} {} hash evidence drifted".format(
                    family, channel))

    modules = receipt.get("modules")
    if not isinstance(modules, dict) or set(modules) != set(EXPECTED_MODULES):
        fail("Material Flow import receipt module closure drifted")
    mesh_receipts = {}
    for module_name, contract in EXPECTED_MODULES.items():
        module = modules[module_name]
        if (module.get("station") != contract["station"]
                or tuple(module.get("placement_slot_source_cm", ())) != contract["placement_slot_cm"]
                or tuple(module.get("rotation_source", ())) != (0, 0, 0)
                or module.get("source_fbx_sha256")
                != source_proof["runtimeprep_fbx_sha256"][module_name]):
            fail("Material Flow import receipt {} module provenance drifted".format(module_name))
        meshes = module.get("meshes")
        if not isinstance(meshes, dict) or set(meshes) != set(contract["meshes"]):
            fail("Material Flow import receipt {} mesh closure drifted".format(module_name))
        for mesh_name in contract["meshes"]:
            row = meshes[mesh_name]
            spec = source_proof["mesh_specs"][mesh_name]
            expected_min, expected_max = converted_source_bounds_cm(spec)
            if (row.get("mesh_object_path") != expected_mesh_path(mesh_name)
                    or row.get("source_triangles") != EXPECTED_TRIANGLES[mesh_name]
                    or row.get("unreal_render_triangles") != EXPECTED_TRIANGLES[mesh_name]
                    or row.get("lod_count") != 1
                    or row.get("unreal_uv_channels") != 2
                    or row.get("combine_meshes") is not False
                    or row.get("transform_vertex_to_absolute") is not False
                    or row.get("bake_pivot_in_vertex") is not False
                    or row.get("auto_generated_collision") is not False):
                fail("Material Flow import receipt mesh policy drifted for {}".format(mesh_name))
            expected_bounds = row.get("expected_unreal_aabb_cm_after_convert_scene", {})
            actual_bounds = row.get("unreal_aabb_cm", {})
            if (tuple(expected_bounds.get("min", ())) != expected_min
                    or tuple(expected_bounds.get("max", ())) != expected_max
                    or not within_tolerance(actual_bounds.get("min", ()), expected_min, 0.25)
                    or not within_tolerance(actual_bounds.get("max", ()), expected_max, 0.25)):
                fail("Material Flow import receipt bounds drifted for {}".format(mesh_name))
            if tuple(row.get("semantic_slots", ())) != tuple(spec["material_slots"]):
                fail("Material Flow import receipt semantic slots drifted for {}".format(mesh_name))
            if row.get("source_root_contract") != spec["root"]:
                fail("Material Flow import receipt root contract drifted for {}".format(mesh_name))
            if mesh_name in MOVER_MESHES:
                mover = row.get("mover")
                if not mover_contract_matches(mover, MOVER_MESHES[mesh_name],
                                              mesh_name + " importer mover"):
                    fail("Material Flow import receipt mover evidence drifted for {}".format(mesh_name))
            elif row.get("mover") is not None:
                fail("Material Flow import receipt incorrectly marks {} as a mover".format(mesh_name))
            mesh_receipts[mesh_name] = row

    return {
        "sha256": sha256(IMPORT_RECEIPT),
        "status": receipt["status"],
        "mesh_receipts": mesh_receipts,
        "receipt": receipt,
    }


def expected_sampler_type(parameter: str):
    return {
        "BaseColorMap": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
        "NormalMap": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
        "ORMMap": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
        "WearMaskMap": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    }[parameter]


def audit_shared_master() -> dict:
    master = unreal.load_asset(MASTER_PATH)
    if not master or not isinstance(master, unreal.Material):
        fail("shared StagePack master does not resolve to a Material")
    blend_mode = master.get_editor_property("blend_mode")
    two_sided = bool(master.get_editor_property("two_sided"))
    if enum_name(blend_mode) != "BLEND_OPAQUE" or two_sided:
        fail("shared StagePack master is not the required opaque one-sided material")

    defaults = {}
    for parameter, channel in TEXTURE_PARAMETERS.items():
        actual = unreal.MaterialEditingLibrary.get_material_default_texture_parameter_value(
            master, parameter)
        expected = expected_shared_texture_path("FoundryCharcoal", channel)
        defaults[parameter] = asset_path(actual)
        if defaults[parameter] != expected:
            fail("shared StagePack master {} default map drifted".format(parameter))
    raw_dust = float(unreal.MaterialEditingLibrary.get_material_default_scalar_parameter_value(
        master, "RawDustStrength"))
    if abs(raw_dust) > 0.0001:
        fail("shared StagePack master RawDustStrength is not zero")

    expressions = list(unreal.MaterialEditingLibrary.get_material_expressions(master))
    samples = {
        str(node.get_editor_property("parameter_name")): node
        for node in expressions
        if isinstance(node, unreal.MaterialExpressionTextureSampleParameter2D)
    }
    if set(samples) != set(TEXTURE_PARAMETERS):
        fail("shared StagePack master texture-sample graph closure drifted")
    sampler_results = {}
    for parameter in TEXTURE_PARAMETERS:
        actual = samples[parameter].get_editor_property("sampler_type")
        sampler_results[parameter] = str(actual)
        if actual != expected_sampler_type(parameter):
            fail("shared StagePack master {} sampler type drifted".format(parameter))

    expected_mask_inputs = {
        320: "ORMMap",
        400: "ORMMap",
        480: "ORMMap",
        600: "WearMaskMap",
    }
    masks = [
        node for node in expressions
        if isinstance(node, unreal.MaterialExpressionComponentMask)
    ]
    by_y = {int(node.get_editor_property("material_expression_editor_y")): node for node in masks}
    if len(masks) != 4 or set(by_y) != set(expected_mask_inputs):
        fail("shared StagePack master ComponentMask graph shape drifted")
    mask_results = {}
    for y, expected_parameter in sorted(expected_mask_inputs.items()):
        node = by_y[y]
        inputs = list(unreal.MaterialEditingLibrary.get_inputs_for_material_expression(
            master, node))
        source = inputs[0] if len(inputs) == 1 else None
        source_parameter = (
            str(source.get_editor_property("parameter_name"))
            if source and isinstance(source, unreal.MaterialExpressionTextureSampleParameter2D)
            else None
        )
        output = (
            str(unreal.MaterialEditingLibrary.get_input_node_output_name_for_material_expression(
                node, source))
            if source else None
        )
        mask_results[str(y)] = {
            "source_parameter": source_parameter,
            "output": output,
        }
        if source_parameter != expected_parameter or output != "RGB":
            fail("shared StagePack master ComponentMask y={} wiring drifted".format(y))

    return {
        "path": MASTER_PATH,
        "blend_mode": enum_name(blend_mode),
        "two_sided": two_sided,
        "texture_defaults": defaults,
        "RawDustStrength": raw_dust,
        "samplers": sampler_results,
        "component_mask_inputs": mask_results,
    }


def audit_texture(texture_path: str, channel: str, source_record: dict) -> dict:
    texture = unreal.load_asset(texture_path)
    if not texture or not isinstance(texture, unreal.Texture):
        fail("{} does not resolve to a Texture".format(texture_path))
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
    if (srgb != expected_srgb or compression != expected_compression
            or flip_green != (channel == "N")):
        fail("{} import settings drifted".format(texture_path))
    return {
        "path": asset_path(texture),
        "source_path": str(source_record["path"]),
        "source_sha256": source_record["sha256"],
        "srgb": srgb,
        "compression": str(compression),
        "flip_green_channel": flip_green,
    }


def audit_material_instance(
        family: str,
        material_path: str,
        texture_paths: dict[str, str],
        expected_dust: float,
) -> dict:
    material = unreal.load_asset(material_path)
    if not material or not isinstance(material, unreal.MaterialInstanceConstant):
        fail("{} does not resolve to a MaterialInstanceConstant".format(material_path))
    parent = asset_path(material.get_editor_property("parent"))
    if parent != MASTER_PATH:
        fail("{} parent drifted from shared StagePack master".format(family))
    parameters = {}
    for parameter, channel in TEXTURE_PARAMETERS.items():
        texture = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
            material, parameter)
        parameters[parameter] = asset_path(texture)
        if parameters[parameter] != texture_paths[channel]:
            fail("{} {} map drifted".format(family, parameter))
    dust = float(unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(
        material, "RawDustStrength"))
    if abs(dust - expected_dust) > 0.0001:
        fail("{} RawDustStrength drifted".format(family))
    return {
        "path": asset_path(material),
        "parent": parent,
        "texture_parameters": parameters,
        "RawDustStrength": dust,
    }


def audit_material_closure(source_proof: dict) -> dict:
    """Verify local new maps/MIs and live StagePack reuse without duplication."""
    expected_shared_texture_assets = {
        expected_shared_texture_path(family, channel)
        for family in SHARED_FAMILIES for channel in CHANNELS
    }
    expected_shared_material_assets = {
        expected_shared_material_path(family) for family in SHARED_FAMILIES
    }
    actual_shared_texture_assets = list_asset_paths(SHARED_TEXTURE_DESTINATION)
    actual_shared_material_assets = list_asset_paths(SHARED_MATERIAL_DESTINATION)
    if actual_shared_texture_assets != expected_shared_texture_assets:
        fail("shared StagePack texture folder is not the exact 36-texture closure")
    if actual_shared_material_assets != expected_shared_material_assets | {MASTER_PATH}:
        fail("shared StagePack material folder is not the exact nine-MI-plus-master closure")

    material_flow_assets = list_asset_paths(DESTINATION)
    duplicated_shared_assets = material_flow_assets & (
        expected_shared_texture_assets | expected_shared_material_assets | {MASTER_PATH}
    )
    if duplicated_shared_assets:
        fail("Material Flow destination duplicates StagePack shared assets: {}".format(
            sorted(duplicated_shared_assets)))

    master_result = audit_shared_master()
    shared_textures = {}
    shared_materials = {}
    for family in SHARED_FAMILIES:
        texture_paths = {}
        for channel in CHANNELS:
            path = expected_shared_texture_path(family, channel)
            texture_paths[channel] = path
            shared_textures[texture_name(family, channel)] = audit_texture(
                path, channel, source_proof["source_textures"][family][channel])
        shared_materials[family] = audit_material_instance(
            family, expected_shared_material_path(family), texture_paths,
            SHARED_FAMILY_DUST[family])

    new_textures = {}
    new_materials = {}
    for family in NEW_FAMILIES:
        texture_paths = {}
        for channel in CHANNELS:
            path = expected_new_texture_path(family, channel)
            texture_paths[channel] = path
            new_textures[texture_name(family, channel)] = audit_texture(
                path, channel, source_proof["source_textures"][family][channel])
        new_materials[family] = audit_material_instance(
            family, expected_new_material_path(family), texture_paths,
            NEW_FAMILY_DUST[family])

    return {
        "master": master_result,
        "shared_stagepack": {
            "destination": SHARED_DESTINATION,
            "texture_asset_count": len(shared_textures),
            "material_instance_count": len(shared_materials),
            "textures": shared_textures,
            "material_instances": shared_materials,
        },
        "new_material_flow": {
            "destination": DESTINATION,
            "texture_asset_count": len(new_textures),
            "material_instance_count": len(new_materials),
            "textures": new_textures,
            "material_instances": new_materials,
        },
        "duplicate_shared_assets_in_material_flow": [],
    }


def audit_native_meshes(source_proof: dict, import_proof: dict) -> dict:
    mesh_editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if mesh_editor is None or not hasattr(mesh_editor, "get_num_uv_channels"):
        fail("UE 5.8 StaticMeshEditorSubsystem UV query is unavailable")
    if not hasattr(unreal, "EditorStaticMeshLibrary"):
        fail("UE 5.8 EditorStaticMeshLibrary collision query is unavailable")

    results = {}
    for mesh_name in sorted(EXPECTED_TRIANGLES):
        mesh_path = expected_mesh_path(mesh_name)
        mesh = unreal.load_asset(mesh_path)
        if not mesh or not isinstance(mesh, unreal.StaticMesh):
            fail("{} does not resolve to a StaticMesh".format(mesh_path))
        spec = source_proof["mesh_specs"][mesh_name]
        expected_min, expected_max = converted_source_bounds_cm(spec)
        bounds = mesh.get_bounding_box()
        actual_min = vector_tuple(bounds.min)
        actual_max = vector_tuple(bounds.max)
        triangles = int(mesh.get_num_triangles(0))
        lod_count = int(mesh.get_num_lods())
        uv_channels = int(mesh_editor.get_num_uv_channels(mesh, 0))
        try:
            simple_collision = int(unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh))
            convex_collision = int(unreal.EditorStaticMeshLibrary.get_convex_collision_count(mesh))
        except Exception as error:
            fail("{} collision query failed: {}".format(mesh_name, error))
        slots = tuple(str(slot.get_editor_property("material_slot_name"))
                      for slot in mesh.get_editor_property("static_materials"))
        material_paths = tuple(asset_path(slot.get_editor_property("material_interface"))
                               for slot in mesh.get_editor_property("static_materials"))
        expected_slots = tuple(spec["material_slots"])
        expected_material_paths = tuple(
            expected_shared_material_path(slot.removeprefix("CA_MW_"))
            if slot.removeprefix("CA_MW_") in SHARED_FAMILIES
            else expected_new_material_path(slot.removeprefix("CA_MW_"))
            for slot in expected_slots
        )
        if triangles != EXPECTED_TRIANGLES[mesh_name]:
            fail("{} UE LOD0 triangles={} rather than {}".format(
                mesh_name, triangles, EXPECTED_TRIANGLES[mesh_name]))
        if lod_count != 1 or uv_channels != 2:
            fail("{} must remain LOD0-only with exactly two UV channels".format(mesh_name))
        if not within_tolerance(actual_min, expected_min, 0.25) or not within_tolerance(
                actual_max, expected_max, 0.25):
            fail("{} AABB does not preserve Convert Scene pivot-local bounds".format(mesh_name))
        if slots != expected_slots or material_paths != expected_material_paths:
            fail("{} semantic slot/material binding drifted".format(mesh_name))
        if (simple_collision != 0 or convex_collision != 0):
            fail("{} has authored collision despite the source-candidate policy".format(mesh_name))
        if (int(mesh.get_editor_property("light_map_coordinate_index")) != 1
                or int(mesh.get_editor_property("light_map_resolution")) != 128):
            fail("{} lightmap UV policy drifted".format(mesh_name))

        importer_mesh = import_proof["mesh_receipts"][mesh_name]
        is_mover = mesh_name in MOVER_MESHES
        if is_mover:
            mover_evidence = MOVER_MESHES[mesh_name]
            if (spec["root"] != MOVER_ROOT
                    or not mover_contract_matches(
                        importer_mesh.get("mover"), mover_evidence,
                        mesh_name + " native mover")):
                fail("{} mover pivot evidence drifted".format(mesh_name))
        else:
            mover_evidence = None
            if spec["root"] != STATION_ROOT or importer_mesh.get("mover") is not None:
                fail("{} station-root evidence drifted".format(mesh_name))
        results[mesh_name] = {
            "path": asset_path(mesh),
            "source_triangles": EXPECTED_TRIANGLES[mesh_name],
            "unreal_render_triangles": triangles,
            "lod_count": lod_count,
            "uv_channels": uv_channels,
            "light_map_coordinate_index": int(mesh.get_editor_property("light_map_coordinate_index")),
            "light_map_resolution": int(mesh.get_editor_property("light_map_resolution")),
            "source_root_contract": spec["root"],
            "mover_pivot_evidence": mover_evidence,
            "expected_unreal_aabb_cm_after_convert_scene": {
                "min": list(expected_min), "max": list(expected_max),
            },
            "unreal_aabb_cm": {"min": list(actual_min), "max": list(actual_max)},
            "semantic_slots": list(slots),
            "default_materials": list(material_paths),
            "simple_collision_count": simple_collision,
            "convex_collision_count": convex_collision,
        }
    if sum(result["unreal_render_triangles"] for result in results.values()) != 3792:
        fail("native Material Flow triangle total is not 3,792")
    return results


def audit() -> dict:
    source_proof = validate_source_authorities()
    import_proof = audit_import_receipt(source_proof)

    expected_assets = expected_native_asset_paths()
    actual_assets = list_asset_paths(DESTINATION)
    if actual_assets != expected_assets:
        fail("Material Flow destination is not the exact 30-package closure")
    actual_packages = {package_path(path) for path in actual_assets}
    expected_packages = {package_path(path) for path in expected_assets}
    if len(actual_packages) != 30 or actual_packages != expected_packages:
        fail("Material Flow native package count/identity is not exactly 30")

    material_proof = audit_material_closure(source_proof)
    mesh_proof = audit_native_meshes(source_proof, import_proof)
    return {
        "$schema": "lineboss/audit/onefactory/press/material-flow-v001-native/v1",
        "generated_utc": now(),
        "status": "PASS__MATERIAL_FLOW_V001_CURRENT_NATIVE_CLOSURE",
        "write_scope": [],
        "content_writes": [],
        "map_loaded_or_saved": [],
        "source_or_importer_rerun": False,
        "destination": DESTINATION,
        "native_package_count": len(actual_packages),
        "native_assets": sorted(actual_assets),
        "source_provenance": {
            "source_blend_sha256": source_proof["source_blend_sha256"],
            "matflow_manifest_sha256": source_proof["source_manifest_sha256"],
            "texture_manifest_sha256": source_proof["source_texture_manifest_sha256"],
            "runtimeprep_stats_sha256": source_proof["source_runtimeprep_stats_sha256"],
            "fbx_payload_audit_sha256": source_proof["source_payload_audit_sha256"],
            "runtimeprep_fbx_sha256": source_proof["runtimeprep_fbx_sha256"],
            "shared_source_texture_reuse": source_proof["shared_source_texture_reuse"],
        },
        "import_receipt": {
            "path": str(IMPORT_RECEIPT),
            "sha256": import_proof["sha256"],
            "status": import_proof["status"],
        },
        "materials": material_proof,
        "meshes": mesh_proof,
        "native_triangle_total": sum(
            mesh["unreal_render_triangles"] for mesh in mesh_proof.values()),
        "failures": [],
    }


def write_new_receipt(result: dict) -> Path:
    """Never overwrite evidence: use base, then monotonically numbered retries."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    index = 0
    while True:
        suffix = "" if index == 0 else "_retry{}".format(index)
        candidate = AUDIT_DIR / "{}{}.json".format(RECEIPT_BASENAME, suffix)
        result["write_scope"] = [str(candidate)]
        try:
            with candidate.open("x", encoding="utf-8") as handle:
                json.dump(result, handle, indent=2, sort_keys=True)
                handle.write("\n")
            return candidate
        except FileExistsError:
            index += 1


def safe_snapshot(root: Path) -> dict:
    try:
        return snapshot_tree(root)
    except Exception as error:
        return {"snapshot_error": str(error), "root": str(root)}


def safe_source_snapshot() -> dict:
    try:
        return snapshot_source_authorities()
    except Exception as error:
        return {"snapshot_error": str(error)}


def main() -> None:
    native_before = safe_snapshot(NATIVE_CONTENT_ROOT)
    source_before = safe_source_snapshot()
    try:
        if "snapshot_error" in native_before or "snapshot_error" in source_before:
            fail("could not establish a pre-audit content/source fingerprint")
        result = audit()
        native_after = safe_snapshot(NATIVE_CONTENT_ROOT)
        source_after = safe_source_snapshot()
        if "snapshot_error" in native_after or "snapshot_error" in source_after:
            fail("could not establish a post-audit content/source fingerprint")
        result["native_content_snapshot_before"] = native_before
        result["native_content_snapshot_after"] = native_after
        result["native_content_unchanged"] = native_before == native_after
        result["source_authority_snapshot_before"] = source_before
        result["source_authority_snapshot_after"] = source_after
        result["source_authorities_unchanged"] = source_before == source_after
        if not result["native_content_unchanged"]:
            fail("read-only audit mutated native Content")
        if not result["source_authorities_unchanged"]:
            fail("read-only audit mutated source authorities")
        receipt = write_new_receipt(result)
        unreal.log("MATERIAL_FLOW_V001_NATIVE_AUDIT_PASS=" + str(receipt))
        unreal.SystemLibrary.quit_editor()
    except Exception as error:
        failure = {
            "$schema": "lineboss/audit/onefactory/press/material-flow-v001-native/v1",
            "generated_utc": now(),
            "status": "FAIL__MATERIAL_FLOW_V001_CURRENT_NATIVE_CLOSURE",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "content_writes": [],
            "map_loaded_or_saved": [],
            "source_or_importer_rerun": False,
            "native_content_snapshot_before": native_before,
            "native_content_snapshot_after": safe_snapshot(NATIVE_CONTENT_ROOT),
            "source_authority_snapshot_before": source_before,
            "source_authority_snapshot_after": safe_source_snapshot(),
            "write_scope": [],
        }
        failure["native_content_unchanged"] = (
            failure["native_content_snapshot_before"]
            == failure["native_content_snapshot_after"]
        )
        failure["source_authorities_unchanged"] = (
            failure["source_authority_snapshot_before"]
            == failure["source_authority_snapshot_after"]
        )
        # Even a filesystem failure while recording the failed audit must not
        # leave a live editor session behind.  The receipt remains exclusive
        # create-only whenever the filesystem permits it.
        try:
            receipt = write_new_receipt(failure)
            unreal.log_error("MATERIAL_FLOW_V001_NATIVE_AUDIT_FAIL=" + str(receipt))
        finally:
            unreal.SystemLibrary.quit_editor()
        raise


if __name__ == "__main__":
    main()
