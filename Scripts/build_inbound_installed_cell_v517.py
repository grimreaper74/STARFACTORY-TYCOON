"""Fresh v517 rebuild using retained v514 assets plus corrected presentation."""
from pathlib import Path

root=Path(__file__).parent
base=(root/"build_inbound_installed_cell_v514.py").read_text(encoding="utf-8")
base=base.replace("v514","v517").replace("V514","V517").replace("V014_","V017_")
old='''if library.does_asset_exist(path):
        raise RuntimeError(f"Fresh intake path already exists: {path}")
    task = unreal.AssetImportTask()'''
new='''if library.does_asset_exist(path):
        mesh=library.load_asset(path)
        if not isinstance(mesh, unreal.StaticMesh):
            raise RuntimeError(f"Retained intake asset is invalid: {path}")
        size=mesh.get_bounds().box_extent*2.0
        return mesh, {"asset":path,"source":str(fbx),"sha256":digest(fbx),
            "bounds_cm":[round(size.x,2),round(size.y,2),round(size.z,2)],
            "material_slots":len(mesh.get_editor_property("static_materials")),
            "body_setup":mesh.get_editor_property("body_setup") is not None,"reused":True}
    task = unreal.AssetImportTask()'''
if old not in base:
    raise RuntimeError("v517 retained-import patch anchor not found")
base=base.replace(old,new)
exec(compile(base,str(root/"build_inbound_installed_cell_v514.py"),"exec"),globals(),globals())

visual=(root/"build_inbound_installed_cell_v515.py").read_text(encoding="utf-8")
visual=visual.replace("v515","v517").replace("V515","V517")
visual=visual.replace("V014_","V017_").replace("V015_","V017_")
setup='''if library.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing overwrite {MAP}")
if not library.duplicate_asset(SRC, MAP):
    raise RuntimeError("Could not duplicate retained v514 into fresh v517")
if not levels.load_level(MAP):
    raise RuntimeError("Could not load v517")
'''
if setup not in visual:
    raise RuntimeError("v517 visual setup removal anchor not found")
visual=visual.replace(setup,"")
exec(compile(visual,str(root/"build_inbound_installed_cell_v515.py"),"exec"),globals(),globals())
