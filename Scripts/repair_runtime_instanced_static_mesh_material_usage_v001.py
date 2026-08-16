"""Repair the exact runtime materials rejected by HISM/ISM components.

This script is deliberately allowlisted and idempotent.  It verifies that the
allowlist still matches the warnings captured in the source runtime log before
touching any asset, refuses to mutate a base material outside the Line Boss
project namespace, enables only MATUSAGE_InstancedStaticMeshes, recompiles each
unique base material, and resaves every affected material interface.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import unreal


PROJECT_ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE_LOG = PROJECT_ROOT / "Saved" / "Logs" / "ModernMockup_v010_floor_route_game_visible.log"
RECEIPT = (
    PROJECT_ROOT
    / "Saved"
    / "Audits"
    / "RuntimeMaterials"
    / "instanced_static_mesh_usage_repair_v001.json"
)

TARGETS = [
    # ED-line status indicators.
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_StatusGreen_v001",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_StatusAmber_v001",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_StatusRed_v001",
    # Body-weld/control-room HISM materials.
    "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_FoundryCharcoal_R_v002",
    "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_SafetyYellow_R_v002",
    "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_BrushedSteel_R_v002",
    # ED-line structural, process, service and validation materials.
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_Stainless_v001",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_StructuralSteel_Graphite_v001",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_PaintShop_Green_v001",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_SafetyYellow_v001",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_PaintShop_GreenLight_v001",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_Oven_InsulatedPanel_Alt_v001",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_Oven_InsulatedPanel_v001",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_ServiceLight_v001",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_RubberSeal_v001",
    # Inbound-coil HISM materials.
    "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/Material_0",
    "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/MI_CA_MW_WrappedCoil_StructuralCore",
]

WARNING_PATTERN = re.compile(
    r"Material (?P<asset>/Game/[^\s]+?)\.[^\s]+ missing usage flag InstancedStaticMeshes!"
)
USAGE_PROPERTY = "used_with_instanced_static_meshes"


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def package_file(package_path: str) -> Path:
    relative = package_path.removeprefix("/Game/") + ".uasset"
    return PROJECT_ROOT / "Content" / Path(relative)


def usage_flag() -> unreal.MaterialUsage:
    # The generated Python spelling has been stable, but the fallback keeps the
    # script explicit across minor UE revisions without accepting another usage.
    preferred = "MATUSAGE_INSTANCED_STATIC_MESHES"
    if hasattr(unreal.MaterialUsage, preferred):
        return getattr(unreal.MaterialUsage, preferred)
    candidates = [
        name
        for name in dir(unreal.MaterialUsage)
        if "INSTANCED" in name.upper()
        and "STATIC" in name.upper()
        and "MESH" in name.upper()
        and "SKINNED" not in name.upper()
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"Could not resolve InstancedStaticMeshes material usage enum: {candidates}")
    return getattr(unreal.MaterialUsage, candidates[0])


def load_preflight() -> tuple[list[dict], dict[str, unreal.Material]]:
    if not SOURCE_LOG.is_file():
        raise RuntimeError(f"Source runtime log is missing: {SOURCE_LOG}")

    warning_assets = WARNING_PATTERN.findall(SOURCE_LOG.read_text(encoding="utf-8", errors="replace"))
    warning_set = set(warning_assets)
    target_set = set(TARGETS)
    if len(TARGETS) != 17 or len(target_set) != len(TARGETS):
        raise RuntimeError("Repair allowlist must contain exactly 17 unique assets")
    if warning_set != target_set:
        raise RuntimeError(
            "Source-log InstancedStaticMeshes warnings no longer match the repair allowlist: "
            f"missing_from_allowlist={sorted(warning_set - target_set)} "
            f"missing_from_log={sorted(target_set - warning_set)}"
        )

    rows: list[dict] = []
    bases: dict[str, unreal.Material] = {}
    for target in TARGETS:
        interface = unreal.EditorAssetLibrary.load_asset(target)
        if not isinstance(interface, unreal.MaterialInterface):
            raise RuntimeError(f"Target is not a MaterialInterface: {target} ({interface})")

        base = interface if isinstance(interface, unreal.Material) else interface.get_base_material()
        if not isinstance(base, unreal.Material):
            raise RuntimeError(f"Could not resolve UMaterial base for: {target}")
        base_path = base.get_path_name().split(".", 1)[0]
        if not base_path.startswith("/Game/LineBoss/"):
            raise RuntimeError(
                f"Refusing shared/external base-material mutation: target={target} base={base_path}"
            )

        bases[base_path] = base
        rows.append(
            {
                "asset": target,
                "asset_class": interface.get_class().get_name(),
                "base_material": base_path,
                "asset_sha256_before": sha256(package_file(target)),
                "base_sha256_before": sha256(package_file(base_path)),
                "interface_object": interface,
            }
        )
    return rows, bases


def main() -> None:
    usage = usage_flag()
    rows, bases = load_preflight()

    base_results: dict[str, dict] = {}
    for base_path, base in bases.items():
        before = bool(base.get_editor_property(USAGE_PROPERTY))
        # UE 5.8's current API returns None; the persisted property is the
        # authority.  (set_material_usage is retained only as a deprecated
        # compatibility wrapper and its optional bool is not a change result.)
        unreal.MaterialEditingLibrary.set_base_material_usage(base, usage, True)
        after_set = bool(base.get_editor_property(USAGE_PROPERTY))
        if not after_set:
            raise RuntimeError(f"Usage flag did not set on {base_path}")

        unreal.MaterialEditingLibrary.recompile_material(base)
        saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(base, only_if_is_dirty=False))
        if not saved:
            raise RuntimeError(f"Failed to save base material: {base_path}")
        after_save = bool(base.get_editor_property(USAGE_PROPERTY))
        if not after_save:
            raise RuntimeError(f"Usage flag did not persist after save on {base_path}")

        base_results[base_path] = {
            "before": before,
            "changed": (not before) and after_save,
            "after": after_save,
            "saved": saved,
            "sha256_after": sha256(package_file(base_path)),
        }

    for row in rows:
        interface = row.pop("interface_object")
        interface_saved = bool(
            unreal.EditorAssetLibrary.save_loaded_asset(interface, only_if_is_dirty=False)
        )
        if not interface_saved:
            raise RuntimeError(f"Failed to resave material interface: {row['asset']}")
        row["interface_resaved"] = interface_saved
        row["asset_sha256_after"] = sha256(package_file(row["asset"]))
        row["usage_after"] = bool(
            bases[row["base_material"]].get_editor_property(USAGE_PROPERTY)
        )

    all_valid = (
        len(rows) == 17
        and all(row["interface_resaved"] and row["usage_after"] for row in rows)
        and all(result["saved"] and result["after"] for result in base_results.values())
    )
    receipt = {
        "schema": "lineboss.runtime_material_usage_repair.v1",
        "result": "PASS" if all_valid else "FAIL",
        "source_runtime_log": str(SOURCE_LOG),
        "source_warning": "missing usage flag InstancedStaticMeshes",
        "usage_enum": str(usage),
        "target_count": len(rows),
        "unique_base_material_count": len(base_results),
        "safety": {
            "allowlisted_only": True,
            "project_owned_bases_only": True,
            "surface_parameters_changed": False,
            "visual_effect": "none; adds the ISM/HISM shader permutation only",
        },
        "base_materials": base_results,
        "material_interfaces": rows,
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")

    if not all_valid:
        raise RuntimeError(f"InstancedStaticMeshes repair validation failed: {RECEIPT}")
    unreal.log(
        "LINE_BOSS_INSTANCED_STATIC_MESH_USAGE_REPAIR_V001_PASS "
        f"targets={len(rows)} unique_bases={len(base_results)} receipt={RECEIPT}"
    )


main()
