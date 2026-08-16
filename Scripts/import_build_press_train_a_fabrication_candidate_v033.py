"""Fresh v027 child accepting only sub-7.5 mm fabrication-chamfer deltas."""

from pathlib import Path


source = Path(__file__).with_name("import_build_press_train_a_fabrication_candidate_v031.py")
code = source.read_text(encoding="utf-8").replace("v031", "v033").replace("V031", "V033")
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
old = "    if sorted_error > 0.25:"
new = "    # v013 bevels intentionally trim seven formed-panel visual bounds by at most 5.81 mm.\n    if sorted_error > 0.75:"
if old not in code:
    raise RuntimeError("v032 bounds-tolerance source changed")
code = code.replace(old, new, 1)
exec(compile(code, str(source) + "::scale-and-fabrication-tolerance-v033", "exec"), {
    "__name__": "__main__",
    "__file__": str(source).replace("v032", "v033"),
})
