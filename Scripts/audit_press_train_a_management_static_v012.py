"""Exact-map static gate for Train A v012 with five mechanical-bay modules."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_isolated_static_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressTrainAIsolatedCandidate_v001", "/Game/LineBoss/Maps/LB_PressTrainAManagementCameraCandidate_v012")
code = code.replace("/Game/LineBoss/Candidates/PressTrains/Shared/Blockout_v001", "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003")
code = code.replace("Saved/Audits/PressTrains/press_train_a_isolated_static_v001.json", "Saved/Audits/PressTrains/press_train_a_management_static_v012.json")
code = code.replace("_v001", "_v003")
code = code.replace("press-train-a-isolated-static-v001", "press-train-a-management-static-v012")
code = code.replace("PRESS_TRAIN_A_V001", "PRESS_TRAIN_A_V012")
code = code.replace(
    'scope = [actor for actor in actors if "LB.PressTrain.TrainA.Isolated" in tags(actor)]',
    'scope = [actor for actor in actors if "LB.PressTrain.TrainA.Isolated" in tags(actor) and "LB.Validation.Environment" not in tags(actor)]',
)
code = code.replace(
    'tooling = [actor for actor in presentation if any(tag.startswith("LB.PressTrain.Tooling.") for tag in tags(actor))]',
    'tooling = [actor for actor in presentation if any(tag.startswith("LB.PressTrain.Tooling.") for tag in tags(actor))]\nmechanical_bays = [actor for actor in presentation if "LB.PressTrain.Fixed.MechanicalBay" in tags(actor)]',
)
code = code.replace("if len(presentation) != 37:", "if len(presentation) != 42:")
code = code.replace('failures.append(f"expected 37 presentation mesh actors, found {len(presentation)}")', 'failures.append(f"expected 42 presentation mesh actors, found {len(presentation)}")')
code = code.replace(
    'if len(tooling) != 5:\n    failures.append(f"expected five recipe die actors, found {len(tooling)}")',
    'if len(tooling) != 5:\n    failures.append(f"expected five recipe die actors, found {len(tooling)}")\nif len(mechanical_bays) != 5:\n    failures.append(f"expected five mechanical-bay actors, found {len(mechanical_bays)}")',
)
code = code.replace(
    'if missing_assets:\n    failures.append(f"missing imported assets: {missing_assets}")',
    'mechanical_asset = "/Game/LineBoss/Candidates/PressTrains/Shared/MechanicalBay_v001/SM_CA_MW_PT_MechanicalBayDress_v001"\nif not library.does_asset_exist(mechanical_asset):\n    missing_assets.append(mechanical_asset)\nif missing_assets:\n    failures.append(f"missing imported assets: {missing_assets}")',
)
code = code.replace(
    '"tooling_count": len(tooling),',
    '"tooling_count": len(tooling),\n    "mechanical_bay_count": len(mechanical_bays),',
)
exec(compile(code, str(base) + "::v012", "exec"), globals(), globals())
