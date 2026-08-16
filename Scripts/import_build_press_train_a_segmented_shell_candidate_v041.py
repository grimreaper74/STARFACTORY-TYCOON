"""Import v016 through the proven isolated v040 intake contract as fresh v041."""

from pathlib import Path


source = Path(__file__).with_name("import_build_press_train_a_fabricated_shell_candidate_v040.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v015", "v016").replace("V015", "V016")
code = code.replace("v040", "v041").replace("V040", "V041")
code = code.replace(
    "SOURCE_ONLY_FABRICATED_SHELL__UNREAL_INTAKE_REQUIRED__NOT_PROMOTED",
    "SOURCE_ONLY_SEGMENTED_MIDTONE_SHELL__UNREAL_INTAKE_REQUIRED__NOT_PROMOTED",
)
code = code.replace("fabricated-shell-build-v041", "segmented-shell-build-v041")
code = code.replace("FABRICATED_SHELL_ISOLATED_INTAKE", "SEGMENTED_MIDTONE_SHELL_ISOLATED_INTAKE")
exec(compile(code, str(source) + "::v041", "exec"), globals(), globals())
