import json
from pathlib import Path
import unreal
DEST="/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v038_ModularRig"
rows=[]
for path in unreal.EditorAssetLibrary.list_assets(DEST,recursive=False,include_folder=False):
    asset=unreal.load_asset(path)
    rows.append({"name":asset.get_name(),"class":asset.get_class().get_name()})
out=Path(unreal.Paths.project_saved_dir())/"Audits/lb_cr01_asset_classes_v038.json"
out.write_text(json.dumps(rows,indent=2),encoding="utf-8")
