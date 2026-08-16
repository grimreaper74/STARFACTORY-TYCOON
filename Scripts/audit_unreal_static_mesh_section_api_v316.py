"""Read-only API discovery for static-mesh section/material inspection."""
from pathlib import Path
import unreal
out=Path(unreal.Paths.project_saved_dir())/"Audits/PressTrains/unreal_static_mesh_section_api_v316.txt"
sub=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
names=sorted(n for n in dir(sub) if "section" in n.lower() or "material" in n.lower() or "lod" in n.lower())
out.parent.mkdir(parents=True,exist_ok=True);out.write_text("\n".join(names),encoding="utf-8");print("\n".join(names));unreal.SystemLibrary.quit_editor()
