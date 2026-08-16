"""Record PR-009 native runtime plus modular presentation-contract automation."""
from pathlib import Path

base = Path(__file__).with_name("audit_pr009_native_runtime_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("PR009_Runtime_v001", "PR009_Runtime_v002")
code = code.replace("press_shop_pr009_native_runtime_source_v001.json", "press_shop_pr009_native_runtime_presentation_v002.json")
code = code.replace("press-shop-pr009-native-runtime-source-v001/v1", "press-shop-pr009-native-runtime-presentation-v002/v1")
code = code.replace(
    "NATIVE_PR009_REMOTE_AUTHORITY_PROCESS_FAULT_ISOLATION_TRACEABILITY_AND_SAFE_SAVE_RESTORE_AUTOMATION_PASS__MAP_BINDING_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "NATIVE_PR009_REMOTE_AUTHORITY_PROCESS_FAULT_ISOLATION_TRACEABILITY_SAFE_SAVE_RESTORE_AND_PRESENTATION_CONTRACT_AUTOMATION_PASS__FINAL_ASSET_BINDING_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED")
code = code.replace(
    '        "safe stationary restore of moving production with explicit restart required",',
    '        "safe stationary restore of moving production with explicit restart required",\n'
    '        "26 modular motion contracts plus the station root, including 18 independent roller pivots and eight mechanism movers",\n'
    '        "receiving-phase infeed-roll presentation motion",')
code = code.replace(
    '        "No v083 map actor or staged mesh decomposition is bound yet.",',
    '        "v083 contains the native actor but uses combined diagnostic meshes; final corrected semantic FBXs are not bound.",')
exec(compile(code, str(base) + "::runtime-presentation-v002", "exec"), globals(), globals())
