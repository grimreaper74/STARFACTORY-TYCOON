"""Replace v008's wrongly signed monitor group with the verified +12-degree v005 group."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "import_build_main_control_room_operator_aim_candidate_v008.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace(
    'SOURCE = ROOT / "SourceAssets/ControlRoom/MainControlRoom_v006/fbx_candidate"',
    'SOURCE = ROOT / "SourceAssets/ControlRoom/MainControlRoom_v005/fbx_candidate"',
)
code = code.replace(
    'BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_PlayableCandidate_v007"',
    'BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_OperatorAimCandidate_v008"',
)
code = code.replace(
    'MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_OperatorAimCandidate_v008"',
    'MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_OperatorAimCorrectedCandidate_v018"',
)
code = code.replace(
    'DEST = "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v008"',
    'DEST = "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v018"',
)
code = code.replace(
    'OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_operator_aim_import_build_v008.json"',
    'OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_operator_aim_corrected_build_v018.json"',
)
code = code.replace('v006_CANDIDATE.fbx', 'v005_CANDIDATE.fbx')
code = code.replace('f"SM_CA_MW_MCR_{category}_v008"', 'f"SM_CA_MW_MCR_{category}_v018"')
code = code.replace('actors.get(f"LB_MCR_V006_{category}")', 'actors.get(f"LB_MCR_V008_{category}")')
code = code.replace('actor.set_actor_label(f"LB_MCR_V008_{category}")', 'actor.set_actor_label(f"LB_MCR_V018_{category}")')
code = code.replace('label.startswith("LB_MCR_V006_CAM_")', 'label.startswith("LB_MCR_V008_CAM_")')
code = code.replace('label.replace("V006", "V008")', 'label.replace("V008", "V018")')
code = code.replace('"LB.ControlRoom.v007"', '"LB.ControlRoom.v008"')
code = code.replace('"LB.ControlRoom.v008" if str(tag) == "LB.ControlRoom.v008"', '"LB.ControlRoom.v018" if str(tag) == "LB.ControlRoom.v008"')
code = code.replace('unreal.Name("LB.ControlRoom.v008")', 'unreal.Name("LB.ControlRoom.v018")')
code = code.replace('main-control-room-operator-aim-import-build-v008', 'main-control-room-operator-aim-corrected-build-v018')
code = code.replace('PASS__MONITORS_AIMED_DOWN_TOWARD_SEATED_OPERATOR__RUNTIME_VISUAL_GATE_REQUIRED__NOT_PROMOTED', 'PASS__MONITOR_FACE_NORMALS_AIM_DOWN_TOWARD_SEATED_OPERATOR__RUNTIME_VISUAL_GATE_REQUIRED__NOT_PROMOTED')
code = code.replace('FAIL__CONTROL_ROOM_V008_OPERATOR_AIM_BUILD__NOT_PROMOTED', 'FAIL__CONTROL_ROOM_V018_OPERATOR_AIM_BUILD__NOT_PROMOTED')
code = code.replace('"source_package": "SourceAssets/ControlRoom/MainControlRoom_v006"', '"source_package": "SourceAssets/ControlRoom/MainControlRoom_v005"')
code = code.replace('"source_pitch_degrees": -12.0', '"source_pitch_degrees": 12.0')
code = code.replace(
    '"pitch_basis": "Blender negative-X aims monitor normals down toward the seated 1.12 m operator eye point"',
    '"pitch_basis": "The visible monitor face is local -Y; Blender +12-degree X pitch aims that face down/front toward the seated 1.12 m operator eye point"',
)
exec(compile(code, str(SOURCE) + "::v018", "exec"), globals(), globals())
