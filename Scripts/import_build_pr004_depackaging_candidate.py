"""Gate, import and assemble the isolated PR-004 depackaging candidate.

This script is deliberately fail-closed.  Running it with normal CPython only
performs source preflight and writes a dry-run audit.  Running it from Unreal
Editor also remains a dry run unless the environment contains the exact token

    LB_PR004_IMPORT_EXECUTE=I_UNDERSTAND_CANDIDATE_ONLY

The importer allow-list contains only the audited powered cradle v001 and robot
v002.  PackagingRig v001 is forbidden, and PackagingRig_v002 is also excluded
because its independent review passed FBX integrity but failed the release
visual gate.  It writes only below the candidate content root and a dedicated
validation map; there is no promotion path in this script.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CANONICAL_REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
PROJECT_FILE = CANONICAL_REPO / "LineBossCarFactory.uproject"
CELL_CONTRACT = CANONICAL_REPO / "Content/LineBoss/Data/pr004_robotic_depack_cell_v001.json"

DESTINATION_ROOT = "/Game/LineBoss/Stations/Press/PR004/Candidate_v001"
MATERIAL_ROOT = DESTINATION_ROOT + "/Materials"
VALIDATION_MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v001"

PREFLIGHT_AUDIT = CANONICAL_REPO / "Saved/Audits/pr004_unreal_import_preflight_v001.json"
IMPORT_AUDIT = CANONICAL_REPO / "Saved/Audits/pr004_unreal_import_candidate_v001.json"

EXECUTE_ENV = "LB_PR004_IMPORT_EXECUTE"
EXECUTE_TOKEN = "I_UNDERSTAND_CANDIDATE_ONLY"
EXPECTED_ENGINE_MAJOR_MINOR = "5.8"

# The locked envelope is always centred on the validation-map origin.  The
# possible -221 cm facility-fit child offset remains deliberately unapplied.
CELL_ORIGIN_CM = (0.0, 0.0, 0.0)
CANDIDATE_CHILD_OFFSET_CM = (0.0, 0.0, 0.0)
LOCKED_ENVELOPE_CM = {"flow_x": 1240.0, "across_y": 1440.0, "height_z": 450.0}

FAMILY_SPECS = (
    {
        "id": "powered_cradle_v001",
        "manifest": CANONICAL_REPO / "SourceAssets/PR004/PoweredRestrainedCradle/pr004_powered_cradle_candidate_v001_manifest.json",
        "audit": CANONICAL_REPO / "Saved/Audits/pr004_powered_cradle_candidate_v001_fbx_validation.json",
        "version": "v001",
        "expected_modules": 5,
        "destination": DESTINATION_ROOT + "/PoweredCradle_v001",
    },
    {
        "id": "robot_v002",
        "manifest": CANONICAL_REPO / "SourceAssets/PR004/RoboticDepackRobot/pr004_robotic_depack_robot_candidate_v002_manifest.json",
        "audit": CANONICAL_REPO / "Saved/Audits/pr004_robot_candidate_v002_fbx_validation.json",
        "version": "v002",
        "expected_modules": 28,
        "destination": DESTINATION_ROOT + "/Robot_v002",
    },
)

EXCLUDED_PACKAGING_V002 = {
    "id": "packaging_v002",
    "manifest": CANONICAL_REPO / "SourceAssets/PR004/PackagingRig_v002/pr004_packaging_rig_candidate_v002_manifest.json",
    "audit": CANONICAL_REPO / "Saved/Audits/pr004_packaging_rig_candidate_v002_independent_fbx_visual_audit.json",
    "version": "v002",
    "expected_modules": 43,
    "exclusion_reason": "SOURCE_FBX_PASS_BUT_RELEASE_VISUAL_GATE_FAIL__AWAIT_REPLACEMENT_VERSION",
}

FORBIDDEN_SOURCE_FRAGMENTS = (
    "SourceAssets\\PR004\\PackagingRig\\",
    "SourceAssets/PR004/PackagingRig/",
    "packaging_rig_candidate_v001",
)


@dataclass(frozen=True)
class SourceModule:
    family: str
    version: str
    module_id: str
    asset_name: str
    fbx: Path
    destination: str
    location_cm: tuple[float, float, float]
    rotation_deg: tuple[float, float, float]
    category: str
    is_mover: bool
    runtime_parent: str | None
    manifest_record: dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def path_is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def flatten_boolean_checks(value: Any) -> list[bool]:
    found: list[bool] = []
    if isinstance(value, bool):
        found.append(value)
    elif isinstance(value, dict):
        for child in value.values():
            found.extend(flatten_boolean_checks(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(flatten_boolean_checks(child))
    return found


def source_audit_passes(audit: dict[str, Any], *, independent_required: bool) -> tuple[bool, list[str]]:
    """Return a conservative technical-pass decision and human-readable reasons."""
    reasons: list[str] = []
    status = str(audit.get("status", "")).upper()
    booleans = flatten_boolean_checks(audit.get("checks", {}))
    explicit_pass_values = [
        audit.get("all_source_checks_pass"),
        audit.get("all_checks_pass"),
        audit.get("technical_pass"),
        audit.get("fbx_gate_pass"),
    ]
    explicit_pass = any(value is True for value in explicit_pass_values)
    derived_checks_pass = bool(booleans) and all(booleans)

    if "NOT_PROMOTED" not in status and str(audit.get("promotion", "")).upper().find("FORBIDDEN") < 0:
        reasons.append("audit does not preserve candidate/not-promoted status")
    if not (explicit_pass or derived_checks_pass or "GATE_PASS" in status):
        reasons.append("audit does not report a technical FBX pass")
    if booleans and not all(booleans):
        reasons.append("one or more audit checks are false")
    if independent_required:
        method_text = " ".join(
            str(audit.get(key, ""))
            for key in ("method", "validation_method", "review_type", "audit_type", "scope")
        ).upper()
        schema_text = str(audit.get("$schema", "")).upper()
        # An independently generated FBX audit may identify itself via schema,
        # method, review_type, or an explicit boolean.  A source manifest alone
        # can never satisfy this gate.
        independent = bool(audit.get("independent_review") is True) or "INDEPENDENT" in method_text
        fbx_evidence = "FBX" in method_text or "FBX" in schema_text or "FBX" in status
        if not independent:
            reasons.append("independent_review evidence is missing")
        if not fbx_evidence:
            reasons.append("FBX re-import/validation evidence is missing")
    return not reasons, reasons


def discover_engine_installations() -> list[dict[str, Any]]:
    """Discover Unreal installs without assuming a fixed launcher location."""
    candidates: dict[str, dict[str, Any]] = {}

    launcher_manifest = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "Epic/UnrealEngineLauncher/LauncherInstalled.dat"
    if launcher_manifest.exists():
        try:
            data = read_json(launcher_manifest)
            for item in data.get("InstallationList", []):
                location = Path(str(item.get("InstallLocation", "")))
                app_name = str(item.get("AppName", ""))
                if location.exists() and app_name.upper().startswith("UE_"):
                    candidates[str(location.resolve()).lower()] = {
                        "location": str(location.resolve()),
                        "source": str(launcher_manifest),
                        "launcher_app": app_name,
                    }
        except (OSError, ValueError, json.JSONDecodeError):
            pass

    program_files = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
    for epic_root in (program_files / "Epic Games", program_files / "EpicGames"):
        if epic_root.exists():
            for location in epic_root.glob("UE_*"):
                if location.is_dir():
                    candidates.setdefault(str(location.resolve()).lower(), {
                        "location": str(location.resolve()), "source": "filesystem_scan"
                    })

    records: list[dict[str, Any]] = []
    for record in candidates.values():
        location = Path(record["location"])
        build_file = location / "Engine/Build/Build.version"
        editor = location / "Engine/Binaries/Win64/UnrealEditor.exe"
        version = None
        if build_file.exists():
            try:
                build = read_json(build_file)
                version = f"{build.get('MajorVersion')}.{build.get('MinorVersion')}.{build.get('PatchVersion')}"
            except (OSError, ValueError, json.JSONDecodeError):
                version = None
        records.append({
            **record,
            "version": version,
            "editor": str(editor),
            "editor_exists": editor.exists(),
        })
    return sorted(records, key=lambda value: value["location"].lower())


def normalise_manifest_modules(spec: dict[str, Any], manifest: dict[str, Any]) -> list[SourceModule]:
    result: list[SourceModule] = []
    for index, record in enumerate(manifest.get("modules", []), start=1):
        family = str(spec["id"])
        if family.startswith("packaging_"):
            asset_name = str(record.get("name", ""))
            module_id = str(record.get("asset_id") or asset_name or index)
            location_m = record.get("rest_location_m", [0.0, 0.0, 0.0])
            location_cm = tuple(float(value) * 100.0 for value in location_m)
            rotation = tuple(float(value) for value in record.get("rest_rotation_deg", [0.0, 0.0, 0.0]))
            category = str(record.get("category", "packaging"))
            custom = record.get("custom_properties", {})
            runtime_parent = "packaged_coil"
            is_mover = category in {"wrap_runtime", "wrap_waste_state", "band_runtime", "band_waste_state"}
        else:
            asset_name = str(record.get("object", ""))
            module_id = str(record.get("id") or asset_name or index)
            location_raw = record.get("assembly_location_cm", record.get("rest_location_cm", [0.0, 0.0, 0.0]))
            location_cm = tuple(float(value) for value in location_raw)
            rotation = tuple(float(value) for value in record.get("assembly_rotation_deg", [0.0, 0.0, 0.0]))
            custom = record.get("custom_properties", {})
            category = (
                "robot" if family == "robot_v002"
                else "film_dewrap" if family.startswith("film_dewrap")
                else "process_context" if family.startswith("process_context")
                else "cradle"
            )
            runtime_parent = custom.get("runtime_parent")
            is_mover = bool(
                custom.get("moving_part")
                or custom.get("moving_part_id")
                or custom.get("motion_type")
                or custom.get("motion_contract")
            ) and module_id not in {
                "base", "static", "tool_rack", "band_tool", "wrap_tool", "edge_tool", "inspection_tool"
            }

        fbx = Path(str(record.get("fbx", "")))
        result.append(SourceModule(
            family=family,
            version=str(spec["version"]),
            module_id=module_id,
            asset_name=asset_name,
            fbx=fbx,
            destination=str(spec["destination"]),
            location_cm=location_cm,
            rotation_deg=rotation,
            category=category,
            is_mover=is_mover,
            runtime_parent=str(runtime_parent) if runtime_parent else None,
            manifest_record=record,
        ))
    return result


def run_preflight() -> tuple[dict[str, Any], list[SourceModule]]:
    gates: dict[str, bool] = {}
    blockers: list[str] = []
    warnings: list[str] = []
    families: list[dict[str, Any]] = []
    modules: list[SourceModule] = []

    gates["canonical_repo_exists"] = CANONICAL_REPO.is_dir()
    gates["canonical_repo_not_onedrive"] = "ONEDRIVE" not in str(CANONICAL_REPO.resolve()).upper()
    gates["project_file_exists"] = PROJECT_FILE.is_file()
    gates["cell_contract_exists"] = CELL_CONTRACT.is_file()
    for name, passed in tuple(gates.items()):
        if not passed:
            blockers.append(name)

    project = read_json(PROJECT_FILE) if PROJECT_FILE.exists() else {}
    enabled_plugins = {
        str(plugin.get("Name")) for plugin in project.get("Plugins", []) if plugin.get("Enabled") is True
    }
    gates["python_plugin_enabled"] = "PythonScriptPlugin" in enabled_plugins
    gates["editor_scripting_enabled"] = "EditorScriptingUtilities" in enabled_plugins
    gates["interchange_enabled"] = "Interchange" in enabled_plugins
    if not all(gates[key] for key in ("python_plugin_enabled", "editor_scripting_enabled", "interchange_enabled")):
        blockers.append("required Unreal editor plugins are not enabled")

    cell = read_json(CELL_CONTRACT) if CELL_CONTRACT.exists() else {}
    locked = cell.get("fixed_dimensions_cm", {})
    gates["locked_envelope_matches_contract"] = (
        float(locked.get("overall_flow_length", -1)) == LOCKED_ENVELOPE_CM["flow_x"]
        and float(locked.get("overall_across_width", -1)) == LOCKED_ENVELOPE_CM["across_y"]
        and float(locked.get("maximum_cell_equipment_height", -1)) == LOCKED_ENVELOPE_CM["height_z"]
    )
    gates["candidate_fit_offset_not_applied"] = CANDIDATE_CHILD_OFFSET_CM == (0.0, 0.0, 0.0)
    if not gates["locked_envelope_matches_contract"]:
        blockers.append("locked 14.4 m x 12.4 m x 4.5 m envelope differs from the authoritative contract")
    if not gates["candidate_fit_offset_not_applied"]:
        blockers.append("the provisional -221 cm fit offset must not be applied by this importer")

    for spec in FAMILY_SPECS:
        entry: dict[str, Any] = {
            "id": spec["id"],
            "version": spec["version"],
            "manifest": str(spec["manifest"]),
            "audit": str(spec["audit"]),
            "destination": spec["destination"],
        }
        manifest_exists = Path(spec["manifest"]).is_file()
        audit_exists = Path(spec["audit"]).is_file()
        entry["manifest_exists"] = manifest_exists
        entry["audit_exists"] = audit_exists
        if not manifest_exists:
            blockers.append(f"{spec['id']}: manifest missing")
            families.append(entry)
            continue
        manifest = read_json(Path(spec["manifest"]))
        family_modules = normalise_manifest_modules(spec, manifest)
        entry["manifest_status"] = manifest.get("status")
        entry["manifest_version"] = manifest.get("version")
        entry["module_count"] = len(family_modules)
        entry["expected_module_count"] = spec["expected_modules"]
        entry["manifest_version_matches"] = manifest.get("version") == spec["version"]
        entry["module_count_matches"] = len(family_modules) == spec["expected_modules"]
        entry["all_fbx_exist"] = all(module.fbx.is_file() for module in family_modules)
        entry["all_fbx_canonical"] = all(path_is_under(module.fbx, CANONICAL_REPO) for module in family_modules)
        entry["all_fbx_off_onedrive"] = all("ONEDRIVE" not in str(module.fbx.resolve()).upper() for module in family_modules)
        entry["asset_names_nonempty"] = all(bool(module.asset_name) for module in family_modules)
        entry["destination_is_candidate_only"] = str(spec["destination"]).startswith(DESTINATION_ROOT + "/")
        source_text = "\n".join(str(module.fbx) for module in family_modules)
        entry["forbidden_v001_packaging_absent"] = not any(fragment.lower() in source_text.lower() for fragment in FORBIDDEN_SOURCE_FRAGMENTS)
        if not str(spec["id"]).startswith("packaging_"):
            # Packaging-v001 fragment checks are relevant globally, but only
            # PackagingRig_v002 itself is required to have v002 filenames.
            entry["forbidden_v001_packaging_absent"] = True
        version_overrides = spec.get("module_version_overrides", {})
        entry["module_version_overrides"] = version_overrides
        entry["required_version_suffixes_present"] = all(
            module.asset_name.endswith(version_overrides.get(module.module_id, spec["version"]))
            and module.fbx.stem.endswith(version_overrides.get(module.module_id, spec["version"]))
            for module in family_modules
        )

        if audit_exists:
            audit = read_json(Path(spec["audit"]))
            passed, reasons = source_audit_passes(
                audit, independent_required=bool(spec.get("requires_independent_fbx_pass"))
            )
            entry["audit_status"] = audit.get("status")
            entry["audit_technical_pass"] = passed
            entry["audit_blockers"] = reasons
        else:
            entry["audit_status"] = "MISSING"
            entry["audit_technical_pass"] = False
            entry["audit_blockers"] = [
                f"independent {spec['id']} FBX technical-pass audit has not been published"
                if spec.get("requires_independent_fbx_pass") else "source FBX audit missing"
            ]

        family_required = (
            entry["manifest_version_matches"]
            and entry["module_count_matches"]
            and entry["all_fbx_exist"]
            and entry["all_fbx_canonical"]
            and entry["all_fbx_off_onedrive"]
            and entry["asset_names_nonempty"]
            and entry["destination_is_candidate_only"]
            and entry["forbidden_v001_packaging_absent"]
            and entry["required_version_suffixes_present"]
            and entry["audit_technical_pass"]
        )
        entry["family_gate_pass"] = family_required
        if family_required:
            modules.extend(family_modules)
        else:
            blockers.append(f"{spec['id']}: source family gate not satisfied")
        families.append(entry)

    engines = discover_engine_installations()
    matching_engines = [
        record for record in engines
        if str(record.get("version") or "").startswith(EXPECTED_ENGINE_MAJOR_MINOR + ".") and record.get("editor_exists")
    ]
    gates["unreal_5_8_install_discovered"] = bool(matching_engines)
    if not matching_engines:
        warnings.append("Unreal 5.8 editor installation was not discoverable; preflight can run but editor import cannot.")

    all_family_gates = len(families) == len(FAMILY_SPECS) and all(entry.get("family_gate_pass") is True for entry in families)
    gates["all_source_family_gates_pass"] = all_family_gates
    source_ready = all(gates.values()) and all_family_gates
    execute_token_present = os.environ.get(EXECUTE_ENV) == EXECUTE_TOKEN
    unreal_available = False
    unreal_engine_version = None
    try:
        import unreal  # type: ignore

        unreal_available = True
        unreal_engine_version = str(unreal.SystemLibrary.get_engine_version())
    except (ImportError, AttributeError):
        pass

    audit_result = {
        "$schema": "line-boss/audit/pr004-unreal-import-preflight/v1",
        "generated_utc": utc_now(),
        "status": "READY_FOR_EXPLICIT_CANDIDATE_IMPORT" if source_ready else "BLOCKED_NO_IMPORT_PERFORMED",
        "mode": "UNREAL_EDITOR" if unreal_available else "EXTERNAL_DRY_RUN",
        "canonical_repo": str(CANONICAL_REPO),
        "project": str(PROJECT_FILE),
        "destination_root": DESTINATION_ROOT,
        "validation_map": VALIDATION_MAP,
        "promotion_supported": False,
        "packaging_v001_forbidden": True,
        "locked_envelope_cm": LOCKED_ENVELOPE_CM,
        "cell_origin_cm": CELL_ORIGIN_CM,
        "candidate_child_offset_cm": CANDIDATE_CHILD_OFFSET_CM,
        "provisional_minus_221_cm_offset_applied": False,
        "gates": gates,
        "families": families,
        "source_module_count_if_ready": len(modules),
        "engine_discovery": engines,
        "matching_unreal_5_8_installations": matching_engines,
        "unreal_python_available": unreal_available,
        "unreal_engine_version": unreal_engine_version,
        "execute_token_present": execute_token_present,
        "blockers": blockers,
        "warnings": warnings,
        "next_gate": (
            "Publish an independent packaging FBX technical-pass audit, then rerun preflight."
            if any(str(entry["id"]).startswith("packaging_") and not entry.get("audit_technical_pass") for entry in families)
            else "Open the canonical project in Unreal 5.8 and explicitly supply the candidate-only execution token."
        ),
        "scope_limit": "No Unreal asset import, level edit, runtime edit or promotion is performed by preflight.",
    }
    PREFLIGHT_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    PREFLIGHT_AUDIT.write_text(json.dumps(audit_result, indent=2), encoding="utf-8")
    return audit_result, modules


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true", help="Run the default read-only source preflight.")
    parser.add_argument("--execute", action="store_true", help="Request import; the environment token and Unreal Editor are still required.")
    # Unreal Editor adds its own command-line switches.  Unknown switches must
    # not turn into an accidental execute request.
    args, _unknown = parser.parse_known_args()
    return args


# ---------------------------------------------------------------------------
# Unreal-only implementation
# ---------------------------------------------------------------------------


MATERIAL_SPECS = {
    # name: (base colour, metallic, roughness, two-sided)
    "MachineDark": ((0.025, 0.032, 0.040, 1.0), 0.72, 0.62, False),
    "SafetyYellow": ((0.82, 0.42, 0.025, 1.0), 0.18, 0.48, False),
    "MaintenanceOrange": ((0.76, 0.20, 0.018, 1.0), 0.12, 0.50, False),
    "MachinedSteel": ((0.42, 0.46, 0.49, 1.0), 0.92, 0.24, False),
    "CastIron": ((0.055, 0.063, 0.070, 1.0), 0.72, 0.78, False),
    "Rubber": ((0.008, 0.010, 0.012, 1.0), 0.00, 0.84, False),
    "HoseCable": ((0.012, 0.016, 0.020, 1.0), 0.02, 0.72, False),
    "SensorBlue": ((0.010, 0.16, 0.34, 1.0), 0.18, 0.26, False),
    "OpaqueSensorLens": ((0.018, 0.10, 0.16, 1.0), 0.26, 0.16, False),
    "WarningRed": ((0.55, 0.008, 0.004, 1.0), 0.08, 0.34, False),
    "ReadyGreen": ((0.010, 0.34, 0.070, 1.0), 0.06, 0.30, False),
    "ServiceLabel": ((0.62, 0.64, 0.61, 1.0), 0.10, 0.58, False),
    "GreaseResidue": ((0.045, 0.032, 0.014, 1.0), 0.02, 0.32, False),
    "CoilSteel": ((0.29, 0.32, 0.34, 1.0), 0.94, 0.31, False),
    "CoilPackaging": ((0.16, 0.18, 0.19, 1.0), 0.04, 0.66, True),
    "BandSteel": ((0.22, 0.24, 0.25, 1.0), 0.91, 0.29, True),
    "DullGreyWrap": ((0.34, 0.36, 0.37, 1.0), 0.02, 0.78, True),
    "RemovedFilm": ((0.032, 0.040, 0.045, 1.0), 0.00, 0.76, True),
    "CompactedFilm": ((0.018, 0.024, 0.028, 1.0), 0.00, 0.88, True),
    "EdgeProtector": ((0.22, 0.14, 0.070, 1.0), 0.00, 0.86, True),
    "IdentityLabel": ((0.62, 0.60, 0.52, 1.0), 0.00, 0.68, True),
    "ValidationConcrete": ((0.105, 0.105, 0.095, 1.0), 0.02, 0.88, False),
}


def choose_material_key(module: SourceModule, slot_name: str) -> str:
    low = (slot_name + " " + module.asset_name + " " + module.category).lower()
    if module.family.startswith("process_context"):
        if module.module_id == "packaged_master_coil":
            context_coil_rules = (
                (("protectivewrap", "wrapoverlap", "wraprepair"), "CoilPackaging"),
                (("blacksteelband",), "BandSteel"),
                (("compressededgeprotector",), "EdgeProtector"),
                (("idlabel", "labelink"), "IdentityLabel"),
                (("woundsteel", "boreedge", "bandbuckle"), "CoilSteel"),
            )
            for needles, key in context_coil_rules:
                if any(needle in low for needle in needles):
                    return key
            return "CoilSteel"
        if module.module_id == "compacted_band_bundle":
            return "BandSteel"
        if module.module_id == "compacted_plastic_bale":
            return "CompactedFilm"
        return "RemovedFilm"
    if module.family.startswith("packaging_"):
        if module.category in {"wrap", "wrap_runtime", "wrap_waste_state"}:
            return "DullGreyWrap"
        if module.category in {"bands", "band_runtime", "band_waste_state"}:
            return "BandSteel"
        if module.category == "protectors":
            return "EdgeProtector"
        if module.category == "identity":
            return "IdentityLabel"
        return "CoilSteel"
    if module.family.startswith("film_dewrap"):
        film_rules = (
            (("vcifilm", "filmweb", "woundfilm"), "RemovedFilm"),
            (("plasticbale", "compactedfilm"), "CompactedFilm"),
            (("safetyyellow", "yellowworn"), "SafetyYellow"),
            (("plasticbinblue", "hydraulicbluegrey", "sensorblue"), "SensorBlue"),
            (("rubber",), "Rubber"),
            (("hose", "cable"), "HoseCable"),
            (("chrome", "brushedsteel"), "MachinedSteel"),
            (("warningred", "_red_"), "WarningRed"),
            (("readygreen", "_green_"), "ReadyGreen"),
            (("label",), "ServiceLabel"),
            (("openmesh", "darktoolsteel", "machinecharcoal", "weldedframe", "weldseam"), "MachineDark"),
        )
        for needles, key in film_rules:
            if any(needle in low for needle in needles):
                return key
    rules = (
        (("yellow", "ochre"), "SafetyYellow"),
        (("orange",), "MaintenanceOrange"),
        (("warningred", "_red_"), "WarningRed"),
        (("readygreen", "_green_"), "ReadyGreen"),
        (("rubber", "vacuumcup"), "Rubber"),
        (("hose", "cable", "dress"), "HoseCable"),
        (("sensorblue", "hydraulicidblue"), "SensorBlue"),
        (("sensorglass", "lens"), "OpaqueSensorLens"),
        (("grease",), "GreaseResidue"),
        (("label", "rating", "ink", "plate"), "ServiceLabel"),
        (("castiron", "joint", "framecharcoal"), "CastIron"),
        (("machined", "chrome", "fastener", "steel", "hydraulicbody", "loadshoe", "reducer"), "MachinedSteel"),
    )
    for needles, key in rules:
        if any(needle in low for needle in needles):
            return key
    return "MachineDark"


def ue_import_and_build(preflight: dict[str, Any], modules: list[SourceModule]) -> None:
    import unreal  # type: ignore

    if preflight["status"] != "READY_FOR_EXPLICIT_CANDIDATE_IMPORT":
        raise RuntimeError(f"PR004 source gates are not ready: {preflight['blockers']}")
    if os.environ.get(EXECUTE_ENV) != EXECUTE_TOKEN:
        raise RuntimeError(
            f"Candidate import refused. Set {EXECUTE_ENV}={EXECUTE_TOKEN} only after reviewing {PREFLIGHT_AUDIT}."
        )
    engine_version = str(unreal.SystemLibrary.get_engine_version())
    if not engine_version.startswith(EXPECTED_ENGINE_MAJOR_MINOR + "."):
        raise RuntimeError(f"PR004 importer requires Unreal {EXPECTED_ENGINE_MAJOR_MINOR}; editor reports {engine_version}")
    if any(not module.destination.startswith(DESTINATION_ROOT + "/") for module in modules):
        raise RuntimeError("Importer destination escaped the candidate-only root")
    if any(fragment.lower() in str(module.fbx).lower() for module in modules for fragment in FORBIDDEN_SOURCE_FRAGMENTS):
        raise RuntimeError("PackagingRig v001 is forbidden")

    assets = unreal.EditorAssetLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()

    def create_master(two_sided: bool):
        suffix = "TwoSided" if two_sided else "Solid"
        path = f"{MATERIAL_ROOT}/M_LB_PR004_CandidateOpaque_{suffix}_Master"
        material = assets.load_asset(path) if assets.does_asset_exist(path) else None
        if not material:
            material = tools.create_asset(
                f"M_LB_PR004_CandidateOpaque_{suffix}_Master",
                MATERIAL_ROOT,
                unreal.Material,
                unreal.MaterialFactoryNew(),
            )
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
        material.set_editor_property("two_sided", two_sided)
        if hasattr(unreal.MaterialEditingLibrary, "delete_all_material_expressions"):
            unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
        base = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionVectorParameter, -420, -100
        )
        base.set_editor_properties({
            "parameter_name": unreal.Name("BaseColor"),
            "default_value": unreal.LinearColor(0.18, 0.18, 0.18, 1.0),
        })
        metal = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionScalarParameter, -420, 40
        )
        metal.set_editor_properties({"parameter_name": unreal.Name("Metallic"), "default_value": 0.0})
        rough = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionScalarParameter, -420, 160
        )
        rough.set_editor_properties({"parameter_name": unreal.Name("Roughness"), "default_value": 0.65})
        unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
        unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
        unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
        unreal.MaterialEditingLibrary.recompile_material(material)
        assets.save_loaded_asset(material, only_if_is_dirty=False)
        return material

    masters = {False: create_master(False), True: create_master(True)}
    material_instances: dict[str, Any] = {}
    for name, (colour, metallic, roughness, two_sided) in MATERIAL_SPECS.items():
        path = f"{MATERIAL_ROOT}/MI_LB_PR004_{name}"
        instance = assets.load_asset(path) if assets.does_asset_exist(path) else None
        if not instance:
            instance = tools.create_asset(
                f"MI_LB_PR004_{name}", MATERIAL_ROOT,
                unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew(),
            )
        instance.set_editor_property("parent", masters[two_sided])
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
            instance, "BaseColor", unreal.LinearColor(*colour)
        )
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "Metallic", metallic)
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "Roughness", roughness)
        unreal.MaterialEditingLibrary.update_material_instance(instance)
        assets.save_loaded_asset(instance, only_if_is_dirty=False)
        material_instances[name] = instance

    tasks = []
    for module in modules:
        task = unreal.AssetImportTask()
        task.set_editor_properties({
            "filename": str(module.fbx),
            "destination_path": module.destination,
            "destination_name": module.asset_name,
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
            "auto_generate_collision": False,
            "remove_degenerates": True,
        })
        task.set_editor_property("options", options)
        tasks.append(task)

    # UE 5.8.1 Interchange crashed inside StaticMeshDescription when the five
    # process-context FBXs were appended to the established 44-task batch.
    # Independent one-FBX probes passed for every source file.  Importing and
    # compiling one task at a time is therefore the fail-closed stable route.
    for task_index, task in enumerate(tasks, start=1):
        unreal.log(f"LINE_BOSS_PR004_IMPORT_TASK {task_index}/{len(tasks)} {task.get_editor_property('filename')}")
        tools.import_asset_tasks([task])
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

    import_records: list[dict[str, Any]] = []
    imported_by_key: dict[tuple[str, str], Any] = {}
    for module in modules:
        mesh_path = f"{module.destination}/{module.asset_name}"
        mesh = assets.load_asset(mesh_path)
        if not isinstance(mesh, unreal.StaticMesh):
            raise RuntimeError(f"Static mesh import failed: {mesh_path}")
        # UE 5.8 commandlet mode does not instantiate StaticMeshEditorSubsystem
        # on this workstation, while its deprecated compatibility library returns
        # -1 and silently creates no simple collision.  The isolated candidate
        # therefore uses render-mesh collision as a deterministic validation
        # fallback.  This is deliberately not a release collision claim: custom
        # UCX/primitive collision remains mandatory before promotion.
        body_setup = mesh.get_editor_property("body_setup")
        if body_setup is None:
            raise RuntimeError(f"Static mesh has no BodySetup for validation collision: {mesh_path}")
        body_setup.set_editor_property(
            "collision_trace_flag",
            unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE,
        )
        body_setup.modify()
        mesh.modify()
        assignments = []
        material_keys = set()
        for slot_index, slot in enumerate(mesh.get_editor_property("static_materials")):
            slot_name = str(
                slot.get_editor_property("imported_material_slot_name")
                or slot.get_editor_property("material_slot_name")
            )
            material_key = choose_material_key(module, slot_name)
            selected = material_instances[material_key]
            mesh.set_material(slot_index, selected)
            material_keys.add(material_key)
            assignments.append({"slot": slot_name, "material_key": material_key, "material": selected.get_path_name()})
        assets.save_loaded_asset(mesh, only_if_is_dirty=False)
        imported_by_key[(module.family, module.module_id)] = mesh
        import_records.append({
            "family": module.family,
            "module_id": module.module_id,
            "asset": mesh.get_path_name(),
            "source_fbx": str(module.fbx),
            "collision_policy": str(body_setup.get_editor_property("collision_trace_flag")),
            "collision_gate": "VALIDATION_COMPLEX_AS_SIMPLE__RELEASE_UCX_OR_PRIMITIVES_REQUIRED",
            "source_material_slot_count": len(assignments),
            "consolidated_material_instance_count": len(material_keys),
            "opaque_material_assignments": assignments,
        })
    assets.save_directory(DESTINATION_ROOT, only_if_is_dirty=False, recursive=True)

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    candidate_iteration = DESTINATION_ROOT.rsplit("/", 1)[-1]
    candidate_tag = unreal.Name(f"LB.PR004.ImportCandidate.{candidate_iteration}")
    if assets.does_asset_exist(VALIDATION_MAP):
        levels.load_level(VALIDATION_MAP)
        for existing in actor_system.get_all_level_actors():
            if candidate_tag in list(existing.get_editor_property("tags")):
                actor_system.destroy_actor(existing)
    elif not levels.new_level(VALIDATION_MAP):
        raise RuntimeError(f"Could not create dedicated validation map {VALIDATION_MAP}")

    def tags(*values: str):
        return [candidate_tag, unreal.Name("LB.Asset.Candidate.NotPromoted"), *(unreal.Name(value) for value in values)]

    def spawn_cube(label: str, location, size, material_key: str, *actor_tags: str):
        actor = actor_system.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
        actor.set_actor_label(label)
        actor.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
        actor.set_actor_scale3d(unreal.Vector(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
        actor.static_mesh_component.set_material(0, material_instances[material_key])
        actor.set_editor_property("tags", tags(*actor_tags))
        return actor

    # Locked footprint and height datums.  These are validation primitives,
    # not additional imported factory assets.
    spawn_cube("LB_PR004_LockedFloor_1240x1440", (0, 0, -5), (1240, 1440, 10), "ValidationConcrete", "LB.PR004.Envelope")
    boundary_thickness = 6.0
    boundary_height = 8.0
    spawn_cube("LB_PR004_Envelope_N", (0, 720, boundary_height / 2), (1240, boundary_thickness, boundary_height), "SafetyYellow", "LB.PR004.Envelope")
    spawn_cube("LB_PR004_Envelope_S", (0, -720, boundary_height / 2), (1240, boundary_thickness, boundary_height), "SafetyYellow", "LB.PR004.Envelope")
    spawn_cube("LB_PR004_Envelope_E", (620, 0, boundary_height / 2), (boundary_thickness, 1440, boundary_height), "SafetyYellow", "LB.PR004.Envelope")
    spawn_cube("LB_PR004_Envelope_W", (-620, 0, boundary_height / 2), (boundary_thickness, 1440, boundary_height), "SafetyYellow", "LB.PR004.Envelope")
    for x in (-620.0, 620.0):
        for y in (-720.0, 720.0):
            spawn_cube(f"LB_PR004_HeightDatum_{int(x)}_{int(y)}", (x, y, 225), (5, 5, 450), "SafetyYellow", "LB.PR004.HeightDatum")

    # Deterministic industrial validation lighting.  The former empty maps
    # could render either black or clipped white depending on editor exposure,
    # which made material comparison meaningless.
    key = actor_system.spawn_actor_from_class(
        unreal.RectLight, unreal.Vector(-260.0, 40.0, 620.0), unreal.Rotator()
    )
    key.set_actor_label("LB_PR004_ValidationKey")
    key.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(key.get_actor_location(), unreal.Vector(-80.0, 40.0, 120.0)), False
    )
    key.get_editor_property("rect_light_component").set_editor_properties({
        "intensity": 850.0,
        "attenuation_radius": 1700.0,
        "source_width": 520.0,
        "source_height": 260.0,
    })
    key.set_editor_property("tags", tags("LB.Light.Validation"))
    fill = actor_system.spawn_actor_from_class(
        unreal.RectLight, unreal.Vector(460.0, -350.0, 480.0), unreal.Rotator()
    )
    fill.set_actor_label("LB_PR004_ValidationFill")
    fill.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(fill.get_actor_location(), unreal.Vector(160.0, 80.0, 120.0)), False
    )
    fill.get_editor_property("rect_light_component").set_editor_properties({
        "intensity": 420.0,
        "attenuation_radius": 1500.0,
        "source_width": 380.0,
        "source_height": 220.0,
    })
    fill.set_editor_property("tags", tags("LB.Light.Validation"))
    ambient = actor_system.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 700.0), unreal.Rotator(-58.0, 135.0, 0.0)
    )
    ambient.set_actor_label("LB_PR004_ValidationAmbient")
    ambient.get_editor_property("directional_light_component").set_editor_properties({
        "intensity": 0.55,
        "light_color": unreal.Color(198, 214, 232, 255),
        "cast_shadows": False,
    })
    ambient.set_editor_property("tags", tags("LB.Light.Validation"))
    exposure = actor_system.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
    exposure.set_actor_label("LB_PR004_FixedExposure")
    exposure.set_editor_properties({"unbound": True, "blend_weight": 1.0, "tags": tags("LB.Light.Validation")})
    exposure_settings = exposure.get_editor_property("settings")
    exposure_settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": -1.35,
    })
    exposure.set_editor_property("settings", exposure_settings)

    # Source X/Y -> facility -Y/+X is a -90 degree yaw.  The assembly remains
    # at the locked origin; the proposed -221 cm facility-fit offset is absent.
    source_to_facility_yaw = -90.0
    family_roots = {
        "powered_cradle_v001": (-280.0, 120.0, 0.0),
        "robot_v002": (150.0, -40.0, 0.0),
        "packaging_v002": (-280.0, 120.0, 130.5),
        "film_dewrap_v004": (310.0, 290.0, 0.0),
        "process_context_v001": (0.0, 0.0, 0.0),
    }
    for module in modules:
        if module.family.startswith("packaging_"):
            family_roots.setdefault(module.family, (-280.0, 120.0, 130.5))

    actor_records = []
    actors_by_key: dict[tuple[str, str], Any] = {}
    for module in modules:
        root = family_roots[module.family]
        sx, sy, sz = module.location_cm
        # Rz(-90): source (x,y,z) -> facility (y,-x,z).
        location = unreal.Vector(root[0] + sy, root[1] - sx, root[2] + sz)
        roll, pitch, yaw = module.rotation_deg
        rotation = unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw + source_to_facility_yaw)
        actor = actor_system.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
        actor.set_actor_label(f"LB_PR004_{module.family}_{module.module_id}")
        actor.static_mesh_component.set_static_mesh(imported_by_key[(module.family, module.module_id)])
        actor.static_mesh_component.set_editor_property(
            "mobility", unreal.ComponentMobility.MOVABLE if module.is_mover else unreal.ComponentMobility.STATIC
        )
        initially_visible = not (
            module.family.startswith("packaging_")
            and (
                module.category in {
                    "wrap_runtime", "wrap_waste_state", "band_runtime", "band_waste_state"
                }
                or "capturedtail" in module.asset_name.lower()
            )
        )
        actor.static_mesh_component.set_editor_properties({
            "visible": initially_visible,
            "hidden_in_game": not initially_visible,
        })
        actor.set_editor_property("tags", tags(
            "LB.Station.PR004", f"LB.SourceFamily.{module.family}",
            "LB.Module.Mover" if module.is_mover else "LB.Module.Static",
        ))
        actors_by_key[(module.family, module.module_id)] = actor
        actor_records.append({
            "family": module.family,
            "module_id": module.module_id,
            "actor": actor.get_actor_label(),
            "location_cm": list(location.to_tuple()),
            "rotation_deg": [roll, pitch, yaw + source_to_facility_yaw],
            "mobility": "MOVABLE" if module.is_mover else "STATIC",
            "runtime_parent_contract": module.runtime_parent,
            "initially_visible": initially_visible,
        })

    # Curated pack content is validation dressing only.  Reuse the vendor lamp
    # and cable bundle where they are genuinely stronger; never substitute the
    # custom PR-004 hero mechanisms or their material UVs.
    vendor_dressing = (
        ("LB_PR004_VENDOR_Lamp_NW", "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Lamp01", (-420.0, 470.0, 430.0), (0.0, 0.0, 0.0), (1.4, 1.4, 1.4)),
        ("LB_PR004_VENDOR_Lamp_SE", "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Lamp01", (420.0, -420.0, 430.0), (0.0, 0.0, 180.0), (1.4, 1.4, 1.4)),
        ("LB_PR004_VENDOR_CableBundle", "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_CableSet_01", (385.0, 455.0, 20.0), (0.0, 0.0, 90.0), (1.1, 1.1, 1.1)),
    )
    vendor_records = []
    for label, path, location, rotation, scale in vendor_dressing:
        mesh = assets.load_asset(path)
        if not isinstance(mesh, unreal.StaticMesh):
            continue
        actor = actor_system.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(*rotation))
        actor.set_actor_label(label)
        actor.set_actor_scale3d(unreal.Vector(*scale))
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        actor.set_editor_property("tags", tags("LB.Vendor.FactoryEnvironment", "LB.Asset.ValidationOnly"))
        vendor_records.append({"actor": label, "asset": path})

    # Preserve meaningful articulated relationships using KEEP_WORLD.  The map
    # remains a visual/import candidate; runtime Blueprint/C++ binding is a
    # separate gate.
    parent_contract = {
        ("powered_cradle_v001", "left_side_clamp"): ("powered_cradle_v001", "static"),
        ("powered_cradle_v001", "right_side_clamp"): ("powered_cradle_v001", "static"),
        ("powered_cradle_v001", "index_drive"): ("powered_cradle_v001", "static"),
        ("powered_cradle_v001", "end_stop_locator"): ("powered_cradle_v001", "static"),
        ("robot_v002", "j1"): ("robot_v002", "base"),
        ("robot_v002", "j2"): ("robot_v002", "j1"),
        ("robot_v002", "j3"): ("robot_v002", "j2"),
        ("robot_v002", "j4"): ("robot_v002", "j3"),
        ("robot_v002", "j5"): ("robot_v002", "j4"),
        ("robot_v002", "j6"): ("robot_v002", "j5"),
        ("robot_v002", "changer_body"): ("robot_v002", "j6"),
        ("robot_v002", "changer_lock"): ("robot_v002", "changer_body"),
        ("robot_v002", "dress_lower"): ("robot_v002", "j1"),
        ("robot_v002", "dress_upper"): ("robot_v002", "j2"),
        ("robot_v002", "dress_wrist"): ("robot_v002", "j4"),
        ("robot_v002", "band_left_capture"): ("robot_v002", "band_tool"),
        ("robot_v002", "band_right_capture"): ("robot_v002", "band_tool"),
        ("robot_v002", "band_cutter"): ("robot_v002", "band_tool"),
        ("robot_v002", "band_roll_left"): ("robot_v002", "band_tool"),
        ("robot_v002", "band_roll_right"): ("robot_v002", "band_tool"),
        ("robot_v002", "wrap_vacuum_carrier"): ("robot_v002", "wrap_tool"),
        ("robot_v002", "wrap_peel_roll"): ("robot_v002", "wrap_tool"),
        ("robot_v002", "edge_left_jaw"): ("robot_v002", "edge_tool"),
        ("robot_v002", "edge_right_jaw"): ("robot_v002", "edge_tool"),
        ("robot_v002", "inspection_bore_camera"): ("robot_v002", "inspection_tool"),
        ("robot_v002", "inspection_shutter"): ("robot_v002", "inspection_tool"),
        ("film_dewrap_v004", "tab_clamp"): ("film_dewrap_v004", "static"),
        ("film_dewrap_v004", "spindle_expand"): ("film_dewrap_v004", "static"),
        ("film_dewrap_v004", "spindle_rotor"): ("film_dewrap_v004", "static"),
        ("film_dewrap_v004", "dancer_arm"): ("film_dewrap_v004", "static"),
        ("film_dewrap_v004", "dancer_roller"): ("film_dewrap_v004", "dancer_arm"),
        ("film_dewrap_v004", "stripper_plate"): ("film_dewrap_v004", "static"),
        ("film_dewrap_v004", "transfer_gate"): ("film_dewrap_v004", "static"),
        ("film_dewrap_v004", "compactor_ram"): ("film_dewrap_v004", "static"),
        ("film_dewrap_v004", "bale_discharge"): ("film_dewrap_v004", "static"),
    }
    packaging_root_key = next(
        (
            (module.family, module.module_id)
            for module in modules
            if module.family.startswith("packaging_") and module.category == "bare"
        ),
        None,
    )
    attachment_records = []
    for child_key, child_actor in actors_by_key.items():
        parent_key = parent_contract.get(child_key)
        if child_key[0].startswith("packaging_") and packaging_root_key and child_key != packaging_root_key:
            parent_key = packaging_root_key
        if not parent_key or parent_key not in actors_by_key:
            continue
        parent_actor = actors_by_key[parent_key]
        try:
            child_actor.attach_to_actor(
                parent_actor, unreal.Name(""),
                unreal.AttachmentRule.KEEP_WORLD,
                unreal.AttachmentRule.KEEP_WORLD,
                unreal.AttachmentRule.KEEP_WORLD,
                False,
            )
            attachment_records.append({"child": child_actor.get_actor_label(), "parent": parent_actor.get_actor_label(), "attached": True})
        except Exception as exc:  # Unreal API variations are audited, never hidden.
            attachment_records.append({"child": child_actor.get_actor_label(), "parent": parent_actor.get_actor_label(), "attached": False, "error": str(exc)})

    # Deterministic validation cameras; none are the normal gameplay camera.
    camera_specs = (
        ("LB_PR004_CAM_Overview_SW", (-1080, 1050, 760), (0, 0, 120), 48.0, None),
        ("LB_PR004_CAM_Overview_NE", (980, -1120, 690), (-40, 0, 125), 48.0, None),
        ("LB_PR004_CAM_Top", (0, 0, 1900), (0, 0, 0), 50.0, 2700.0),
        ("LB_PR004_CAM_CradleClose", (-690, 580, 330), (-280, 120, 130), 42.0, None),
        ("LB_PR004_CAM_RobotTools", (610, 450, 340), (120, -110, 125), 44.0, None),
        ("LB_PR004_CAM_PackagingClose", (-590, -270, 300), (-280, 120, 130), 40.0, None),
        ("LB_PR004_CAM_FilmDewrap", (865, 815, 410), (300, 260, 125), 43.0, None),
    )
    cameras = []
    for label, location_raw, target_raw, fov, ortho_width in camera_specs:
        location = unreal.Vector(*location_raw)
        camera = actor_system.spawn_actor_from_class(unreal.CameraActor, location, unreal.Rotator())
        camera.set_actor_label(label)
        component = camera.get_editor_property("camera_component")
        if ortho_width is not None:
            camera.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=-90.0, yaw=-90.0), False)
            component.set_editor_properties({
                "projection_mode": unreal.CameraProjectionMode.ORTHOGRAPHIC,
                "ortho_width": ortho_width,
                "aspect_ratio": 16.0 / 9.0,
                "constrain_aspect_ratio": True,
            })
        else:
            camera.set_actor_rotation(
                unreal.MathLibrary.find_look_at_rotation(location, unreal.Vector(*target_raw)), False
            )
            component.set_editor_properties({
                "field_of_view": fov,
                "aspect_ratio": 16.0 / 9.0,
                "constrain_aspect_ratio": True,
            })
        camera.set_editor_property("tags", tags("LB.Camera.Validation", "LB.Camera.Fixed.PR004"))
        cameras.append(label)

    if not levels.save_current_level():
        raise RuntimeError("Failed to save the isolated PR004 validation map")
    assets.save_directory(DESTINATION_ROOT, only_if_is_dirty=False, recursive=True)

    import_result = {
        "$schema": "line-boss/audit/pr004-unreal-import-candidate/v1",
        "generated_utc": utc_now(),
        "status": "UNREAL_IMPORT_CANDIDATE_NOT_PROMOTED",
        "engine_version": engine_version,
        "project": str(PROJECT_FILE),
        "destination_root": DESTINATION_ROOT,
        "validation_map": VALIDATION_MAP,
        "source_preflight": str(PREFLIGHT_AUDIT),
        "source_preflight_status": preflight["status"],
        "promotion_supported": False,
        "packaging_v001_imported": False,
        "locked_envelope_cm": LOCKED_ENVELOPE_CM,
        "cell_origin_cm": CELL_ORIGIN_CM,
        "candidate_child_offset_cm": CANDIDATE_CHILD_OFFSET_CM,
        "provisional_minus_221_cm_offset_applied": False,
        "imported_asset_count": len(import_records),
        "imported_assets": import_records,
        "assembled_actor_count": len(actor_records),
        "assembled_actors": actor_records,
        "attachments": attachment_records,
        "vendor_validation_dressing": vendor_records,
        "fixed_cameras": cameras,
        "material_policy": {
            "blend_mode": "OPAQUE_ONLY",
            "imported_materials": False,
            "imported_textures": False,
            "shared_master_count": len(masters),
            "shared_instance_count": len(material_instances),
            "slot_reordering_or_deletion": False,
            "safe_consolidation": "Original slots retained; equivalent slots reuse controlled shared material instances.",
        },
        "collision_policy": {
            "candidate_validation": "CTF_USE_COMPLEX_AS_SIMPLE",
            "reason": "StaticMeshEditorSubsystem is unavailable in UE 5.8 commandlet mode and the compatibility API returned -1 without generating primitives.",
            "release_gate_passed": False,
            "release_requirement": "Author and independently inspect modular UCX or hand-built primitive collision before promotion.",
        },
        "remaining_gates": [
            "Inspect fresh fixed-camera Unreal screenshots against the Pro references.",
            "Verify J1-J6 hierarchy, all tool pivots and cradle articulation in runtime.",
            "Build swept collision and robot/crane/waste-machine safety interlocks.",
            "Bind the persistent packaged-coil actor and visible band/plastic waste handshakes.",
            "Replace candidate-only flat material parameters with release PBR detail where visual review requires it.",
            "Do not promote any asset or map solely because this import succeeds.",
        ],
        "scope_limit": "Candidate import and isolated validation-map assembly only; no runtime integration or promotion performed.",
    }
    IMPORT_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    IMPORT_AUDIT.write_text(json.dumps(import_result, indent=2), encoding="utf-8")
    unreal.log(
        f"LINE_BOSS_PR004_CANDIDATE_IMPORT_PASS assets={len(import_records)} map={VALIDATION_MAP} audit={IMPORT_AUDIT}"
    )


def main() -> int:
    args = parse_args()
    preflight, modules = run_preflight()
    print(
        f"LINE_BOSS_PR004_IMPORT_PREFLIGHT status={preflight['status']} "
        f"mode={preflight['mode']} audit={PREFLIGHT_AUDIT}"
    )
    execute_requested = args.execute or os.environ.get(EXECUTE_ENV) == EXECUTE_TOKEN
    if not execute_requested:
        return 0 if preflight["status"] == "READY_FOR_EXPLICIT_CANDIDATE_IMPORT" else 2
    if preflight["status"] != "READY_FOR_EXPLICIT_CANDIDATE_IMPORT":
        print("PR004 import refused: source gates are incomplete.", file=sys.stderr)
        return 3
    try:
        import unreal  # type: ignore  # noqa: F401
    except ImportError:
        print("PR004 import refused: execute mode must run inside Unreal Editor Python.", file=sys.stderr)
        return 4
    ue_import_and_build(preflight, modules)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
