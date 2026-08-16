"""Exact-scale import from candidate-only v004 centimetre-coordinate staging derivatives."""

from pathlib import Path


base = Path(__file__).with_name("import_build_press_train_a_assembly_study_integration_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace('ASSEMBLY_FBX = SOURCE / "FBX/SM_CA_MW_PTA_SevenStageAssemblyStudy_v001.fbx"',
                    'SOURCE_ASSEMBLY_FBX = SOURCE / "FBX/SM_CA_MW_PTA_SevenStageAssemblyStudy_v001.fbx"\nSTAGING = ROOT / "Saved/ImportStaging/PressTrainAAssemblyIntegration_v004"\nASSEMBLY_FBX = STAGING / "SM_CA_MW_PTA_SevenStageAssemblyStudy_v001.fbx"')
code = code.replace('DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v001"',
                    'DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v004"')
code = code.replace('MAP = "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyIntegrationCandidate_v001"',
                    'MAP = "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyIntegrationCandidate_v004"')
code = code.replace('press_train_a_assembly_integration_build_v001.json',
                    'press_train_a_assembly_integration_build_v004.json')
code = code.replace('press-train-a-assembly-integration-build-v001',
                    'press-train-a-assembly-integration-build-v004')
code = code.replace('if sha(ASSEMBLY_FBX) != manifest["assembly_fbx"]["sha256"]:',
                    'if sha(SOURCE_ASSEMBLY_FBX) != manifest["assembly_fbx"]["sha256"]:')
code = code.replace('    path = ROOT / record["path"]\n    name = path.stem\n    mesh, imported = import_static(path, MODULE_DEST, name, True)',
                    '    source_path = ROOT / record["path"]\n    path = STAGING / source_path.name\n    name = source_path.stem\n    if not path.exists():\n        raise FileNotFoundError(path)\n    mesh, imported = import_static(path, MODULE_DEST, name, True)')
code = code.replace('LB.PressTrain.TrainA.AssemblyIntegration.v001',
                    'LB.PressTrain.TrainA.AssemblyIntegration.v004')
code = code.replace('LB.Asset.Candidate.v001', 'LB.Asset.Candidate.v004')
code = code.replace('_Integration_v001', '_Integration_v004')
code = code.replace('AssemblyStudyIntegration_v001', 'AssemblyStudyIntegration_v004')
code = code.replace('"sha256": sha(ASSEMBLY_FBX), "manifest"',
                    '"source_sha256": sha(SOURCE_ASSEMBLY_FBX), "staging_sha256": sha(ASSEMBLY_FBX), "manifest"')
exec(compile(code, str(base) + "::cm_staging_exact_scale_v004", "exec"), globals(), globals())
