"""Create the generated Press Shop integration map in an isolated UE session.

UE 5.8 keeps a duplicated World object alive until the editor session exits.
Loading that duplicate immediately in the same process trips the editor's world
leak guard, so candidate creation and candidate population are deliberately two
separate commandlet invocations.
"""

import unreal


FOUNDATION = "/Game/LineBoss/Maps/LB_PressShop_Foundation"
MAP = "/Game/LineBoss/Maps/LB_PressShop_IntegrationCandidate_v002"

library = unreal.EditorAssetLibrary
if library.does_asset_exist(MAP):
    unreal.log(f"LINE_BOSS_PRESS_SHOP_INTEGRATION_PREP_PASS existing={MAP}")
else:
    duplicate = library.duplicate_asset(FOUNDATION, MAP)
    if duplicate is None:
        raise RuntimeError("Failed duplicating Press Shop foundation")
    if not library.save_loaded_asset(duplicate, False):
        raise RuntimeError("Failed saving duplicated Press Shop integration map")
    unreal.log(f"LINE_BOSS_PRESS_SHOP_INTEGRATION_PREP_PASS created={MAP}")

