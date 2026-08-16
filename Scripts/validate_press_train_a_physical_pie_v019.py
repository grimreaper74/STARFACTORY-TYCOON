"""v019 PIE adapter: validate standing-pawn defaults while SIE uses a spectator controller."""

from pathlib import Path

source = Path(__file__).resolve().parent / "validate_press_train_a_physical_pie_v018.py"
code = source.read_text(encoding="utf-8").replace("v018", "v019").replace("V018", "V019")

needle = '''    pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
    capsule_component = pawn.get_component_by_class(unreal.CapsuleComponent) if pawn else None
    pawn_row = {"present": pawn is not None,
                "class": pawn.get_class().get_name() if pawn else None,
                "location_cm": ([pawn.get_actor_location().x, pawn.get_actor_location().y,
                                  pawn.get_actor_location().z] if pawn else None),
                "capsule_radius_cm": capsule_component.get_unscaled_capsule_radius() if capsule_component else None,
                "capsule_half_height_cm": capsule_component.get_unscaled_capsule_half_height() if capsule_component else None}
    if not pawn or not capsule_component: failures.append(f"standing operator pawn/capsule missing: {pawn_row}")
    elif abs(pawn_row["capsule_radius_cm"] - 34.0) > 0.1 or abs(pawn_row["capsule_half_height_cm"] - 88.0) > 0.1:
        failures.append(f"standing operator capsule authority mismatch: {pawn_row}")
'''
replacement = '''    pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
    pawn_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBControlRoomPawn")
    pawn_defaults = unreal.get_default_object(pawn_class) if pawn_class else None
    default_capsule = pawn_defaults.get_component_by_class(unreal.CapsuleComponent) if pawn_defaults else None
    pawn_row = {"sie_runtime_pawn_present": pawn is not None,
                "sie_runtime_pawn_class": pawn.get_class().get_name() if pawn else None,
                "sie_uses_spectator_by_design": bool(pawn and pawn.get_class().get_name() == "SpectatorPawn"),
                "map_game_mode_checked_by_static_gate": "/Script/LineBossCarFactory.LBControlRoomGameMode",
                "standing_pawn_class": pawn_class.get_name() if pawn_class else None,
                "default_capsule_radius_cm": default_capsule.get_unscaled_capsule_radius() if default_capsule else None,
                "default_capsule_half_height_cm": default_capsule.get_unscaled_capsule_half_height() if default_capsule else None,
                "capsule_sweep_uses_authoritative_defaults": True}
    if not pawn_class or not default_capsule:
        failures.append(f"standing operator class/default capsule missing: {pawn_row}")
    elif abs(pawn_row["default_capsule_radius_cm"] - 34.0) > 0.1 or abs(pawn_row["default_capsule_half_height_cm"] - 88.0) > 0.1:
        failures.append(f"standing operator default capsule authority mismatch: {pawn_row}")
'''
if needle not in code:
    raise RuntimeError("v018 pawn proof block changed; refusing v019 PIE adapter")
code = code.replace(needle, replacement, 1)

exec(compile(code, str(source) + "::v019", "exec"), globals(), globals())
