"""Correct v001 clean-shell constants from mistaken linearised values to authored sRGB values."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
DIR="/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v001/Materials"
OUT=ROOT/"Saved/Audits/PressShopIntegration/clean_shell_material_colour_repair_v20260809_v002.json"
PROTECTED=ROOT/"Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED="5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
before=hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if before!=EXPECTED:raise RuntimeError("protected hash mismatch")
colours={
 "M_LB_CleanShell_SealedEpoxyGrey_v001":"666B6E",
 "M_LB_CleanShell_WarmWhite_v001":"F3F1E9",
 "M_LB_CleanShell_FoundryCharcoal_v001":"202428",
 "M_LB_CleanShell_WalkwayGreen_v001":"1F4B44",
 "M_LB_CleanShell_SafetyYellow_v001":"F2C300",
 "M_LB_CleanShell_SignalRed_v001":"C7352C",
 "M_LB_CleanShell_MarkingWhite_v001":"F3F1E9",
}
repaired=[]
for name,h in colours.items():
 m=unreal.load_asset(f"{DIR}/{name}")
 if not isinstance(m,unreal.Material):raise RuntimeError(name)
 nodes=unreal.MaterialEditingLibrary.get_material_expressions(m)
 bases=[n for n in nodes if isinstance(n,unreal.MaterialExpressionConstant3Vector)]
 if len(bases)!=1:raise RuntimeError(f"{name} base nodes={len(bases)}")
 rgb=tuple(int(h[i:i+2],16)/255.0 for i in (0,2,4))
 bases[0].set_editor_property("constant",unreal.LinearColor(*rgb,1.0))
 unreal.MaterialEditingLibrary.recompile_material(m);unreal.EditorAssetLibrary.save_loaded_asset(m)
 repaired.append({"material":m.get_path_name(),"hex":f"#{h}","constant":rgb})
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
after=hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if after!=before:raise RuntimeError("protected map changed")
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({
 "$schema":"cairnwell/audit/clean-shell-material-colour-repair/v2","generated_utc":datetime.now(timezone.utc).isoformat(),
 "status":"PASS__AUTHORED_SRGB_CONSTANTS_RESTORED__FRESH_VISUAL_REVIEW_REQUIRED","materials":repaired,
 "protected_v438_before":before,"protected_v438_after":after
},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_CLEAN_SHELL_MATERIAL_REPAIR_V002_PASS")
