// Spacecraft-era input map authority (owner 2026-08-26: "look at car
// manufacturer and map all the mouse and keyboard keys to ours").
//
// ONE table owns the player's mouse+keyboard scheme: every row is a
// player-facing binding with a stable id, a localized display name, the
// legacy mapping it drives, and its default key(s). The defaults adopt
// the Car Manufacture conventions recovered from its embedded input
// asset (WASD pan, Q/E rotate, C/V zoom, Z/X object rotation, 1-4
// pause/speed, Tab section cycling, F5 quick save, LMB/RMB, Escape)
// wherever they fit our fixed-pitch 2.5D camera; the full mapping and
// its evidence live in Docs/INPUT_MAP_CM_ADOPTION_v001.md.
//
// All operations act on a UInputSettings instance (passed in, so
// automation tests run against a scratch object) and are fail-closed:
// a rebind that would shadow another row refuses with the collision
// named rather than silently double-binding.

#pragma once

#include "CoreMinimal.h"
#include "InputCoreTypes.h"
#include "UObject/Object.h"
#include "LBSpacecraftInputMap.generated.h"

class UInputSettings;

UENUM()
enum class ELBSpacecraftInputRowKind : uint8
{
	Action,
	AxisKey
};

UENUM()
enum class ELBSpacecraftInputCategory : uint8
{
	Camera,
	Build,
	Game
};

USTRUCT()
struct LINEBOSSCARFACTORY_API FLBSpacecraftInputRow
{
	GENERATED_BODY()

	FName RowId;
	FName MappingName;
	ELBSpacecraftInputRowKind Kind = ELBSpacecraftInputRowKind::Action;
	ELBSpacecraftInputCategory Category = ELBSpacecraftInputCategory::Camera;

	/** AxisKey rows: the scale this key contributes (sign identifies
	 *  the row among the axis' mappings, e.g. W=+1 / S=-1). */
	float AxisScale = 0.f;

	FKey DefaultKey;
	bool bDefaultShift = false;

	/** Additional default keys bound alongside the primary (e.g. the
	 *  ghost also rotates on R and F next to the CM-adopted X). */
	FKey ExtraDefaultKey1;
	FKey ExtraDefaultKey2;

	/** Localized name shown in the controls page. */
	FText DisplayName;

	/** Locked rows (LMB confirm, Escape menu, wheel zoom) are listed
	 *  but never rebindable - the scheme's fixed anchors. */
	bool bRebindable = true;
};

class LINEBOSSCARFACTORY_API FLBSpacecraftInputMap
{
public:
	/** The complete player-facing scheme, in display order. */
	static const TArray<FLBSpacecraftInputRow>& GetRows();

	static const FLBSpacecraftInputRow* FindRow(FName RowId);

	/** Adds any spacecraft mapping that is entirely absent from the
	 *  settings (fresh install, stale Saved/Input.ini predating a new
	 *  action). Player rebinds survive - only missing mappings gain
	 *  their defaults. Returns the number of mappings added. */
	static int32 EnsureSpacecraftBindings(UInputSettings& Settings);

	/** Restores every row to its default key(s), dropping keyboard and
	 *  mouse rebinds. Gamepad mappings are untouched. */
	static void ResetSpacecraftBindings(UInputSettings& Settings);

	/** Every keyboard/mouse key currently serving the row. */
	static TArray<FKey> GetAllKeys(const UInputSettings& Settings,
		const FLBSpacecraftInputRow& Row);

	/** The row's current primary keyboard/mouse key (invalid FKey when
	 *  the mapping has none), plus its shift modifier for actions. */
	static FKey GetPrimaryKey(const UInputSettings& Settings,
		const FLBSpacecraftInputRow& Row, bool& bOutShift);

	/** Fail-closed rebind: refuses locked rows, gamepad keys, Escape,
	 *  and keys already serving another spacecraft row (collision
	 *  named). On success the row's keyboard/mouse mappings are
	 *  replaced with NewKey. The caller persists and rebuilds keymaps. */
	static bool RebindRow(UInputSettings& Settings, FName RowId,
		const FKey& NewKey, FString& OutReason);

	/** True when the key may be offered for rebinding at all. */
	static bool IsBindableKey(const FKey& Key);
};
