"""Run the v031 isolated replacement build with corrected v032 staging."""

from pathlib import Path


source = Path(__file__).with_name("import_build_press_train_a_fabrication_candidate_v031.py")
code = source.read_text(encoding="utf-8").replace("v031", "v032").replace("V031", "V032")
old_hmi = '''hmi_count = sum(
    isinstance(actor, unreal.TextRenderActor)
    and "LB.HMI.PressTrain.LiveState" in {str(value) for value in actor.tags}
    for actor in actors
)'''
new_hmi = '''hmi_count = sum(
    isinstance(actor, unreal.TextRenderActor)
    and bool({
        "LB.HMI.PressTrain.LiveState",
        "LB.HMI.PressTrainA.LiveState",
    } & {str(value) for value in actor.tags})
    for actor in actors
)'''
if old_hmi not in code:
    raise RuntimeError("v031 live-HMI detection source changed")
code = code.replace(old_hmi, new_hmi, 1)
exec(compile(code, str(source) + "::correct-centimetre-scale-v032", "exec"), {
    "__name__": "__main__",
    "__file__": str(source).replace("v031", "v032"),
})
