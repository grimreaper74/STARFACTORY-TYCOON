"""Run the exact v005 assembly gate against the direct v006 visual successor."""

from pathlib import Path


base = Path(__file__).with_name("audit_press_train_a_assembly_integration_static_v005.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyIntegrationCandidate_v005",
    "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyVisualCandidate_v006",
)
code = code.replace(
    "press_train_a_assembly_integration_static_v005.json",
    "press_train_a_assembly_visual_static_v006.json",
)
code = code.replace(
    "PASS__EXACT_IMPORT_STATIC_COLLISION_NAV_AUTHORING_PERFORMANCE_BRANDING_GATE__RUNTIME_NAV_ANIMATION_PRO_VISUAL_OPEN__NOT_PROMOTED",
    "PASS__V006_EXACT_INHERITED_IMPORT_STATIC_COLLISION_NAV_AUTHORING_PERFORMANCE_BRANDING_GATE__RUNTIME_NAV_ANIMATION_PRO_VISUAL_OPEN__NOT_PROMOTED",
)
exec(compile(code, str(base) + "::v006", "exec"), globals(), globals())

