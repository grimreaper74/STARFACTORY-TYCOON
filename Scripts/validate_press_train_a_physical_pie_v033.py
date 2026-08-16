"""Run the retained physical gameplay gate on fabrication child v033."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_train_a_physical_pie_v019.py")
adapter = source.read_text(encoding="utf-8")
needle = 'exec(compile(code, str(source) + "::v019", "exec"), globals(), globals())'
replacement = '''# The v033 child inherits the exact v024 physical tag/collision contract.
code = code.replace("v019", "v024").replace("V019", "V024")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressTrainAPhysicalGameplayCandidate_v024",
    "/Game/LineBoss/Maps/LB_PressTrainAFabricationCandidate_v033")
code = code.replace(
    "Saved/Audits/PressTrains/press_train_a_physical_pie_v024.json",
    "Saved/Audits/PressTrains/press_train_a_physical_pie_v033.json")
exec(compile(code, str(source) + "::fabrication-v033", "exec"), globals(), globals())'''
if needle not in adapter:
    raise RuntimeError("v019 physical adapter changed")
adapter = adapter.replace(needle, replacement, 1)
exec(compile(adapter, str(source) + "::fabrication-v033", "exec"), globals(), globals())
