"""Run the exact v005 assembly gate against the direct v008 visual successor.

The six new west fill lights are validation-rig actors, not inherited assembly
objects. Exclude only those lights from the inherited provenance scope while
leaving all machine, transform, material, collision and bounds checks exact.
"""

from pathlib import Path


base = Path(__file__).with_name("audit_press_train_a_assembly_integration_static_v005.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyIntegrationCandidate_v005",
    "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyVisualCandidate_v008",
)
code = code.replace(
    "press_train_a_assembly_integration_static_v005.json",
    "press_train_a_assembly_visual_static_v008.json",
)
code = code.replace(
    'scope = [actor for actor in actors if "LB.PressTrain.TrainA.AssemblyIntegration.v005" in tags(actor)]',
    'scope = [actor for actor in actors if "LB.PressTrain.TrainA.AssemblyIntegration.v005" in tags(actor) and not ("LB.Validation.Lighting.v008" in tags(actor) and "LB.Asset.Candidate.v005" not in tags(actor))]',
)
code = code.replace(
    "PASS__EXACT_IMPORT_STATIC_COLLISION_NAV_AUTHORING_PERFORMANCE_BRANDING_GATE__RUNTIME_NAV_ANIMATION_PRO_VISUAL_OPEN__NOT_PROMOTED",
    "PASS__V008_EXACT_INHERITED_IMPORT_STATIC_COLLISION_NAV_AUTHORING_PERFORMANCE_BRANDING_GATE__RUNTIME_NAV_ANIMATION_PRO_VISUAL_OPEN__NOT_PROMOTED",
)
exec(compile(code, str(base) + "::v008", "exec"), globals(), globals())
