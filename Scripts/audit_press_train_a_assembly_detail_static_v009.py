"""Run exact manifest/material/collision/performance/branding gates on Train A v009."""

from pathlib import Path


base = Path(__file__).with_name("audit_press_train_a_assembly_integration_static_v005.py")
code = base.read_text(encoding="utf-8")
replacements = {
    '/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyIntegrationCandidate_v005': '/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyDetailCandidate_v009',
    '/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v005': '/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyDetail_v009',
    'SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v001': 'SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v002',
    'PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_v001.json': 'PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_v002.json',
    'press_train_a_assembly_instance_staging_v005.json': 'press_train_a_assembly_detail_staging_v009.json',
    'press_train_a_assembly_integration_build_v005.json': 'press_train_a_assembly_detail_build_v009.json',
    'press_train_a_assembly_integration_static_v005.json': 'press_train_a_assembly_detail_static_v009.json',
    'LB.PressTrain.TrainA.AssemblyIntegration.v005': 'LB.PressTrain.TrainA.AssemblyDetail.v009',
    'LB.Asset.Candidate.v005': 'LB.Asset.Candidate.v009',
    '_UEv005': '_UEv009',
    'if len(presentation) != 163:': 'if len(presentation) != manifest["instance_count"]:',
    'expected 163 presentation actors': 'expected manifest presentation actors',
    'PASS__EXACT_IMPORT_STATIC_COLLISION_NAV_AUTHORING_PERFORMANCE_BRANDING_GATE__RUNTIME_NAV_ANIMATION_PRO_VISUAL_OPEN__NOT_PROMOTED': 'PASS__V009_EXACT_V002_IMPORT_STATIC_COLLISION_NAV_AUTHORING_PERFORMANCE_BRANDING_GATE__RUNTIME_NAV_ANIMATION_PRO_VISUAL_OPEN__NOT_PROMOTED',
    'FAIL__ASSEMBLY_INTEGRATION_STATIC_V005__NOT_PROMOTED': 'FAIL__ASSEMBLY_DETAIL_STATIC_V009__NOT_PROMOTED',
}
for old, new in replacements.items():
    code = code.replace(old, new)
exec(compile(code, str(base) + "::v009", "exec"), globals(), globals())

