from pathlib import Path
src=Path(__file__).with_name("capture_press_train_a_presentation_shell_v037.py")
code=src.read_text(encoding="utf-8").replace("v037","v038").replace("V037","V038")
exec(compile(code,str(src)+"::aligned-shell-v038","exec"),{"__name__":"__main__","__file__":str(src).replace("v037","v038")})
