"""Produce a fresh scale-correct v033 staging set from immutable v013."""

from pathlib import Path


source = Path(__file__).with_name("prepare_press_train_a_fabrication_staging_v032.py")
code = source.read_text(encoding="utf-8").replace("v032", "v033").replace("V032", "V033")
exec(compile(code, str(source) + "::fresh-v033", "exec"), {
    "__name__": "__main__",
    "__file__": str(source).replace("v032", "v033"),
})
