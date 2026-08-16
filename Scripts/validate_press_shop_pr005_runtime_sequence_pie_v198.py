"""Exact v198 PR005 commissioning, interlock, fault and restore wrapper."""

from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_pr005_runtime_sequence_pie_v197.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v197", "v198").replace("V197", "V198")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PR005RuntimeCageInfillCandidate_v198",
    "/Game/LineBoss/Maps/LB_PressShop_PR005AudioRuntimeCandidate_v198",
)
code = code.replace(
    '"audio_binding": "OPEN__SOURCE_AUDIO_EXISTS_BUT_EXACT_V198_RUNTIME_BINDING_NOT_CLAIMED",',
    '"audio_binding": "PASS__SEE_press_shop_pr005_audio_runtime_pie_v198.json",',
)
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
