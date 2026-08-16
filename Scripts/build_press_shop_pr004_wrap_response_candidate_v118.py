"""Build an isolated v118 packaged-coil surface correction from retained v117.

The v005 geometry, collision, native station/crane authority, floor correction,
and accepted lineage are preserved.  Only map-local material overrides on the
15 packaged-coil presentations change.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004ConcreteFloorCandidate_v117"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004WrapResponseCandidate_v118"
DEST = "/Game/LineBoss/Candidates/PressShop/PR004WrapResponse_v118/Materials"
MASTER = "/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003/M_LB_PR004_NonmetalPBR_Master_v003"
OUT = ROOT / "Saved/Audits/press_shop_pr004_wrap_response_build_v118.json"

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if lib.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not create isolated v118 from {BASE}")

parent = lib.load_asset(MASTER)
if parent is None:
    raise RuntimeError(f"missing wrap PBR master {MASTER}")


def material(name, tint, roughness, texture_influence, scale, normal_strength, rough_variation):
    value = tools.create_asset(name, DEST, unreal.MaterialInstanceConstant,
                               unreal.MaterialInstanceConstantFactoryNew())
    if value is None:
        raise RuntimeError(f"could not create {DEST}/{name}")
    value.set_editor_property("parent", parent)
    mel.set_material_instance_vector_parameter_value(value, "SurfaceTint", unreal.LinearColor(*tint, 1.0))
    for key, scalar in {
        "TextureInfluence": texture_influence,
        "TextureScale": scale,
        "BaseRoughness": roughness,
        "RoughTextureInfluence": rough_variation,
        "Metallic": 0.0,
        "NormalStrength": normal_strength,
    }.items():
        mel.set_material_instance_scalar_parameter_value(value, key, scalar)
    mel.update_material_instance(value)
    lib.save_loaded_asset(value, only_if_is_dirty=False)
    return value


# Linear values deliberately match the pale silver-grey protective wrap in the
# retained source render. Contrast lives in overlaps, patches and compressed
# fibre rather than turning the entire package charcoal.
materials = {
    2: material("MI_CA_MW_PaleSilverPolyWrap_v118", (0.42, 0.47, 0.54), 0.70, 0.24, 18.0, 0.28, 0.34),
    3: material("MI_CA_MW_PolyWrapOverlap_v118", (0.25, 0.30, 0.36), 0.77, 0.30, 20.0, 0.30, 0.38),
    4: material("MI_CA_MW_PolyWrapRepairPatch_v118", (0.16, 0.23, 0.31), 0.80, 0.34, 22.0, 0.32, 0.42),
    6: material("MI_CA_MW_CompressedFibreEdge_v118", (0.24, 0.105, 0.030), 0.92, 0.34, 18.0, 0.22, 0.38),
    8: material("MI_CA_MW_TraceabilityLabelPaper_v118", (0.72, 0.68, 0.58), 0.82, 0.10, 6.0, 0.06, 0.12),
}

changed = []
station_present = False
for actor in actors_api.get_all_level_actors():
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is None or "SM_LB_MasterCoil_Candidate_v005" not in mesh.get_path_name():
            continue
        before = {}
        for slot, replacement in materials.items():
            old = component.get_material(slot)
            before[str(slot)] = old.get_path_name() if old else None
            component.set_material(slot, replacement)
        prior_tags = [str(value) for value in actor.tags]
        actor.tags = [unreal.Name(value) for value in dict.fromkeys(prior_tags + [
            "LB.Asset.Candidate.v118", "LB.Material.PackagedCoil.PaleSilverPolyWrap.v118"
        ])]
        changed.append({
            "actor": actor.get_actor_label(),
            "component": component.get_name(),
            "before": before,
            "after": {str(slot): value.get_path_name() for slot, value in materials.items()},
        })
        if component.get_name() == "PR004_WrappedCoilVisual":
            station_present = True

failures = []
if len(changed) != 15:
    failures.append(f"expected 15 packaged-coil presentations, changed {len(changed)}")
if not station_present:
    failures.append("native PR-004 wrapped-coil component was not found")
if not levels.save_current_level():
    failures.append("could not save isolated v118")
lib.save_directory(DEST.rsplit("/", 1)[0], only_if_is_dirty=False, recursive=True)

report = {
    "$schema": "cairnwell/audit/press-shop-pr004-wrap-response-build-v118/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_V118_PALE_SILVER_POLY_WRAP_BUILT__VISUAL_AND_EXACT_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V118_WRAP_RESPONSE_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "changed_component_count": len(changed),
    "changed_material_slots": sorted(materials),
    "changes": changed,
    "geometry_changed": False,
    "collision_or_navigation_changed": False,
    "machinery_or_gameplay_authority_changed": False,
    "v117_changed": False,
    "promotion_authorized": False,
    "press_shop_complete": False,
    "failures": failures,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "changed_component_count": len(changed), "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
