"""Legacy-FBX exact-scale successor; preserves failed Interchange v001/v002 candidates."""

from pathlib import Path


base = Path(__file__).with_name("import_build_press_train_a_assembly_study_integration_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace('DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v001"',
                    'DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v003"')
code = code.replace('MAP = "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyIntegrationCandidate_v001"',
                    'MAP = "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyIntegrationCandidate_v003"')
code = code.replace('press_train_a_assembly_integration_build_v001.json',
                    'press_train_a_assembly_integration_build_v003.json')
code = code.replace('press-train-a-assembly-integration-build-v001',
                    'press-train-a-assembly-integration-build-v003')
code = code.replace('"import_uniform_scale": 1.0', '"import_uniform_scale": 100.0')
code = code.replace('mel = unreal.MaterialEditingLibrary',
                    'mel = unreal.MaterialEditingLibrary\nunreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")')
code = code.replace('LB.PressTrain.TrainA.AssemblyIntegration.v001',
                    'LB.PressTrain.TrainA.AssemblyIntegration.v003')
code = code.replace('LB.Asset.Candidate.v001', 'LB.Asset.Candidate.v003')
code = code.replace('_Integration_v001', '_Integration_v003')
code = code.replace('AssemblyStudyIntegration_v001', 'AssemblyStudyIntegration_v003')
exec(compile(code, str(base) + "::legacy_exact_scale_v003", "exec"), globals(), globals())
