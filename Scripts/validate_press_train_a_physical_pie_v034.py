"""Run inherited v024 physical contract on collision-safe fabrication v034."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_train_a_physical_pie_v033.py")
code = source.read_text(encoding="utf-8").replace("v033", "v034").replace("V033", "V034")
code = code.replace(
    "LB_PressTrainAFabricationCandidate_v034",
    "LB_PressTrainAFabricationCollisionSafeCandidate_v034",
)
exec(compile(code, str(source) + "::collision-safe-v034", "exec"), globals(), globals())
