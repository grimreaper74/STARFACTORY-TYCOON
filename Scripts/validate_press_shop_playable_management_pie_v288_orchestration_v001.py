"""Re-run the exact v288 playable-management gate without overwriting retained evidence."""
from pathlib import Path

_original_write_text = Path.write_text


def _write_text_without_overwriting_retained_v288(self, data, *args, **kwargs):
    if self.name == "press_shop_playable_management_pie_v288.json":
        self = self.with_name("press_shop_playable_management_pie_v288_orchestration_v001.json")
    return _original_write_text(self, data, *args, **kwargs)


Path.write_text = _write_text_without_overwriting_retained_v288
source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v288.py")
code = source.read_text(encoding="utf-8")
exec(compile(code, str(source) + "::orchestration_v001", "exec"), globals(), globals())
