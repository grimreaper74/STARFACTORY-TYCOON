"""Build fresh MR01 v022 with native authority and corrected straight-dock presentation.

This deliberately derives the proven v021 assembly procedure in memory, then changes
only its candidate namespace, retained v022 payload source and presentation-axis parent.
The native collision, route, docking sockets, pivots, save state and tools remain on the
unchanged C++ authority axes.
"""

from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = ROOT / "Scripts/build_lb_mr01_candidate_v021_reusable_authority.py"
code = BASE.read_text(encoding="utf-8")


def replace_once(old, new):
    global code
    count = code.count(old)
    if count != 1:
        raise RuntimeError("Expected one source fragment, found {}: {}".format(count, old[:120]))
    code = code.replace(old, new, 1)


replace_once(
    '"""Build reusable MR01 v021 on native authority with v020 connected-lift art."""',
    '"""Build reusable MR01 v022 with corrected straight-dock presentation axis."""',
)
replace_once(
    'SOURCE_ROOT = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v020"\n'
    'PAYLOAD_ROOT = SOURCE_ROOT + "/Payload"\n'
    'ARM_ROOT = SOURCE_ROOT + "/Arm"\n'
    'TOOLS_ROOT = SOURCE_ROOT + "/Tools"',
    'SOURCE_ROOT = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v022"\n'
    'PAYLOAD_ROOT = SOURCE_ROOT + "/Payload"\n'
    'ARM_ROOT = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v020/Arm"\n'
    'TOOLS_ROOT = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v020/Tools"',
)
replace_once(
    'CANDIDATE_ROOT = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v021"\n'
    'BP_PATH = CANDIDATE_ROOT + "/Blueprints/BP_LB_MR01_MaintenanceAMR_v021"\n'
    'AUDIT = ROOT / "Saved/Audits/lb_mr01_candidate_v021_reusable_authority_build.json"',
    'CANDIDATE_ROOT = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v022"\n'
    'BP_PATH = CANDIDATE_ROOT + "/Blueprints/BP_LB_MR01_MaintenanceAMR_v022"\n'
    'AUDIT = ROOT / "Saved/Audits/SupportRobots/lb_mr01_candidate_v022_straight_dock_authority_build.json"',
)
replace_once(
    'if assets.does_directory_exist(CANDIDATE_ROOT):\n'
    '    raise RuntimeError(f"Preserve existing candidate namespace {CANDIDATE_ROOT}")\n'
    'import_audit = json.loads((ROOT / "Saved/Audits/lb_mr01_candidate_v020_unreal_import.json").read_text(encoding="utf-8"))\n'
    'if import_audit.get("status") != "IMPORT_GATE_PASS__CANDIDATE_NOT_PROMOTED" or import_audit.get("asset_counts", {}).get("arm_bone_count") != 10:\n'
    '    raise RuntimeError("v020 strict Unreal import authority is not green")',
    'if assets.does_asset_exist(BP_PATH):\n'
    '    raise RuntimeError(f"Preserve existing candidate Blueprint {BP_PATH}")\n'
    'payload_audit = json.loads((ROOT / "Saved/Audits/SupportRobots/mr01_v022_static_payload_unreal_import.json").read_text(encoding="utf-8"))\n'
    'if payload_audit.get("static_mesh_count") != 345:\n'
    '    raise RuntimeError("v022 payload import count is not authoritative")\n'
    'arm_audit = json.loads((ROOT / "Saved/Audits/lb_mr01_candidate_v020_unreal_import.json").read_text(encoding="utf-8"))\n'
    'if arm_audit.get("status") != "IMPORT_GATE_PASS__CANDIDATE_NOT_PROMOTED" or arm_audit.get("asset_counts", {}).get("arm_bone_count") != 10:\n'
    '    raise RuntimeError("v020 ten-bone arm authority is not green")',
)
replace_once(
    'if missing:\n'
    '    raise RuntimeError(f"Native MR01 contract pivots missing: {missing}")\n\n'
    'payload_paths =',
    'if missing:\n'
    '    raise RuntimeError(f"Native MR01 contract pivots missing: {missing}")\n\n'
    '# Presentation artwork was authored with length on local Y.  Rotate only the\n'
    '# imported payload/arm parent onto native CFR +X.  Do not rotate native sockets,\n'
    '# collision, route projection, wheels, tool rack or runtime pivots.\n'
    'presentation_axis_handle, presentation_axis_component = add_component(\n'
    '    blueprint, handles["RobotVisualRoot"], unreal.SceneComponent, "MR01PresentationAxisRoot")\n'
    'configure_scene(presentation_axis_component, rotation=(0.0, 0.0, -90.0), tags=(\n'
    '    "LB.MR01.PresentationAxisCorrection.v022", "LB.Asset.CandidateNotPromoted"))\n\n'
    'payload_paths =',
)
replace_once('parent_handle = handles["RobotVisualRoot"]', 'parent_handle = presentation_axis_handle')
replace_once(
    'arm_handle, arm_component = add_component(blueprint, handles["RobotVisualRoot"], unreal.PoseableMeshComponent, "Visual_MR01_ArmPoseable")',
    'arm_handle, arm_component = add_component(blueprint, presentation_axis_handle, unreal.PoseableMeshComponent, "Visual_MR01_ArmPoseable")',
)

# Candidate identity and audit wording are presentation lineage, not engineering data.
code = code.replace('LB.Asset.Candidate.v020', 'LB.Asset.Candidate.v022')
code = code.replace('LB.Asset.Candidate.v021', 'LB.Asset.Candidate.v022')
code = code.replace('v020 payload meshes including connected sleeve', 'v022 payload meshes including corrected side bumpers')
code = code.replace('MR01 v021 generated class unavailable', 'MR01 v022 generated class unavailable')
code = code.replace(
    '"$schema": "line-boss/audit/lb-mr01-candidate-v021-reusable-authority-build",',
    '"$schema": "cairnwell/audit/lb-mr01-candidate-v022-straight-dock-authority-build/v1",',
)
code = code.replace(
    '"status": "REUSABLE_NATIVE_AUTHORITY_ASSEMBLY_BUILT__FRESH_RELOAD_RUNTIME_AND_CAMERA_GATES_REQUIRED__NOT_PROMOTED",',
    '"status": "V022_STRAIGHT_DOCK_NATIVE_AUTHORITY_ASSEMBLY_BUILT__FRESH_RELOAD_RUNTIME_AND_CAMERA_GATES_REQUIRED__NOT_PROMOTED",',
)
code = code.replace(
    '"source_candidate": SOURCE_ROOT,',
    '"source_candidate": SOURCE_ROOT,\n'
    '    "presentation_axis_root": "MR01PresentationAxisRoot",\n'
    '    "presentation_axis_relative_yaw_deg": -90.0,\n'
    '    "native_collision_and_dock_authority_rotated": False,',
)
code = code.replace('LB_MR01_V021_REUSABLE_BUILD_PASS', 'LB_MR01_V022_STRAIGHT_DOCK_BUILD_PASS')

exec(compile(code, str(BASE) + "::v022-straight-dock", "exec"), globals(), globals())
