"""Read-only exact-v438 validation; v441 is rejected because Python discarded the bool return."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_builder_authority_exact_v441.py")
code = base.read_text(encoding="utf-8")
code = code.replace("press_shop_builder_authority_exact_v441.json", "press_shop_builder_authority_exact_v442.json")
code = code.replace("builder-authority-exact-v441/v1", "builder-authority-exact-v442/v1")
old = '''response = authority.evaluate_train_transform(transform)
        valid, reason = response if isinstance(response, tuple) else (bool(response), "")'''
new = '''description = str(authority.describe_train_transform(transform))
        valid = description.startswith("VALID:")
        reason = description.split(":", 1)[1].strip() if ":" in description else description'''
code = code.replace(old, new)
old = '''response = authority.evaluate_train_transform(outside)
    outside_valid, outside_reason = response if isinstance(response, tuple) else (bool(response), "")
    if outside_valid or "OUTSIDE" not in str(outside_reason):
        failures.append(f"outside placement did not fail explicitly: {response}")'''
new = '''outside_description = str(authority.describe_train_transform(outside))
    outside_valid = outside_description.startswith("VALID:")
    outside_reason = outside_description.split(":", 1)[1].strip() if ":" in outside_description else outside_description
    if outside_valid or "OUTSIDE" not in str(outside_reason):
        failures.append(f"outside placement did not fail explicitly: {outside_description}")'''
code = code.replace(old, new)
code = code.replace('"FAIL__V438_AUTHORITY_NOT_RETAINABLE"', '"FAIL__V438_AUTHORITY_V442_NOT_RETAINABLE"')
exec(compile(code, str(base) + "::v442", "exec"), globals(), globals())
