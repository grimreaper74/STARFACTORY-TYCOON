"""Corrected 100x scale successor; preserves failed AssemblyStudyIntegration v001."""

from pathlib import Path


base = Path(__file__).with_name("import_build_press_train_a_assembly_study_integration_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace('DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v001"',
                    'DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v002"')
code = code.replace('MAP = "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyIntegrationCandidate_v001"',
                    'MAP = "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyIntegrationCandidate_v002"')
code = code.replace('press_train_a_assembly_integration_build_v001.json',
                    'press_train_a_assembly_integration_build_v002.json')
code = code.replace('press-train-a-assembly-integration-build-v001',
                    'press-train-a-assembly-integration-build-v002')
code = code.replace('"import_uniform_scale": 1.0', '"import_uniform_scale": 100.0')
code = code.replace('LB.PressTrain.TrainA.AssemblyIntegration.v001',
                    'LB.PressTrain.TrainA.AssemblyIntegration.v002')
code = code.replace('LB.Asset.Candidate.v001', 'LB.Asset.Candidate.v002')
code = code.replace('_Integration_v001', '_Integration_v002')
code = code.replace('AssemblyStudyIntegration_v001', 'AssemblyStudyIntegration_v002')
exec(compile(code, str(base) + "::corrected_v002", "exec"), globals(), globals())
