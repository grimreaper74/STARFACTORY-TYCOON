"""Build v232 directly from v230 with a robust pale-silver outer-wrap response."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v230"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v232"
DEST = "/Game/LineBoss/Candidates/PressShop/PackagedCoilSurface_v232/Materials"
MATERIAL_NAME = "MI_CA_MW_PaleSilverProtectiveWrap_v232"
MASTER = "/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/M_LB_PR004_NonmetalPBR_Master_v003"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_packaged_coil_surface_build_v232.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v230.umap"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
material_path = f"{DEST}/{MATERIAL_NAME}"
if library.does_asset_exist(material_path):
    raise RuntimeError(f"refusing to overwrite preserved material {material_path}")
parent_hash_before = sha256(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

parent = library.load_asset(MASTER)
if parent is None:
    raise RuntimeError(f"missing nonmetal PBR master {MASTER}")
material = tools.create_asset(
    MATERIAL_NAME, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
if material is None:
    raise RuntimeError(f"could not create {material_path}")
material.set_editor_property("parent", parent)
mel.set_material_instance_vector_parameter_value(
    material, "SurfaceTint", unreal.LinearColor(0.84, 0.88, 0.92, 1.0))
for name, value in {
    "TextureInfluence": 0.08,
    "TextureScale": 18.0,
    "BaseRoughness": 0.62,
    "RoughTextureInfluence": 0.20,
    "Metallic": 0.0,
    "NormalStrength": 0.22,
}.items():
    mel.set_material_instance_scalar_parameter_value(material, name, value)
mel.update_material_instance(material)
library.save_loaded_asset(material, only_if_is_dirty=False)

changed = []
failures = []
for actor in actors_api.get_all_level_actors():
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is None or "SM_LB_MasterCoil_Candidate_v005" not in mesh.get_path_name():
            continue
        before = component.get_material(2)
        before_path = before.get_path_name() if before else None
        if "MI_CA_MW_PaleSilverPolyWrap_v118" not in (before_path or ""):
            failures.append(f"unexpected slot-2 source on {actor.get_actor_label()}: {before_path}")
            continue
        component.set_material(2, material)
        prior_tags = [str(value) for value in actor.tags]
        actor.tags = [unreal.Name(value) for value in dict.fromkeys(prior_tags + [
            "LB.Asset.Candidate.v232", "LB.Material.PackagedCoil.PaleSilverProtectiveWrap.v232",
            "LB.Asset.CandidateNotPromoted",
        ])]
        changed.append({
            "actor": actor.get_actor_label(),
            "component": component.get_name(),
            "before": before_path,
            "after": material.get_path_name(),
        })

if len(changed) != 15:
    failures.append(f"expected exactly 15 packaged-coil presentations, changed {len(changed)}")
pr003 = [row for row in changed if "CS-" in row["actor"]]
if len(pr003) != 12:
    failures.append(f"expected exactly 12 PR003 inventory identities including in-transfer CS-06, found {len(pr003)}")

if not levels.save_current_level():
    failures.append("could not save v232")
library.save_directory(DEST.rsplit("/", 1)[0], only_if_is_dirty=False, recursive=True)
parent_hash_after = sha256(BASE_FILE)
if parent_hash_after != parent_hash_before:
    failures.append("protected v230 parent changed")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v232.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-packaged-coil-surface-build-v232/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FIFTEEN_PACKAGED_COIL_OUTER_WRAP_SLOTS_OVERRIDDEN__FRESH_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(map_file) if map_file.exists() else None,
    "material": material.get_path_name(),
    "material_contract": {
        "surface": "pale silver protective wrapping",
        "metallic": 0.0,
        "base_roughness": 0.62,
        "engineering_data": "NONE_INVENTED"
    },
    "changed_component_count": len(changed),
    "changed_components": sorted(changed, key=lambda row: (row["actor"], row["component"])),
    "changed_material_slots": [2],
    "coil_geometry_transform_count_layout_or_identity_changes": 0,
    "strap_edge_label_saddle_changes": 0,
    "lighting_fixture_authority_machine_collision_navigation_changes": 0,
    "rejected_non_parent": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v231",
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
